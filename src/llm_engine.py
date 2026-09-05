import os
import json
import warnings
import time
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI

try:
    import torch
    if not torch.cuda.is_available():
        warnings.warn("Hardware Acceleration (RTX 5050) not available. Falling back to CPU.", RuntimeWarning)
except ImportError:
    warnings.warn("Torch not installed, unable to verify hardware acceleration.", RuntimeWarning)


class ActionDecision(BaseModel):
    action: Literal["silent_retry", "whatsapp_ping", "voice_call", "fomo_alert"] = "silent_retry"
    delay_minutes: int = Field(default=60, ge=0)
    updated_context: str = Field(default="")
    offer_authorized: bool = Field(default=False)
    is_fallback: bool = Field(default=False)

    @classmethod
    def fallback(cls, context: str) -> "ActionDecision":
        return cls(
            action="silent_retry",
            delay_minutes=60,
            updated_context=f"{context} [LLM/Parse Error - conservative fallback]",
            offer_authorized=False,
            is_fallback=True,
        )

_SYSTEM_PROMPT = (
    "You are the Terminator Protocol Router for Razorpay Revenue Recovery.\n"
    "Analyze the failed transaction and determine the next recovery action based on the escalation tier.\n"
    "Rules:\n"
    "Tier 1: Silent retry.  Output action: 'silent_retry'.\n"
    "Tier 2: WhatsApp soft nudge. Output action: 'whatsapp_ping'.\n"
    "Tier 3: AI voice negotiation. Output action: 'voice_call'. "
    "If prior context shows price sensitivity, set offer_authorized=true (up to 10% discount).\n"
    "Tier 4: Final FOMO push. Output action: 'fomo_alert'.\n\n"
    "Output ONLY valid JSON with these exact keys:\n"
    "  action (string), delay_minutes (int), updated_context (string), offer_authorized (bool)"
)

class LLMRouter:
    def __init__(self, base_url=None, api_key=None):
        self.client = OpenAI(
            base_url=base_url or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=api_key or os.getenv("LLM_API_KEY", "sk-buildathon"),
        )

    def route_transaction(self, txn_id: str, error_code: str, amount: float, tier: int, context: str) -> ActionDecision:
        prompt = f"Txn: {txn_id} | Amount: ₹{amount:.2f} | Error: {error_code} | Tier: {tier} | Context: {context}"
        for attempt in range(3):
            try:
                resp = self.client.chat.completions.create(
                    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
                    messages=[{"role": "system", "content": _SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                return ActionDecision(**json.loads(resp.choices[0].message.content))
            except (Exception, ValidationError):
                if attempt < 2:
                    time.sleep(1)
        return ActionDecision.fallback(context)
