from confluent_kafka import Producer, Consumer
import json
import time

# Lazy config: Redpanda default localhost
KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "terminator_escalations"

producer_conf = {'bootstrap.servers': KAFKA_BROKER}
producer = Producer(**producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def enqueue_escalation(txn_id, tier, context, execute_at_ts):
    """Push escalation task to Redpanda queue."""
    payload = {
        "txn_id": str(txn_id),
        "tier": tier,
        "context": context,
        "execute_at": execute_at_ts
    }
    producer.produce(TOPIC_NAME, json.dumps(payload).encode('utf-8'), callback=delivery_report)
    producer.flush()

def get_consumer(group_id="terminator_workers"):
    consumer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    }
    c = Consumer(**consumer_conf)
    c.subscribe([TOPIC_NAME])
    return c
