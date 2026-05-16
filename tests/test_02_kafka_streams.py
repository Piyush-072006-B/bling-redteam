import pytest
from confluent_kafka.admin import AdminClient

KAFKA_BOOTSTRAP_SERVERS = "localhost:29092"
EXPECTED_TOPICS = {
    "transactions.sandbox",
    "graph.updates.sandbox",
    "fraud.alerts.sandbox",
    "redteam.metrics",
}

def test_kafka_topics_exist():
    """Verify that all required Kafka topics are created and accessible."""
    admin_client = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    
    # Fetch cluster metadata
    metadata = admin_client.list_topics(timeout=10)
    
    # Extract topics
    existing_topics = set(metadata.topics.keys())
    
    missing_topics = EXPECTED_TOPICS - existing_topics
    
    assert not missing_topics, f"Missing Kafka topics: {missing_topics}"
    
    print(f"All expected Kafka topics are present: {EXPECTED_TOPICS}")
