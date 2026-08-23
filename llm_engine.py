from openai import OpenAI
import json

# Lazy config: local vLLM endpoint hosting Qwen-2.5-7B
# To run vLLM: python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-7B-Instruct-AWQ --quantization awq
client = OpenAI(base_url="http://localhost:8000/v1", api_key="sk-buildathon")

SYSTEM_PROMPT = """You are the Terminator Protocol Router for Razorpay Revenue Recovery.
You analyze failed transactions and determine the next action and context based on the escalation tier.
Rules:
Tier 1: Silent Retry (Output action: 'silent_retry')
Tier 2: WhatsApp Soft Ping (Output action: 'whatsapp_ping')
Tier 3: Voice Negotiation (Output action: 'voice_call'. If user showed price sensitivity in context, authorize up to 10% discount).
Tier 4: Terminal FOMO (Output action: 'fomo_alert')

Output MUST be valid JSON with keys:
- action (string): The next action to take
- delay_minutes (int): Minutes to wait before execution
- updated_context (string): Summary of memory
- offer_authorized (bool): True if discount is authorized
"""

def route_transaction(txn_id, error_code, amount, tier, context):
    """Pass state to Qwen and get determinist routing JSON."""
    prompt = f"Txn: {txn_id} | Amount: {amount} | Error: {error_code} | Tier: {tier} | Context: {context}"
    
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct-AWQ",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0, # Deterministic routing
            response_format={ "type": "json_object" }
        )
        decision = json.loads(response.choices[0].message.content)
        return decision
    except Exception as e:
        # Fallback ceiling: If LLM fails or is disconnected, default to conservative retry.
        return {
            "action": "silent_retry",
            "delay_minutes": 60,
            "updated_context": f"{context} [LLM Parse Error or Disconnected]",
            "offer_authorized": False
        }
