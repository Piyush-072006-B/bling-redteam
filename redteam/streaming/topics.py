# ============================================================
# Kafka Topic Definitions
# ============================================================
import os


class Topics:
    TRANSACTIONS = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "transactions.sandbox")
    GRAPH_UPDATES = os.getenv("KAFKA_TOPIC_GRAPH_UPDATES", "graph.updates.sandbox")
    ALERTS = os.getenv("KAFKA_TOPIC_ALERTS", "fraud.alerts.sandbox")
    METRICS = os.getenv("KAFKA_TOPIC_METRICS", "redteam.metrics")

    @classmethod
    def all(cls):
        return [cls.TRANSACTIONS, cls.GRAPH_UPDATES, cls.ALERTS, cls.METRICS]
