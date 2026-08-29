import time
import json
import logging
from db import DatabaseRepository
from llm_engine import LLMRouter
from message_queue import MessageQueue

# Structured JSON logging for Datadog/ELK ingestion
logger = logging.getLogger("executor")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'))
logger.addHandler(handler)

class ExecutorService:
    def __init__(self, db: DatabaseRepository, llm: LLMRouter, mq: MessageQueue):
        self.db = db
        self.llm = llm
        self.mq = mq

    def execute_tier_action(self, txn_id, action, context, offer_authorized):
        # Technical Debt: Bounded mock execution. 
        # Upgrade path: Integrate with Razorpay/Retell APIs.
        outcomes = {
            "silent_retry": "Retry Scheduled via Redpanda",
            "whatsapp_ping": "Sent Razorpay UPI Deep Link via WhatsApp",
            "fomo_alert": "Terminal FOMO Email/SMS Sent",
            "voice_call": "Retell AI Webhook Triggered with 10% EMI Offer" if offer_authorized else "Retell AI Webhook Triggered (Standard Negotiation)"
        }
        outcome = outcomes.get(action, "Unknown Action Triggered")
        self.db.log_audit(txn_id, action, outcome)
        return outcome

    def process_loop(self):
        logger.info(json.dumps({"event": "executor_started"}))
        while True:
            records = self.db.fetch_and_lock_pending(limit=5)
            for rec in records:
                txn_id, tier, context = rec['txn_id'], rec['escalation_tier'], rec['agent_context']
                
                decision = self.llm.route_transaction(txn_id, rec['error_code'], rec['amount'], tier, context)
                self.execute_tier_action(txn_id, decision.action, decision.updated_context, decision.offer_authorized)
                
                next_tier = tier + 1
                
                # TechDebt (Outbox Pattern): Pushing to queue before DB update ensures we don't drop tasks, but may cause duplicates.
                if next_tier <= 4:
                    self.mq.enqueue(txn_id, next_tier, decision.updated_context, time.time() + (decision.delay_minutes * 60))
                self.db.update_transaction(txn_id, "hard_failed" if next_tier > 4 else "pending", rec['retry_count'] + 1, next_tier, decision.updated_context)
                
                logger.info(json.dumps({"event": "transaction_processed", "txn_id": txn_id, "action": decision.action, "next_tier": next_tier}))
            
            if not records:
                logger.info(json.dumps({"event": "executor_idle"}))
                break
            time.sleep(2)

if __name__ == "__main__":
    ExecutorService(DatabaseRepository(), LLMRouter(), MessageQueue()).process_loop()
