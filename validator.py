def _clean_spaces(text: str) -> str:
    return " ".join(text.split()).strip()


def validate_response(response: dict) -> dict:
    if "action" not in response:
        response["action"] = "escalate_true_gap"

    if "answer" not in response or not str(response["answer"]).strip():
        response["answer"] = "Հիմա հստակ պատասխան տալ հնարավոր չէ։ Նշեք՝ կոնկրետ ինչ հարցի մասին է խոսքը։"
        response["action"] = "escalate_true_gap"
        response["escalation_reason"] = "empty_answer"

    if response["action"].startswith("escalate") and not response.get("escalation_reason"):
        response["escalation_reason"] = "missing_reason"

    response["answer"] = _clean_spaces(str(response["answer"]))

    state = response.get("state")
    if not isinstance(state, dict):
        response["state"] = {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        }

    collected_fields = response["state"].get("collected_fields")
    if not isinstance(collected_fields, dict):
        response["state"]["collected_fields"] = {}

    return response
