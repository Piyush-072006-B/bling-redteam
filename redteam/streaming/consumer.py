# ============================================================
# Kafka Consumer — Streaming Layer
# ============================================================
import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException

logger = logging.getLogger(__name__)


class RedTeamConsumer:
    """
    Base Kafka consumer for Red Team sandbox topics.
    Runs in a background thread. Calls handler(message_dict) for each event.
    Only processes events with _simulation=true.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: List[str],
        handler: Callable[[Dict[str, Any]], None],
        auto_offset_reset: str = "earliest",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.handler = handler
        self.auto_offset_reset = auto_offset_reset
        self._consumer: Optional[Consumer] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._connect()

    def _connect(self) -> None:
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": self.auto_offset_reset,
            "enable.auto.commit": True,
            "auto.commit.interval.ms": 5000,
            "session.timeout.ms": 30000,
            "heartbeat.interval.ms": 10000,
            "max.poll.interval.ms": 300000,
        }
        for attempt in range(10):
            try:
                self._consumer = Consumer(config)
                self._consumer.subscribe(self.topics)
                logger.info(
                    "Kafka consumer connected",
                    extra={"group_id": self.group_id, "topics": self.topics},
                )
                return
            except KafkaException as e:
                logger.warning(f"Consumer connect attempt {attempt+1}/10 failed: {e}")
                time.sleep(3)
        raise RuntimeError(f"Cannot connect Kafka consumer for group {self.group_id}")

    def _poll_loop(self) -> None:
        while self._running:
            try:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    payload = json.loads(msg.value().decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Failed to decode message: {e}")
                    continue

                # Sandbox isolation guard — only process simulation events
                if not payload.get("_simulation", False):
                    logger.warning(
                        "Received non-simulation event, skipping",
                        extra={"topic": msg.topic()},
                    )
                    continue

                try:
                    self.handler(payload)
                except Exception as e:
                    logger.error(f"Handler error: {e}", exc_info=True)

            except KafkaException as e:
                logger.error(f"Kafka poll error: {e}")
                time.sleep(1)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name=f"consumer-{self.group_id}",
        )
        self._thread.start()
        logger.info(f"Consumer thread started: {self.group_id}")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self._consumer:
            self._consumer.close()
        logger.info(f"Consumer stopped: {self.group_id}")
