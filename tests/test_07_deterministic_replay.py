import requests
import pytest
import hashlib
import json
import os

GENERATOR_URL = "http://localhost:8001"
MUTATOR_URL = "http://localhost:8004"

def _hash_topology(transactions):
    """Generate a consistent hash of the topology structure."""
    # Remove timestamps and random IDs which might differ across identical structural generations
    clean_txns = []
    for t in transactions:
        clean_t = {k: v for k, v in t.items() if k not in ["timestamp", "transaction_id", "simulation_id"]}
        clean_txns.append(clean_t)
        
    # Sort to ensure order doesn't affect hash if it's identical structurally
    # (Though deterministic mutator should preserve order too)
    clean_txns_sorted = sorted(clean_txns, key=lambda x: (x.get("sender_account", ""), x.get("receiver_account", ""), x.get("amount", 0)))
    
    encoded = json.dumps(clean_txns_sorted, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

def test_deterministic_mutation():
    """Verify that identical inputs and strategies produce identical graph mutations."""
    # 1. Generate a baseline topology
    resp = requests.post(f"{GENERATOR_URL}/generate", json={
        "attack_type": "layering_chain",
        "attack_depth": 3,
        "mutation_generation": 0,
        "tps": 10
    })
    assert resp.status_code == 200
    base_txns = resp.json()
    
    mut_payload = {
        "transactions": base_txns,
        "strategies": ["split_transaction", "delay_transfers"],
        "simulation_id": "sim_deterministic",
        "original_pattern": "layering_chain",
        "mutation_generation": 0,
        "detection_rate_before": 1.0,
        "account_pool_ids": ["acc_1", "acc_2", "acc_3", "acc_4", "acc_5"] # fixed pool for deterministic noise
    }
    
    # 2. Mutate run A
    resp_a = requests.post(f"{MUTATOR_URL}/mutate", json=mut_payload)
    assert resp_a.status_code == 200
    txns_a = resp_a.json()["transactions"]
    hash_a = _hash_topology(txns_a)
    
    # 3. Mutate run B (exact same input)
    resp_b = requests.post(f"{MUTATOR_URL}/mutate", json=mut_payload)
    assert resp_b.status_code == 200
    txns_b = resp_b.json()["transactions"]
    hash_b = _hash_topology(txns_b)
    
    # 4. Assert identical
    assert hash_a == hash_b, "Mutations are not deterministic! Hashes do not match."
    
    # Save replay evidence
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    replay_dir = os.path.join(workspace_root, "evidence", "replay_runs")
    os.makedirs(replay_dir, exist_ok=True)
    with open(os.path.join(replay_dir, "replay_hash.txt"), "w") as f:
        f.write(f"Hash A: {hash_a}\nHash B: {hash_b}\nDeterministic Match: {hash_a == hash_b}")
        
    print(f"Deterministic replay verified. Hash: {hash_a}")
