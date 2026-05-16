# ============================================================
# Graph Heuristics Detection
# ============================================================
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GraphHeuristicsDetector:
    """
    Queries the Graph Engine API to detect graph-based fraud signals.
    Future: replace HTTP calls with direct Neo4j queries.
    """

    def __init__(
        self,
        graph_engine_url: str = "http://graph-engine:8002",
        high_centrality_threshold: float = 0.7,
    ):
        self.graph_url = graph_engine_url.rstrip("/")
        self.centrality_threshold = high_centrality_threshold
        self._client = httpx.Client(timeout=5.0)

    def evaluate(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check graph-level signals for a transaction's accounts.
        """
        sender = txn.get("sender_account", "")
        receiver = txn.get("receiver_account", "")
        risk_score = 0.0
        signals = []

        # Signal 1: Sender centrality (mule hub check)
        sender_centrality = self._get_account_centrality(sender)
        if sender_centrality > self.centrality_threshold:
            signals.append({
                "signal": "high_centrality_sender",
                "account": sender,
                "centrality": sender_centrality,
            })
            risk_score += 0.7

        # Signal 2: Receiver centrality
        receiver_centrality = self._get_account_centrality(receiver)
        if receiver_centrality > self.centrality_threshold:
            signals.append({
                "signal": "high_centrality_receiver",
                "account": receiver,
                "centrality": receiver_centrality,
            })
            risk_score += 0.5

        # Signal 3: Cycle involvement
        cycles = self._get_cycles_involving(sender)
        if cycles:
            signals.append({
                "signal": "cycle_participant",
                "account": sender,
                "cycle_count": len(cycles),
            })
            risk_score += 0.9

        # Signal 4: Sender velocity
        velocity = self._get_velocity(sender)
        if velocity.get("tx_count", 0) >= 5:
            signals.append({
                "signal": "high_velocity",
                "account": sender,
                "tx_count": velocity["tx_count"],
            })
            risk_score += 0.4

        return {
            "transaction_id": txn.get("transaction_id"),
            "graph_signals": signals,
            "graph_risk_score": min(round(risk_score, 4), 1.0),
            "detection_method": "graph_heuristic",
        }

    def _get_account_centrality(self, account_id: str) -> float:
        try:
            r = self._client.get(f"{self.graph_url}/graph/centrality")
            if r.status_code == 200:
                nodes = r.json().get("nodes", [])
                for node in nodes:
                    if node["account_id"] == account_id:
                        return node["centrality"]
        except Exception as e:
            logger.debug(f"Centrality check failed for {account_id}: {e}")
        return 0.0

    def _get_cycles_involving(self, account_id: str) -> List[List[str]]:
        try:
            r = self._client.get(f"{self.graph_url}/graph/cycles")
            if r.status_code == 200:
                cycles = r.json().get("cycles", [])
                return [c for c in cycles if account_id in c]
        except Exception as e:
            logger.debug(f"Cycle check failed: {e}")
        return []

    def _get_velocity(self, account_id: str) -> Dict[str, Any]:
        try:
            r = self._client.get(f"{self.graph_url}/graph/velocity/{account_id}")
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.debug(f"Velocity check failed: {e}")
        return {}

    def close(self):
        self._client.close()
