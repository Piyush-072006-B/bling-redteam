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
    
    # 2. Poll the Escape Analyzer with a timeout to allow consumption and check_export verification
    found = False
    data = {}
    for attempt in range(10):
        time.sleep(1)
        try:
            export_resp = requests.get(f"{ESCAPE_ANALYZER_URL}/export/evasions?limit=100")
            if export_resp.status_code == 200:
                data = export_resp.json()
                variations = data.get("exported_topology_variations", [])
                for v in variations:
                    if v.get("simulation_id") == "sim_e2e_test_export":
                        found = True
                        assert v.get("topology_type") == "mule_network"
                        assert v.get("mutation_generation") == 2
                        break
            if found:
                break
        except Exception:
            pass

    assert found, "Mock evasion event was not found in the exported topologies within timeout"
    assert data.get("validation_required") is True, "Must enforce human validation safeguard"
    print("Successfully verified the evasion export pipeline.")
