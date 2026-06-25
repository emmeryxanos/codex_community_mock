import os
import json
import httpx
from schemas import TicketRequest, TicketResponse

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are a CRM ticket classifier for a digital finance company (like bKash or similar mobile banking).
Your job is to read a customer support message and return a structured JSON classification.

You must respond ONLY with a valid JSON object — no markdown, no explanation, no backticks.

Classification rules:

case_type:
- "wrong_transfer": Customer sent money to the wrong recipient / wrong number / wrong account
- "payment_failed": A transaction failed, payment didn't go through, or balance may have been deducted without completion
- "refund_request": Customer is explicitly asking for a refund or to get their money back for a completed/intended transaction
- "phishing_or_social_engineering": Someone contacted the customer asking for OTP, PIN, password, or card details; suspicious calls/SMS claiming to be the company
- "other": App crashes, login issues, general inquiries, anything not fitting above

severity:
- "low": Informational, no financial impact, no urgency (e.g. app crash, general question)
- "medium": Moderate issue, some financial inconvenience but not urgent (e.g. small refund request)
- "high": Significant financial impact or customer distress (e.g. wrong transfer, failed payment with deducted balance)
- "critical": Active fraud, phishing in progress, large amounts at risk, or account compromise suspected

department:
- "customer_support": General issues, low severity refund_request, other
- "dispute_resolution": wrong_transfer, contested refund_request (medium/high severity)
- "payments_ops": payment_failed
- "fraud_risk": phishing_or_social_engineering

human_review_required:
- Set to true if severity is "critical" OR case_type is "phishing_or_social_engineering"
- Set to true if severity is "high" and financial loss is involved
- Otherwise false

confidence:
- A float between 0.0 and 1.0 reflecting how certain you are of the classification
- Be honest: use lower values when the message is ambiguous

agent_summary:
- One or two neutral, professional sentences summarizing the ticket for a human agent
- NEVER mention PIN, OTP, password, card number, or ask the customer to share any credentials
- Write in third person (e.g. "Customer reports...")
- Be factual and concise

Return exactly this JSON shape:
{
  "case_type": "...",
  "severity": "...",
  "department": "...",
  "agent_summary": "...",
  "human_review_required": true/false,
  "confidence": 0.0
}"""


def build_user_prompt(ticket: TicketRequest) -> str:
    parts = [f"Message: {ticket.message}"]
    if ticket.channel:
        parts.append(f"Channel: {ticket.channel}")
    if ticket.locale:
        parts.append(f"Locale: {ticket.locale}")
    return "\n".join(parts)


async def classify_ticket(ticket: TicketRequest) -> TicketResponse:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 512,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": build_user_prompt(ticket)}
        ],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
        resp.raise_for_status()

    data = resp.json()
    raw_text = data["content"][0]["text"].strip()

    # Strip accidental markdown fences
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    result = json.loads(raw_text)

    # Enforce human_review_required rule regardless of LLM output
    if result["severity"] == "critical" or result["case_type"] == "phishing_or_social_engineering":
        result["human_review_required"] = True

    # Clamp confidence
    result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.8))))

    return TicketResponse(ticket_id=ticket.ticket_id, **result)
