def _matches_when_clause(when_clause: dict, collected_fields: dict) -> bool:
    for field_name, expected_value in when_clause.items():
        actual_value = collected_fields.get(field_name)

        if expected_value == "__any__":
            if actual_value is None:
                return False
            if isinstance(actual_value, str) and not actual_value.strip():
                return False
            continue

        if isinstance(expected_value, list):
            if actual_value not in expected_value:
                return False
        else:
            if actual_value != expected_value:
                return False

    return True


def _select_rule_payload(card: dict, collected_fields: dict) -> dict | None:
    answer_rules = card.get("answer_rules", [])
    if not isinstance(answer_rules, list):
        return None

    for rule in answer_rules:
        if not isinstance(rule, dict):
            continue

        when_clause = rule.get("when", {})
        if not isinstance(when_clause, dict):
            continue

        if _matches_when_clause(when_clause, collected_fields):
            return rule

    return None


def _get_field_question(card: dict, field_name: str) -> str:
    field_questions = card.get("field_questions", {})
    if isinstance(field_questions, dict):
        question = field_questions.get(field_name)
        if isinstance(question, str) and question.strip():
            return question.strip()

    fallback = {
        "referral_status": "Ուղեգիր ունե՞ք։",
        "medicine_name_details": "Նշեք դեղի ճշգրիտ անվանումը, դեղաչափը և ձևը։",
        "service_context": "Նշեք՝ որ ծառայության համար և որտեղ են գումար պահանջել։",
        "refusal_context": "Նշեք՝ ինչ ծառայություն են մերժել կամ ինչու չեն սպասարկել։",
        "routing_need_type": "Նշեք՝ խոսքը մասնագետի, հետազոտության, թե ընդհանուր բուժօգնության մասին է։"
    }

    return fallback.get(field_name, "Նշեք՝ կոնկրետ ինչ հարցի մասին է խոսքը։")


def build_semantic_payload(decision: dict, collected_fields: dict | None = None) -> dict:
    if collected_fields is None:
        collected_fields = {}

    action = decision.get("action")
    card = decision.get("card")
    reason = decision.get("reason")
    missing_fields = decision.get("missing_fields", [])

    payload = {
        "status": "ok",
        "action": action,
        "matched_card_id": card.get("id") if card else None,
        "escalation_reason": reason,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": collected_fields,
        },
        "semantic": {
            "answer_type": action,
            "category": card.get("category") if card else "escalation",
            "policy_answer": "",
            "condition_note": "",
            "partial_answer": "",
            "next_step": "",
            "follow_up_question": "",
            "gap_reason_text": "",
            "safety_text": ""
        }
    }

    if action == "direct_answer" and card:
        rule_payload = _select_rule_payload(card, collected_fields)
        if rule_payload:
            payload["semantic"]["policy_answer"] = rule_payload.get("answer", "")
            payload["semantic"]["next_step"] = rule_payload.get("next_step", "")
        else:
            payload["semantic"]["policy_answer"] = card.get("approved_answer", "")
            payload["semantic"]["next_step"] = card.get("next_step", "")
        return payload

    if action == "clarify" and card:
        missing_field = missing_fields[0] if missing_fields else None
        question = _get_field_question(card, missing_field)
        payload["semantic"]["follow_up_question"] = question
        payload["state"] = {
            "pending_card_id": card.get("id"),
            "pending_field": missing_field,
            "collected_fields": collected_fields,
        }
        return payload

    if action == "partial_answer_with_clarify" and card:
        missing_field = missing_fields[0] if missing_fields else None
        question = _get_field_question(card, missing_field)
        payload["semantic"]["partial_answer"] = card.get("safe_partial_answer", "")
        payload["semantic"]["follow_up_question"] = question
        payload["state"] = {
            "pending_card_id": card.get("id"),
            "pending_field": missing_field,
            "collected_fields": collected_fields,
        }
        return payload

    if action == "partial_answer_with_next_step" and card:
        payload["semantic"]["partial_answer"] = card.get("safe_partial_answer", "")
        payload["semantic"]["next_step"] = card.get("next_step_if_missing", "") or card.get("next_step", "")
        return payload

    if action == "escalate_safety":
        payload["semantic"]["category"] = "safety"
        payload["semantic"]["safety_text"] = "Ես բժշկական խորհրդատվություն չեմ տալիս"
        payload["semantic"]["next_step"] = "Եթե վիճակը շտապ է, զանգահարեք 103 կամ 112"
        return payload

    payload["semantic"]["category"] = "escalation"
    payload["semantic"]["gap_reason_text"] = "Այս հարցով հիմա հստակ պատասխան տալ հնարավոր չէ"
    payload["semantic"]["next_step"] = "Նշեք՝ կոնկրետ որ ծառայության, դեղի կամ խնդրի մասին է խոսքը"
    return payload
