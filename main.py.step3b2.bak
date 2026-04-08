from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from decision_engine import decide
from generator import build_response
from logging_utils import append_request_log
from router import (
    coerce_field_value,
    get_card_by_id,
    get_top_candidates,
    load_all_cards,
    should_continue_pending_flow,
)
from validator import validate_response


app = FastAPI(title="MOH Assistant Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    state: dict[str, Any] | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "cards_loaded": len(load_all_cards()),
    }


@app.post("/chat")
def chat(request: ChatRequest):
    incoming_state = request.state or {}
    collected_fields = incoming_state.get("collected_fields", {})
    if not isinstance(collected_fields, dict):
        collected_fields = {}

    pending_card_id = incoming_state.get("pending_card_id")
    pending_field = incoming_state.get("pending_field")
    pending_card = get_card_by_id(pending_card_id) if pending_card_id else None

    use_pending_flow = False
    if pending_card and pending_field:
        use_pending_flow = should_continue_pending_flow(request.message, pending_field)

    if use_pending_flow:
        coerced_value = coerce_field_value(pending_field, request.message, pending_card)
        if coerced_value is not None:
            collected_fields[pending_field] = coerced_value
        candidates = get_top_candidates(request.message, top_k=5, forced_card=pending_card)
    else:
        collected_fields = {}
        candidates = get_top_candidates(request.message, top_k=5, forced_card=None)

    decision = decide(
        user_text=request.message,
        candidates=candidates,
        collected_fields=collected_fields,
    )

    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
    )

    response = validate_response(response)

    append_request_log({
        "message": request.message,
        "top_candidates": [
            {
                "id": c["card"].get("id"),
                "category": c["card"].get("category"),
                "score": c["score"]
            }
            for c in candidates
        ],
        "action": response.get("action"),
        "matched_card_id": response.get("matched_card_id"),
        "follow_up_question": response.get("follow_up_question"),
        "escalation_reason": response.get("escalation_reason"),
        "state": response.get("state")
    })

    return response
