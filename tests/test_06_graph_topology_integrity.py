import requests
import pytest
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import json
import sys

# Resolve sys.path for redteam import
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from redteam.canonical_exporter import export_pattern

GENERATOR_URL = "http://localhost:8001"

def _build_graph(transactions):
    """Convert a list of transaction dicts into a NetworkX DiGraph."""
    G = nx.DiGraph()
    for t in transactions:
        u = t["sender_account"]
        v = t["receiver_account"]
        w = float(t.get("amount", 0))
        if not G.has_node(u): G.add_node(u)
        if not G.has_node(v): G.add_node(v)
        G.add_edge(u, v, weight=w, timestamp=t.get("timestamp"))
    return G

def _save_evidence(G, name, transactions):
    """Save graph snapshot and JSON export."""
    snapshots_dir = os.path.join(workspace_root, "evidence", "graph_snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)
    
    # Save image
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=8)
    img_path = os.path.join(snapshots_dir, f"{name}.png")
    plt.savefig(img_path)
    plt.close()
    
    # Save JSON via canonical exporter layer
    export_pattern(transactions, f"{name}.json")

@pytest.mark.parametrize("attack_type", [
    "round_trip", "layering_chain", "mule_network", 
    "fan_in_fan_out", "structuring", "velocity_attack"
])
def test_topology_integrity(attack_type):
    """Validate that generated graph structures preserve expected mathematical properties."""
    depth = 4 if attack_type != "mule_network" else 2
    
    resp = requests.post(f"{GENERATOR_URL}/generate", json={
        "attack_type": attack_type,
        "attack_depth": depth,
        "mutation_generation": 0,
        "tps": 10
    })
    assert resp.status_code == 200
    txns = resp.json()
    
    G = _build_graph(txns)
    _save_evidence(G, f"integrity_{attack_type}", txns)
    
    if attack_type == "round_trip":
        cycles = list(nx.simple_cycles(G))
        assert len(cycles) >= 1, "Round trip must contain at least one cycle"
        
    elif attack_type == "layering_chain":
        # Find longest path
        longest_path = 0
        for source in G.nodes():
            for target in G.nodes():
                if source != target and nx.has_path(G, source, target):
                    paths = list(nx.all_simple_paths(G, source, target))
                    for p in paths:
                        longest_path = max(longest_path, len(p) - 1)
        assert longest_path >= depth, "Layering chain must have path depth >= attack depth"
        
    elif attack_type == "mule_network":
        out_degrees = [d for n, d in G.out_degree()]
        assert max(out_degrees) > 2, "Mule network must contain high out-degree hub nodes"
        
    elif attack_type == "fan_in_fan_out":
        in_degrees = [d for n, d in G.in_degree()]
        out_degrees = [d for n, d in G.out_degree()]
        assert max(in_degrees) >= 2, "Must contain high in-degree node"
        assert max(out_degrees) >= 2, "Must contain high out-degree node"
        
    elif attack_type == "structuring":
        amounts = [t["amount"] for t in txns]
        # Structuring generates multiple sub-threshold transactions
        assert len(amounts) >= 3, "Structuring must contain multiple fragmented transactions"
        assert all(a < 10000 for a in amounts), "Amounts must be sub-threshold (<10k)"
        
    elif attack_type == "velocity_attack":
        # Velocity attack should have multiple transactions in a short time
        assert len(txns) >= 5, "Velocity attack must contain high transaction density"
        
    print(f"Topology integrity verified for {attack_type}.")
