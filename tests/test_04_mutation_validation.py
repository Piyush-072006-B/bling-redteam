import requests
import pytest

GENERATOR_URL = "http://localhost:8001"
MUTATOR_URL = "http://localhost:8004"

def test_topology_mutation():
    """Verify that the Mutator successfully alters a baseline topology."""
    # 1. Generate baseline topology
    gen_payload = {
        "attack_type": "layering_chain",
        "attack_depth": 3,
        "mutation_generation": 0,
        "tps": 10
    }
    gen_resp = requests.post(f"{GENERATOR_URL}/generate", json=gen_payload)
    assert gen_resp.status_code == 200
    base_txns = gen_resp.json()
    assert len(base_txns) > 0

    # 2. Mutate the topology
    mut_payload = {
        "transactions": base_txns,
        "strategies": ["split_transaction", "delay_transfers"],
        "simulation_id": "sim_test_mutation",
        "original_pattern": "layering_chain",
        "mutation_generation": 0,
        "detection_rate_before": 1.0
    }
    
    mut_resp = requests.post(f"{MUTATOR_URL}/mutate", json=mut_payload)
    assert mut_resp.status_code == 200, "Mutation request failed"
    
    result = mut_resp.json()
    assert "mutated_count" in result
    assert "strategies_applied" in result
    assert "transactions" in result
    
    mutated_txns = result["transactions"]
    
    # 3. Assert structural changes
    assert len(mutated_txns) > len(base_txns), "split_transaction should increase transaction count"
    
    # Check that mutation generation increased
    for t in mutated_txns:
        assert t.get("mutation_generation") == 1, "Mutation generation should be incremented"
        assert t.get("simulation_id") == "sim_test_mutation"
        
    print(f"Successfully mutated baseline (count: {len(base_txns)}) to evasive topology (count: {len(mutated_txns)})")
