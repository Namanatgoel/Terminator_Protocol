import json
import os
from confluent_kafka import Producer, Consumer

class MessageQueue:
    def __init__(self, broker=None, topic="terminator_escalations"):
        self.broker = broker or os.getenv("KAFKA_BROKER", "localhost:9092")
        self.topic = topic
        self.producer = Producer({'bootstrap.servers': self.broker})

    def _delivery_report(self, err, msg):
        if err: print(f"Delivery failed: {err}")

    def enqueue(self, txn_id, tier, context, execute_at_ts):
        payload = json.dumps({"txn_id": str(txn_id), "tier": tier, "context": context, "execute_at": execute_at_ts})
        self.producer.produce(self.topic, payload.encode('utf-8'), callback=self._delivery_report)
        self.producer.flush(timeout=2.0)

    def get_consumer(self, group_id="terminator_workers"):
        c = Consumer({'bootstrap.servers': self.broker, 'group.id': group_id, 'auto.offset.reset': 'earliest'})
        c.subscribe([self.topic])
        return c
