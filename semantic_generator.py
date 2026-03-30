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


def _get_missing_fields(card: dict, collected_fields: dict) -> list[str]:
    required_fields = card.get("required_fields", [])
    missing = []

    for field in required_fields:
        value = collected_fields.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)

    return missing


def _get_field_question(card: dict, field_name: str) -> str:
    field_questions = card.get("field_questions", {})
    if isinstance(field_questions, dict):
        question = field_questions.get(field_name)
        if isinstance(question, str) and question.strip():
            return question.strip()

    return "Կնշե՞ք ավելի կոնկրետ տվյալներ։"


def _get_field_why(field_name: str) -> str:
    explanations = {
        "referral_status": "Սա կարևոր է, որովհետև ծառայության կազմակերպման կարգը հաճախ կախված է ուղեգրի առկայությունից։",
        "medicine_name_details": "Սա պետք է հստակեցնել, որովհետև վերջնական պատասխանը կախված է դեղի ճշգրիտ անվանումից, դեղաչափից և ձևից։",
        "dispense_location": "Սա կարևոր է, որովհետև պետք է հասկանալ՝ որ օղակում է առաջացել խնդիրը։",
        "service_context": "Սա պետք է հստակեցնել, որովհետև առանց ծառայության տեսակի և վայրի ճիշտ ուղղորդում հնարավոր չէ տալ։",
        "refusal_context": "Սա կարևոր է, որովհետև պետք է հասկանալ՝ ինչն է մերժվել և ինչ հաջորդ քայլ է պետք առաջարկել։",
        "routing_need_type": "Սա պետք է հստակեցնել, որովհետև տարբեր ծառայությունների դեպքում տարբեր ուղղորդում է գործում։",
        "record_issue_type": "Սա կարևոր է, որովհետև բացակա և սխալ տվյալների դեպքում գործողությունները տարբեր են։",
        "record_context": "Սա պետք է հասկանալ, որպեսզի հստակ լինի՝ ինչ տվյալ է խնդրահարույց։",
        "armed_item_type": "Սա կարևոր է, որովհետև տարբեր տվյալների դեպքում տարբեր պատասխանատու օղակներ կարող են լինել։",
        "armed_issue_context": "Սա պետք է հստակեցնել, որպեսզի հասկանալի լինի՝ որտեղ է առաջացել խափանումը կամ չերևալու խնդիրը։",
        "payment_issue_type": "Սա կարևոր է, որովհետև կրկնակի գանձման և սխալ կարգավիճակի դեպքում հետագա քայլերը տարբեր են։",
        "payment_context": "Սա պետք է հասկանալ, որպեսզի հնարավոր լինի ուղղորդել ճիշտ հաստատություն կամ գործողություն։",
        "specialist_type_or_purpose": "Սա կարևոր է, որովհետև նեղ մասնագետի դեպքում ճիշտ ուղղորդումը կախված է դիմելու նպատակից։"
    }
    return explanations.get(field_name, "Սա պետք է հստակեցնել, որպեսզի հնարավոր լինի ճիշտ պատասխան տալ։")


def build_semantic_payload(decision: dict, collected_fields: dict | None = None) -> dict:
    if collected_fields is None:
        collected_fields = {}

    action = decision.get("action")
    card = decision.get("card")
    reason = decision.get("reason")

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
            "partial_answer": "",
            "next_step": "",
            "follow_up_question": "",
            "why_this_question": "",
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

    if action in {"clarify", "partial_answer_with_clarify"} and card:
        missing_fields = _get_missing_fields(card, collected_fields)
        missing_field = missing_fields[0] if missing_fields else None

        payload["semantic"]["partial_answer"] = card.get("safe_partial_answer", "")
        payload["semantic"]["follow_up_question"] = _get_field_question(card, missing_field) if missing_field else "Կնշե՞ք ավելի կոնկրետ տվյալներ։"
        payload["semantic"]["why_this_question"] = _get_field_why(missing_field) if missing_field else "Սա պետք է հստակեցնել, որպեսզի ճիշտ ուղղորդում հնարավոր լինի տալ։"

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
    payload["semantic"]["next_step"] = "Կնշե՞ք ավելի կոնկրետ տվյալներ"
    return payload
