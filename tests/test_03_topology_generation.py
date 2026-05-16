import requests
import pytest

GENERATOR_URL = "http://localhost:8001"

@pytest.mark.parametrize("attack_type, depth", [
    ("layering_chain", 3),
    ("layering_chain", 5),
    ("round_trip", 4),
    ("mule_network", 5),
    ("structuring", 3),
    ("velocity_attack", 4),
    ("dormant_activation", 3),
    ("fan_in_fan_out", 3)
])
def test_topology_generation(attack_type, depth):
    """Test generation of various synthetic laundering graph topologies."""
    payload = {
        "attack_type": attack_type,
        "attack_depth": depth,
        "mutation_generation": 0,
        "tps": 10
    }
    
    response = requests.post(f"{GENERATOR_URL}/generate", json=payload)
    assert response.status_code == 200, f"Failed to generate {attack_type}"
    
    txns = response.json()
    assert isinstance(txns, list), "Response should be a list of transactions"
    assert len(txns) > 0, f"Expected > 0 transactions for {attack_type}, got 0"
    
    # Assert base structure of the first transaction
    first_txn = txns[0]
    assert "sender_account" in first_txn
    assert "receiver_account" in first_txn
    assert "amount" in first_txn
    assert "attack_type" in first_txn
    assert first_txn["attack_type"] == attack_type
    
    print(f"Successfully generated {len(txns)} transactions for {attack_type} (Depth {depth})")
