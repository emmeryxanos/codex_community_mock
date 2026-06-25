# CRM Ticket Sorter

A lightweight REST API that classifies customer support tickets for digital finance companies. Powered by Claude (Anthropic).

## What it does

Accepts a customer message and returns:
- **case_type** — wrong_transfer, payment_failed, refund_request, phishing_or_social_engineering, other
- **severity** — low, medium, high, critical
- **department** — customer_support, dispute_resolution, payments_ops, fraud_risk
- **agent_summary** — one-sentence human-readable summary
- **human_review_required** — true for phishing or critical cases
- **confidence** — 0.0–1.0

## LLM Used

Yes — `claude-sonnet-4-6` via Anthropic API.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/sort-ticket` | Classify a support ticket |

### Example Request

```bash
curl -X POST https://your-service.onrender.com/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "T-001",
    "channel": "app",
    "locale": "en",
    "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
  }'
```

### Example Response

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending 5000 BDT to an incorrect recipient and is requesting a reversal.",
  "human_review_required": true,
  "confidence": 0.92
}
```

## Local Setup

```bash
# Clone and enter directory
git clone <your-repo-url>
cd ticket-sorter

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run
uvicorn main:app --reload
```

API will be available at `http://localhost:8000`.

Interactive docs at `http://localhost:8000/docs`.

## Deploy to Render

1. Push this repo to GitHub (make it public)
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Render auto-detects `render.yaml` — just add your `ANTHROPIC_API_KEY` in the Environment tab
4. Click Deploy

## Project Structure

```
main.py          # FastAPI app with /health and /sort-ticket
classifier.py    # Anthropic API call and prompt logic
schemas.py       # Pydantic request/response models
render.yaml      # Render deployment config
requirements.txt
```

## Safety

- `agent_summary` never asks for or mentions PIN, OTP, password, or card numbers
- `human_review_required` is always `true` for phishing or critical severity — enforced in code, not just by the LLM
- API key stored as environment variable only — never in code or repository
