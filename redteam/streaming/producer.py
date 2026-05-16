# ============================================================
# Kafka Producer — Streaming Layer
# ============================================================
import json
import logging
import time
from typing import Any, Dict, Optional
from confluent_kafka import Producer, KafkaException

logger = logging.getLogger(__name__)


class RedTeamProducer:
    """
    Kafka producer for all Red Team sandbox events.
    All published events are tagged with _simulation=true.
    """

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer: Optional[Producer] = None
        self._connect()

    def _connect(self) -> None:
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "acks": "all",
            "retries": 5,
            "retry.backoff.ms": 500,
            "linger.ms": 5,
            "batch.size": 16384,
            "compression.type": "snappy",
            "enable.idempotence": True,
        }
        for attempt in range(10):
            try:
                self._producer = Producer(config)
                logger.info(
                    "Kafka producer connected",
                    extra={"bootstrap_servers": self.bootstrap_servers},
                )
                return
            except KafkaException as e:
                logger.warning(f"Producer connect attempt {attempt+1}/10 failed: {e}")
                time.sleep(3)
        raise RuntimeError(f"Cannot connect Kafka producer to {self.bootstrap_servers}")

    def _delivery_report(self, err, msg) -> None:
        if err:
            logger.error(
                "Delivery failed",
                extra={"topic": msg.topic(), "error": str(err)},
            )
        else:
            logger.debug(
                "Message delivered",
                extra={"topic": msg.topic(), "partition": msg.partition()},
            )

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """Publish a JSON payload. Enforces _simulation=true."""
        payload["_simulation"] = True

        try:
            self._producer.produce(
                topic=topic,
                value=json.dumps(payload, default=str).encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                callback=self._delivery_report,
            )
            self._producer.poll(0)  # non-blocking trigger callbacks
        except KafkaException as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            raise

    def flush(self, timeout: float = 10.0) -> None:
        if self._producer:
            self._producer.flush(timeout)

    def close(self) -> None:
        self.flush()
        logger.info("Kafka producer closed")
