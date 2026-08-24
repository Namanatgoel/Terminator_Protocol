import time
from db import DatabaseRepository
from llm_engine import LLMRouter
from message_queue import MessageQueue

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
        print("Terminator Protocol Executor Started...")
        while True:
            records = self.db.fetch_and_lock_pending(limit=5)
            for rec in records:
                txn_id, tier, context = rec['txn_id'], rec['escalation_tier'], rec['agent_context']
                
                decision = self.llm.route_transaction(txn_id, rec['error_code'], rec['amount'], tier, context)
                action = decision.get("action", "silent_retry")
                delay = decision.get("delay_minutes", 60)
                new_context = decision.get("updated_context", context)
                
                self.execute_tier_action(txn_id, action, new_context, decision.get("offer_authorized", False))
                
                next_tier = tier + 1
                self.db.update_transaction(txn_id, "hard_failed" if next_tier > 4 else "pending", rec['retry_count'] + 1, next_tier, new_context)
                
                if next_tier <= 4:
                    self.mq.enqueue(txn_id, next_tier, new_context, time.time() + (delay * 60))
                
                print(f"Processed {txn_id} -> Action: {action} | Next Tier: {next_tier}")
            
            if not records:
                print("No pending transactions. Exiting loop.")
                break
            time.sleep(2)

if __name__ == "__main__":
    ExecutorService(DatabaseRepository(), LLMRouter(), MessageQueue()).process_loop()
