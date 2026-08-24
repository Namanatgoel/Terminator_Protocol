import os
import json
import warnings
from openai import OpenAI

try:
    import torch
    if not torch.cuda.is_available():
        warnings.warn("Hardware Acceleration (RTX 5050) not available. Falling back to CPU.", RuntimeWarning)
except ImportError:
    warnings.warn("Torch not installed, unable to verify hardware acceleration.", RuntimeWarning)

class LLMRouter:
    def __init__(self, base_url=None, api_key=None):
        self.client = OpenAI(
            base_url=base_url or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=api_key or os.getenv("LLM_API_KEY", "sk-buildathon")
        )
        self.system_prompt = (
            "You are the Terminator Protocol Router for Razorpay Revenue Recovery.\n"
            "You analyze failed transactions and determine the next action and context based on the escalation tier.\n"
            "Rules:\n"
            "Tier 1: Silent Retry (Output action: 'silent_retry')\n"
            "Tier 2: WhatsApp Soft Ping (Output action: 'whatsapp_ping')\n"
            "Tier 3: Voice Negotiation (Output action: 'voice_call'. If user showed price sensitivity in context, authorize up to 10% discount).\n"
            "Tier 4: Terminal FOMO (Output action: 'fomo_alert')\n\n"
            "Output MUST be valid JSON with keys:\n"
            "- action (string): The next action to take\n"
            "- delay_minutes (int): Minutes to wait before execution\n"
            "- updated_context (string): Summary of memory\n"
            "- offer_authorized (bool): True if discount is authorized"
        )

    def route_transaction(self, txn_id, error_code, amount, tier, context):
        prompt = f"Txn: {txn_id} | Amount: {amount} | Error: {error_code} | Tier: {tier} | Context: {context}"
        try:
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct-AWQ",
                messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "action": "silent_retry",
                "delay_minutes": 60,
                "updated_context": f"{context} [LLM Parse Error or Disconnected]",
                "offer_authorized": False
            }
