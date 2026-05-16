import requests
import pytest
import time

SERVICES = {
    "topology_generator": "http://localhost:8001/health",
    "topology_graph_engine": "http://localhost:8002/health",
    "evaluation_harness": "http://localhost:8003/health",
    "topology_mutator": "http://localhost:8004/health",
    "escape_analyzer": "http://localhost:8005/health",
}

@pytest.mark.parametrize("service_name, url", SERVICES.items())
def test_service_health(service_name, url):
    """Verify that all microservices are up and reporting healthy."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
            print(f"{service_name} is healthy.")
            return
        except (requests.ConnectionError, AssertionError) as e:
            if attempt == max_retries - 1:
                pytest.fail(f"Service {service_name} failed health check at {url}. Error: {e}")
            time.sleep(2)
