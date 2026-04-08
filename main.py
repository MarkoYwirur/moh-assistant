from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from decision_engine import decide
from generator import build_response
from logging_utils import append_request_log
from router import (
    _match_field_values_from_card,
    coerce_field_value,
    get_card_by_id,
    get_top_candidates,
    load_all_cards,
    normalize_text,
    should_continue_pending_flow,
)
from validator import validate_response
from app.controller_v2 import run_controller_v2


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


COMPLAINT_PROCEDURE_SIGNALS = (
    "ինչ տվյալներ",
    "ինչպես է քննվում",
    "բողոքը ինչպես է քննվում",
    "ինչ է լինում հետո",
    "բողոքից հետո",
    "բողոք ներկայացնելուց հետո",
    "ինչ քայլերով",
    "ինչպես բողոք ներկայացնել",
    "ինչ ժամկետում պետք է բողոք ներկայացնել",
    "մեկ տարվա ընթացքում բողոք",
)

COMPLAINT_SERVICE_PROCEDURE_SIGNALS = (
    "ծառայություն",
    "կազմակերպում",
    "հիվանդանոց",
    "վարչական",
    "inspection",
    "տեսչական",
)

COMPLAINT_CONTACT_SIGNALS = (
    "որտեղ դիմել",
    "հեռախոս",
    "8003",
    "կապ",
    "թեժ գիծ",
    "զանգահարել",
)

COMPLAINT_ETHICS_SIGNALS = (
    "բժշկի վարքագիծ",
    "բուժաշխատողի վարքագիծ",
    "էթիկա",
    "խախտում",
    "էթիկայի հանձնաժողով",
)

COMPLAINT_DISPUTE_SIGNALS = (
    "վճարել եմ",
    "պետք է անվճար լիներ",
    "գումար",
    "վճարովի",
)


def _is_service_procedure_complaint(normalized: str) -> bool:
    has_complaint_anchor = any(term in normalized for term in ("բողոք", "բողոք ներկայացնել", "գանգատ"))
    if not has_complaint_anchor:
        return False

    has_contact_signal = any(term in normalized for term in COMPLAINT_CONTACT_SIGNALS)
    has_ethics_signal = any(term in normalized for term in COMPLAINT_ETHICS_SIGNALS)
    has_child_signal = "երեխա" in normalized
    has_service_signal = any(term in normalized for term in COMPLAINT_SERVICE_PROCEDURE_SIGNALS)

    return has_service_signal and not (has_contact_signal or has_ethics_signal or has_child_signal)


def _infer_complaint_subtype(user_text: str) -> str | None:
    normalized = normalize_text(user_text)
    if not normalized:
        return None

    has_complaint_anchor = any(term in normalized for term in ("բողոք", "գանգատ"))
    is_child_medical_aid_contact = (
        "բողոք" in normalized
        and any(term in normalized for term in ("երեխայի բժշկական օգնություն", "երեխաների բժշկական օգնություն", "սպասարկման մասին"))
    )

    if any(term in normalized for term in COMPLAINT_CONTACT_SIGNALS):
        return "contact"

    if is_child_medical_aid_contact:
        return "contact"

    if any(term in normalized for term in COMPLAINT_DISPUTE_SIGNALS):
        return "dispute"

    if any(term in normalized for term in COMPLAINT_ETHICS_SIGNALS):
        return "ethics"

    if _is_service_procedure_complaint(normalized):
        return "service_procedure"

    if has_complaint_anchor and any(term in normalized for term in COMPLAINT_PROCEDURE_SIGNALS):
        return "procedure"

    return None


def _apply_complaint_subtype_bias(candidates: list[dict[str, Any]], complaint_subtype: str | None) -> list[dict[str, Any]]:
    if not candidates or complaint_subtype is None:
        return candidates

    subtype_targets = {
        "procedure": ("complaint_40_provider_misconduct", 5.0),
        "service_procedure": ("complaint_29_inspection", 4.0),
        "ethics": ("complaint_40_provider_misconduct", 5.0),
        "contact": ("complaint_2_official_complaint_channels", 4.0),
        "dispute": ("complaint_unexpected_payment_dispute_v2", 4.0),
    }
    target = subtype_targets.get(complaint_subtype)
    if target is None:
        return candidates

    target_id, boost = target
    adjusted = []
    changed = False
    for candidate in candidates:
        updated = dict(candidate)
        if candidate["card"].get("id") == target_id:
            updated["score"] = round(candidate["score"] + boost, 4)
            changed = True
        adjusted.append(updated)

    if not changed:
        return candidates

    adjusted.sort(key=lambda item: item["score"], reverse=True)
    return adjusted


def _build_ambiguous_complaint_procedure_response() -> dict[str, Any]:
    follow_up_question = "Խոսքը բուժաշխատողի վարքագծի՞, թե հիվանդանոցի ծառայության կամ կազմակերպման մասին է։"
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": f"Բողոքի ընթացակարգը կախված է բողոքի տեսակից։ {follow_up_question}",
        "follow_up_question": follow_up_question,
        "matched_card_id": None,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _infer_worker_benefit_scope(user_text: str) -> str | None:
    normalized = normalize_text(user_text)

    if any(term in normalized for term in ("դեղորայք", "դեղ", "medicine")):
        return "medicine"

    if any(term in normalized for term in ("հետազոտություն", "վերլուծություն", "mri", "ct", "diagnostic")):
        return "diagnostic"

    if any(term in normalized for term in ("բուժօգնություն", "բուժում", "treatment")):
        return "treatment"

    return None


def _has_child_status_signal(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    return any(term in normalized for term in ("երեխա", "երեխայի", "մինչև 18", "մինչեւ 18", "անչափահաս"))


def _infer_child_benefit_scope(user_text: str) -> str | None:
    normalized = normalize_text(user_text)

    if any(term in normalized for term in ("հետազոտ", "վերլուծ", "ախտորոշ", "diagnostic")):
        return "diagnostic"

    if any(term in normalized for term in ("դեղ", "դեղորայք", "medicine")):
        return "medicine"

    if "հիվանդանոց" in normalized:
        return "treatment"

    if "բուժում" in normalized:
        return "treatment"

    if any(term in normalized for term in ("ինչ է ծածկվում", "ինչ ծածկույթ", "բժշկական օգնություն", "անվճար բուժօգնություն", "ինչ իրավունք")):
        return "general_coverage"

    return None


def _seed_inferable_required_fields(card: dict | None, user_text: str, collected_fields: dict[str, Any]) -> dict[str, Any]:
    if not card:
        return collected_fields

    seeded = dict(collected_fields)

    if card.get("id") == "service_referral_status_root_v1":
        required_fields = card.get("required_fields", [])
        for field_name in required_fields:
            if seeded.get(field_name) not in (None, ""):
                continue
            matched_value = _match_field_values_from_card(field_name, user_text, card)
            if matched_value is not None:
                seeded[field_name] = matched_value

    if card.get("id") == "eligibility_status_coverage_root_v1":
        if seeded.get("status_group") in (None, ""):
            matched_status = _match_field_values_from_card("status_group", user_text, card)
            if matched_status == "worker_insured":
                seeded["status_group"] = matched_status
            elif matched_status == "child" or _has_child_status_signal(user_text):
                seeded["status_group"] = "child"

        if seeded.get("status_group") == "worker_insured" and seeded.get("benefit_scope") in (None, ""):
            matched_scope = _infer_worker_benefit_scope(user_text)
            if matched_scope is not None:
                seeded["benefit_scope"] = matched_scope

        if seeded.get("status_group") == "child" and seeded.get("benefit_scope") in (None, ""):
            matched_scope = _infer_child_benefit_scope(user_text)
            if matched_scope is not None:
                seeded["benefit_scope"] = matched_scope

    return seeded


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
        complaint_subtype = _infer_complaint_subtype(request.message)
        if complaint_subtype == "procedure":
            response = _build_ambiguous_complaint_procedure_response()
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
        candidates = _apply_complaint_subtype_bias(candidates, complaint_subtype)

    top_card = candidates[0]["card"] if candidates else None
    collected_fields = _seed_inferable_required_fields(top_card, request.message, collected_fields)

    decision = decide(
        user_text=request.message,
        candidates=candidates,
        collected_fields=collected_fields,
    )

    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
        user_text=request.message,
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

@app.post("/chat-v2")
def chat_v2(request: ChatRequest):
    response = run_controller_v2(
        message=request.message,
        state=request.state or {},
    )

    append_request_log({
        "message": request.message,
        "v2": True,
        "action": response.get("action"),
        "matched_family": response.get("matched_family"),
        "follow_up_question": response.get("follow_up_question"),
        "state": response.get("state"),
        "cited_sources": response.get("cited_sources"),
    })

    return response

