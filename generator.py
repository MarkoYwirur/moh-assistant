from semantic_generator import build_semantic_payload
from style_renderer import render_style


def build_response(decision: dict, collected_fields: dict | None = None, user_text: str = "") -> dict:
    payload = build_semantic_payload(decision, collected_fields, user_text=user_text)
    semantic = payload["semantic"]

    answer = render_style(semantic)

    response = {
        "status": payload["status"],
        "action": payload["action"],
        "answer": answer,
        "follow_up_question": semantic.get("follow_up_question") or None,
        "matched_card_id": payload["matched_card_id"],
        "escalation_reason": payload["escalation_reason"],
        "state": payload["state"],
    }

    return response
