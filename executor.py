import time
import json
import logging
from db import DatabaseRepository
from llm_engine import LLMRouter
from message_queue import MessageQueue

logger = logging.getLogger("executor")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":%(message)s}'))
logger.addHandler(_handler)

_ACTION_OUTCOMES = {
    "silent_retry": "Retry scheduled via Redpanda",
    "whatsapp_ping": "Razorpay UPI deep-link sent via WhatsApp",
    "fomo_alert": "Terminal FOMO email/SMS dispatched",
}

class ExecutorService:
    def __init__(self, db: DatabaseRepository, llm: LLMRouter, mq: MessageQueue):
        self.db = db
        self.llm = llm
        self.mq = mq

    def _execute_action(self, txn_id: str, amount: float, decision) -> str:
        # Technical Debt: Mock execution stubs.
        # Upgrade path: Razorpay Payments API, Twilio WhatsApp, Retell AI webhooks.
        if decision.action == "voice_call":
            outcome = ("Retell AI webhook triggered — 10% EMI offer authorised"
                       if decision.offer_authorized
                       else "Retell AI webhook triggered — standard negotiation")
        else:
            outcome = _ACTION_OUTCOMES.get(decision.action, "Unknown action")
        self.db.log_audit(
            txn_id=txn_id,
            amount=amount,
            action=decision.action,
            outcome=outcome,
            ai_reasoning=decision.updated_context,
            offer_authorized=decision.offer_authorized,
        )
        return outcome

    def process_loop(self):
        logger.info(json.dumps({"event": "executor_started"}))
        while True:
            records = self.db.fetch_and_lock_pending(limit=5)
            for rec in records:
                txn_id = rec["txn_id"]
                tier = rec["escalation_tier"]
                amount = rec["amount"]
                context = rec["agent_context"]

                decision = self.llm.route_transaction(txn_id, rec["error_code"], amount, tier, context)
                self._execute_action(txn_id, amount, decision)

                # Only advance escalation tier when the LLM gave a real decision,
                # not when it fell back due to a transient network error.
                next_tier = tier + (0 if decision.is_fallback else 1)
                final_status = "hard_failed" if next_tier > 4 else "pending"

                if next_tier <= 4 and not decision.is_fallback:
                    self.mq.enqueue(txn_id, next_tier, decision.updated_context, time.time() + decision.delay_minutes * 60)
                self.db.update_transaction(txn_id, final_status, rec["retry_count"] + 1, next_tier, decision.updated_context)

                logger.info(json.dumps({
                    "event": "txn_processed", "txn_id": txn_id,
                    "action": decision.action, "next_tier": next_tier,
                    "is_fallback": decision.is_fallback, "amount": amount,
                }))

            if not records:
                logger.info(json.dumps({"event": "executor_idle_batch_complete"}))
                break
            time.sleep(2)

if __name__ == "__main__":
    ExecutorService(DatabaseRepository(), LLMRouter(), MessageQueue()).process_loop()

