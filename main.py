from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from schemas import TicketRequest, TicketResponse
from classifier import classify_ticket
import httpx

app = FastAPI(
    title="CRM Ticket Sorter",
    description="Classifies customer support tickets for a digital finance company",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ticket-sorter"}


@app.post("/sort-ticket", response_model=TicketResponse)
async def sort_ticket(ticket: TicketRequest):
    if not ticket.message or not ticket.message.strip():
        raise HTTPException(status_code=422, detail="message field must not be empty")

    try:
        result = await classify_ticket(ticket)
        return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream LLM API error: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
