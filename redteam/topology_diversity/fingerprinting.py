import networkx as nx
import numpy as np
from typing import List, Dict, Any

class TopologyFingerprinter:
    """Computes advanced structural signatures from transaction graphs."""

    @staticmethod
    def generate_fingerprint(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a behavioral morphology fingerprint from a list of transactions."""
        if not transactions:
            return {}

        # Build NetworkX DiGraph
        G = nx.DiGraph()
        for txn in transactions:
            G.add_edge(txn["sender_account"], txn["receiver_account"], amount=txn.get("amount", 0))

        # Basic Scalar Metrics (kept for backward compatibility/normalization)
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        density = nx.density(G)

        # 1. Degree Distribution Histograms (In & Out)
        in_degrees = [d for n, d in G.in_degree()]
        out_degrees = [d for n, d in G.out_degree()]
        
        in_degree_hist = np.histogram(in_degrees, bins=[0, 1, 2, 5, 10, 100])[0].tolist() if in_degrees else []
        out_degree_hist = np.histogram(out_degrees, bins=[0, 1, 2, 5, 10, 100])[0].tolist() if out_degrees else []

        # Hub profiling: Nodes with disproportionately high degree
        hub_threshold = np.mean(in_degrees + out_degrees) + 2 * np.std(in_degrees + out_degrees) if (in_degrees and np.std(in_degrees + out_degrees) > 0) else 5
        hubs = [n for n in G.nodes() if G.degree(n) > hub_threshold]

        # 2. Triad Census (16 possible states of 3 nodes)
        try:
            triad_census = nx.triadic_census(G)
        except Exception:
            triad_census = {} # Fallback for very complex graphs if it fails

        # 3. Cycle Signature Vectors
        try:
            # Simple cycles can be expensive, limit the search depth
            cycles = list(nx.simple_cycles(G, length_bound=5))
            cycle_lengths = [len(c) for c in cycles]
            cycle_signature = {
                "total_cycles": len(cycles),
                "avg_length": float(np.mean(cycle_lengths)) if cycle_lengths else 0.0,
                "max_length": int(np.max(cycle_lengths)) if cycle_lengths else 0,
            }
        except Exception:
            cycle_signature = {"total_cycles": 0, "avg_length": 0.0, "max_length": 0}

        # 4. Connected Component Morphology (Weakly connected)
        components = list(nx.weakly_connected_components(G))
        comp_sizes = [len(c) for c in components]

        # 5. Graph Spectral Signatures (Eigenvector Centrality Approximation)
        try:
            eigen_centrality = nx.eigenvector_centrality_numpy(G, max_iter=100)
            spectral_variance = float(np.var(list(eigen_centrality.values())))
        except Exception:
            spectral_variance = 0.0

        fingerprint = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": density,
            "in_degree_hist": in_degree_hist,
            "out_degree_hist": out_degree_hist,
            "hub_count": len(hubs),
            "triad_census": triad_census,
            "cycle_signature": cycle_signature,
            "num_components": len(components),
            "max_component_size": int(np.max(comp_sizes)) if comp_sizes else 0,
            "spectral_variance": spectral_variance,
        }

        return fingerprint
