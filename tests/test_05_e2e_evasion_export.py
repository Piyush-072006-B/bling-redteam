import requests
import pytest
import time
import json
from confluent_kafka import Producer

ESCAPE_ANALYZER_URL = "http://localhost:8005"
KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"

def test_evasion_export_pipeline():
    """Verify that the Escape Analyzer correctly captures and exports evasive topologies."""
    # 1. Publish a mock evasion event directly to Kafka to bypass the timing
    # constraints of the full Evaluation Harness loop.
    producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    
    mock_evasion_event = {
        "simulation_id": "sim_e2e_test_export",
        "evaluation_id": "eval_test_123",
        "topology_type": "mule_network",
        "mutation_generation": 2,
        "evades_heuristics": True,
        "evaluation_latency_ms": 12.5,
        "combined_risk_score": 0.2,
        "_simulation": True
    }
    
    producer.produce(
        topic="fraud.alerts.sandbox",
        key="sim_e2e_test_export",
        value=json.dumps(mock_evasion_event).encode('utf-8')
    )
    producer.flush(timeout=5)
    
    # 2. Give the Escape Analyzer time to consume the message
    time.sleep(3)
    
    # 3. Query the export endpoint
    export_resp = requests.get(f"{ESCAPE_ANALYZER_URL}/export/evasions")
    assert export_resp.status_code == 200, "Export endpoint failed"
    
    data = export_resp.json()
    assert "exported_topology_variations" in data
    assert "validation_required" in data
    assert data["validation_required"] is True, "Must enforce human validation safeguard"
    
    # 4. Verify our specific event is in the export
    variations = data["exported_topology_variations"]
    found = False
    for v in variations:
        if v.get("simulation_id") == "sim_e2e_test_export":
            found = True
            assert v.get("topology_type") == "mule_network"
            assert v.get("mutation_generation") == 2
            break
            
    assert found, "Mock evasion event was not found in the exported topologies"
    print("Successfully verified the evasion export pipeline.")
