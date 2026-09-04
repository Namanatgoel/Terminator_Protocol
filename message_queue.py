import json
import logging
import os
from confluent_kafka import Producer, Consumer, KafkaException

logger = logging.getLogger("message_queue")

class MessageQueue:
    def __init__(self, broker=None, topic="terminator_escalations"):
        self.broker = broker or os.getenv("KAFKA_BROKER", "localhost:9092")
        self.topic = topic
        self._producer = None  # Lazy-init: avoids blocking startup when Redpanda is offline.

    @property
    def producer(self) -> Producer:
        if self._producer is None:
            self._producer = Producer({"bootstrap.servers": self.broker})
        return self._producer

    def _delivery_report(self, err, msg):
        if err:
            logger.warning(json.dumps({"event": "kafka_delivery_failed", "error": str(err)}))

    def enqueue(self, txn_id, tier, context, execute_at_ts):
        payload = json.dumps({"txn_id": str(txn_id), "tier": tier, "context": context, "execute_at": execute_at_ts})
        try:
            self.producer.produce(self.topic, payload.encode("utf-8"), callback=self._delivery_report)
            self.producer.flush(timeout=2.0)
        except KafkaException as e:
            logger.warning(json.dumps({"event": "kafka_enqueue_failed", "txn_id": txn_id, "error": str(e)}))

    def get_consumer(self, group_id="terminator_workers") -> Consumer:
        c = Consumer({"bootstrap.servers": self.broker, "group.id": group_id, "auto.offset.reset": "earliest"})
        c.subscribe([self.topic])
        return c

