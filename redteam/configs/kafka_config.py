# ============================================================
# Shared Kafka Configuration
# ============================================================
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class KafkaConfig:
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    auto_offset_reset: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
    enable_auto_commit: bool = True
    max_poll_interval_ms: int = 300000
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 10000
    request_timeout_ms: int = 40000
    retry_backoff_ms: int = 500
    max_retries: int = 5


class KafkaTopics:
    TRANSACTIONS = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "transactions.sandbox")
    GRAPH_UPDATES = os.getenv("KAFKA_TOPIC_GRAPH_UPDATES", "graph.updates.sandbox")
    ALERTS = os.getenv("KAFKA_TOPIC_ALERTS", "fraud.alerts.sandbox")
    METRICS = os.getenv("KAFKA_TOPIC_METRICS", "redteam.metrics")

    ALL_TOPICS: List[str] = [
        TRANSACTIONS,
        GRAPH_UPDATES,
        ALERTS,
        METRICS,
    ]


class ConsumerGroups:
    GRAPH_ENGINE = os.getenv("KAFKA_GROUP_ID_GRAPH", "graph-engine-group")
    DETECTOR = os.getenv("KAFKA_GROUP_ID_DETECTOR", "detector-group")
    METRICS = os.getenv("KAFKA_GROUP_ID_METRICS", "metrics-group")
    SIMULATION_RUNNER = "simulation-runner-group"


KAFKA_CONFIG = KafkaConfig()
