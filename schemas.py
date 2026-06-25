from pydantic import BaseModel
from typing import Optional, Literal


class TicketRequest(BaseModel):
    ticket_id: str
    channel: Optional[Literal["app", "sms", "call_center", "merchant_portal"]] = None
    locale: Optional[Literal["bn", "en", "mixed"]] = None
    message: str


class TicketResponse(BaseModel):
    ticket_id: str
    case_type: Literal[
        "wrong_transfer",
        "payment_failed",
        "refund_request",
        "phishing_or_social_engineering",
        "other",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    department: Literal[
        "customer_support",
        "dispute_resolution",
        "payments_ops",
        "fraud_risk",
    ]
    agent_summary: str
    human_review_required: bool
    confidence: float
