# ============================================================
# Graph Store — NetworkX-backed transaction graph
# ============================================================
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


class TransactionGraph:
    """
    Thread-safe NetworkX directed graph representing bank account relationships.
    Nodes = accounts, Edges = transactions (weighted by amount).
    Designed for future Neo4j migration: swap this class only.
    """

    def __init__(self, max_nodes: int = 50000):
        self._graph = nx.MultiDiGraph()
        self._lock = threading.RLock()
        self.max_nodes = max_nodes
        self.total_transactions = 0

    def add_transaction(self, txn: Dict[str, Any]) -> None:
        sender = txn["sender_account"]
        receiver = txn["receiver_account"]
        amount = float(txn.get("amount", 0))
        ts = txn.get("timestamp", datetime.utcnow().isoformat())
        attack_type = txn.get("attack_type", "unknown")
        simulation_id = txn.get("simulation_id", "")
        txn_id = txn.get("transaction_id", "")
        mutation_gen = txn.get("mutation_generation", 0)

        with self._lock:
            if len(self._graph.nodes) >= self.max_nodes:
                logger.warning(f"Graph at max capacity ({self.max_nodes} nodes)")
                return

            # Upsert nodes with metadata
            for acc_id in [sender, receiver]:
                if not self._graph.has_node(acc_id):
                    self._graph.add_node(acc_id, first_seen=ts, tx_count=0, total_volume=0.0)
                self._graph.nodes[acc_id]["tx_count"] = (
                    self._graph.nodes[acc_id].get("tx_count", 0) + 1
                )
                self._graph.nodes[acc_id]["last_seen"] = ts
                self._graph.nodes[acc_id]["total_volume"] = (
                    self._graph.nodes[acc_id].get("total_volume", 0.0) + amount
                )

            # Add edge
            self._graph.add_edge(
                sender,
                receiver,
                key=txn_id,
                weight=amount,
                timestamp=ts,
                attack_type=attack_type,
                simulation_id=simulation_id,
                mutation_generation=mutation_gen,
            )
            self.total_transactions += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "nodes": self._graph.number_of_nodes(),
                "edges": self._graph.number_of_edges(),
                "total_transactions": self.total_transactions,
                "is_directed": True,
                "density": (
                    nx.density(self._graph)
                    if self._graph.number_of_nodes() > 1
                    else 0.0
                ),
            }

    def detect_cycles(self, max_cycles: int = 50) -> List[List[str]]:
        """Find cyclic paths — hallmark of round-trip laundering."""
        with self._lock:
            try:
                simple_g = nx.DiGraph(self._graph)
                cycles = []
                for cycle in nx.simple_cycles(simple_g):
                    cycles.append(cycle)
                    if len(cycles) >= max_cycles:
                        break
                return cycles
            except Exception as e:
                logger.error(f"Cycle detection error: {e}")
                return []

    def get_degree_centrality(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """High-centrality nodes are likely mule hubs."""
        with self._lock:
            if self._graph.number_of_nodes() == 0:
                return []
            simple_g = nx.DiGraph(self._graph)
            centrality = nx.degree_centrality(simple_g)
            sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            return [
                {
                    "account_id": node,
                    "centrality": round(score, 6),
                    "in_degree": simple_g.in_degree(node),
                    "out_degree": simple_g.out_degree(node),
                    "total_volume": self._graph.nodes[node].get("total_volume", 0.0),
                    "tx_count": self._graph.nodes[node].get("tx_count", 0),
                }
                for node, score in sorted_nodes[:top_n]
            ]

    def trace_suspicious_paths(
        self, source: str, max_depth: int = 6
    ) -> List[List[str]]:
        """BFS from source to find all paths up to max_depth."""
        with self._lock:
            if source not in self._graph:
                return []
            simple_g = nx.DiGraph(self._graph)
            paths = []
            for target in list(simple_g.nodes)[:500]:
                if target == source:
                    continue
                try:
                    for path in nx.all_simple_paths(
                        simple_g, source=source, target=target, cutoff=max_depth
                    ):
                        paths.append(path)
                        if len(paths) > 100:
                            return paths
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
            return paths

    def get_velocity(
        self,
        account_id: str,
        window_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Count transactions for account within time window."""
        with self._lock:
            if account_id not in self._graph:
                return {"account_id": account_id, "tx_count": 0, "window_seconds": window_seconds}

            cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
            tx_count = 0
            volume = 0.0

            # Check outgoing edges
            for _, _, data in self._graph.out_edges(account_id, data=True):
                try:
                    ts_str = data.get("timestamp", "")
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts.replace(tzinfo=None) >= cutoff:
                        tx_count += 1
                        volume += data.get("weight", 0.0)
                except Exception:
                    pass

            return {
                "account_id": account_id,
                "tx_count": tx_count,
                "volume": round(volume, 2),
                "window_seconds": window_seconds,
            }

    def analyze_account(self, account_id: str) -> Dict[str, Any]:
        """Deep analysis of a single account node."""
        with self._lock:
            if account_id not in self._graph:
                return {"error": "account not found", "account_id": account_id}

            simple_g = nx.DiGraph(self._graph)
            in_neighbors = list(simple_g.predecessors(account_id))
            out_neighbors = list(simple_g.successors(account_id))

            try:
                centrality = nx.degree_centrality(simple_g).get(account_id, 0.0)
            except Exception:
                centrality = 0.0

            node_data = dict(self._graph.nodes[account_id])

            return {
                "account_id": account_id,
                "in_degree": simple_g.in_degree(account_id),
                "out_degree": simple_g.out_degree(account_id),
                "in_neighbors": in_neighbors[:20],
                "out_neighbors": out_neighbors[:20],
                "centrality": round(centrality, 6),
                "total_volume": node_data.get("total_volume", 0.0),
                "tx_count": node_data.get("tx_count", 0),
                "first_seen": node_data.get("first_seen"),
                "last_seen": node_data.get("last_seen"),
            }

    def get_layering_chains(self, min_depth: int = 3) -> List[List[str]]:
        """Detect linear chains (non-cyclic paths) of depth >= min_depth."""
        with self._lock:
            simple_g = nx.DiGraph(self._graph)
            chains = []
            # Find nodes with in_degree=0 (chain starters)
            starters = [n for n in simple_g.nodes if simple_g.in_degree(n) == 0]
            for start in starters[:50]:
                for end in simple_g.nodes:
                    try:
                        for path in nx.all_simple_paths(
                            simple_g, source=start, target=end, cutoff=12
                        ):
                            if len(path) >= min_depth:
                                chains.append(path)
                                if len(chains) > 50:
                                    return chains
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        continue
            return chains

    def clear(self) -> None:
        with self._lock:
            self._graph.clear()
            self.total_transactions = 0
