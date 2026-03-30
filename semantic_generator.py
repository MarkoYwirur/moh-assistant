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
    if not isinstance(required_fields, list):
        return []

    missing = []
    for field in required_fields:
        value = collected_fields.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)

    return missing


def _get_field_question(card: dict, field_name: str) -> str:
    field_questions = card.get("field_questions", {})
    if isinstance(field_questions, dict):
        question = field_questions.get(field_name)
        if isinstance(question, str) and question.strip():
            return question.strip()

    fallback = {
        "referral_status": "Ուղեգիր ունե՞ք։",
        "medicine_name_details": "Նշե՛ք դեղի ճշգրիտ անվանումը, դեղաչափը և ձևը։",
        "dispense_location": "Նշե՛ք՝ որտեղ չեն տրամադրել դեղը։",
        "service_context": "Նշե՛ք՝ որ ծառայության համար և որտեղ են գումար պահանջել։",
        "refusal_context": "Նշե՛ք՝ ինչ ծառայություն են մերժել կամ ինչու չեն սպասարկել։",
        "routing_need_type": "Նշե՛ք՝ խոսքը մասնագետի, հետազոտության, թե ընդհանուր բուժօգնության մասին է։",
        "record_issue_type": "Նշե՛ք՝ տվյալը բացակայում է, թե սխալ է երևում։",
        "record_context": "Նշե՛ք՝ կոնկրետ ինչ գրառման կամ տվյալների մասին է խոսքը։",
        "armed_item_type": "Նշե՛ք՝ ինչ տվյալ պետք է երևար ArMed-ում։",
        "armed_issue_context": "Նշե՛ք՝ որտեղ և երբ եք նկատել խնդիրը։",
        "payment_issue_type": "Նշե՛ք՝ խոսքը կրկնակի գանձման, թե սխալ կարգավիճակի մասին է։",
        "payment_context": "Նշե՛ք՝ որ ծառայության կամ վճարման մասին է խոսքը և որտեղ եք նկատել խնդիրը։",
        "specialist_type_or_purpose": "Նշե՛ք՝ որ մասնագետի մոտ եք ցանկանում դիմել կամ ինչ հարցով է անհրաժեշտ ուղղորդումը։"
    }

    return fallback.get(field_name, "Նշե՛ք՝ կոնկրետ ինչ հարցի մասին է խոսքը։")


def _get_field_why(field_name: str) -> str:
    explanations = {
        "referral_status": "Սա պետք է հասկանալ, որովհետև ծառայության կազմակերպման կարգը հաճախ կախված է ուղեգրի առկայությունից։",
        "medicine_name_details": "Սա պետք է հստակեցնել, որովհետև դեղի ծածկույթը որոշվում է ճշգրիտ անվանումով, դեղաչափով և ձևով։",
        "dispense_location": "Սա կարևոր է, որովհետև պետք է հասկանալ՝ խնդիրը տրամադրման վայրի, կազմակերպման, թե ծածկույթի հետ է կապված։",
        "service_context": "Սա կարևոր է, որովհետև առանց ծառայության տեսակի և վայրի հնարավոր չէ հասկանալ՝ խոսքը վճարի, կազմակերպման, թե իրավունքի հարցի մասին է։",
        "refusal_context": "Սա պետք է հստակեցնել, որպեսզի հասկանալի լինի՝ ինչ է մերժվել և ինչ ուղի պետք է առաջարկել հաջորդ քայլի համար։",
        "routing_need_type": "Սա կարևոր է, որովհետև ճիշտ ուղղորդումը կախված է նրանից, թե ինչ ծառայության համար եք ուզում դիմել։",
        "record_issue_type": "Սա պետք է հասկանալ, որովհետև բացակա գրառման և սխալ տվյալների դեպքում գործողությունները տարբեր են։",
        "record_context": "Սա կարևոր է, որովհետև պետք է հստակ հասկանալ՝ կոնկրետ որ տվյալն է խնդրահարույց։",
        "armed_item_type": "Սա պետք է հստակեցնել, որովհետև տարբեր տվյալների դեպքում տարբեր հաստատություններ են պատասխանատու։",
        "armed_issue_context": "Սա կարևոր է, որովհետև պետք է հասկանալ՝ որտեղ է առաջացել խափանումը կամ փոխանցման խնդիրը։",
        "payment_issue_type": "Սա պետք է հասկանալ, որովհետև կրկնակի գանձման և սխալ կարգավիճակի դեպքում հաջորդ քայլերը տարբեր են։",
        "payment_context": "Սա կարևոր է, որովհետև առանց ծառայության կամ վճարման կոնկրետ տվյալների ճիշտ ուղղորդում հնարավոր չէ տալ։",
        "specialist_type_or_purpose": "Սա պետք է հստակեցնել, որովհետև նեղ մասնագետի դեպքում ուղեգրի անհրաժեշտությունը կախված է ծառայության նպատակից։"
    }

    return explanations.get(field_name, "Սա պետք է հստակեցնել, որպեսզի հնարավոր լինի ճիշտ ուղղորդում տալ։")


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
            "condition_note": "",
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

        question = _get_field_question(card, missing_field) if missing_field else "Կնշե՞ք ավելի կոնկրետ տվյալներ։"
        why_text = _get_field_why(missing_field) if missing_field else "Սա պետք է հստակեցնել, որպեսզի ճիշտ պատասխան հնարավոր լինի ձևակերպել։"

        if action == "partial_answer_with_clarify":
            payload["semantic"]["partial_answer"] = card.get("safe_partial_answer", "")
        payload["semantic"]["follow_up_question"] = question
        payload["semantic"]["why_this_question"] = why_text

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
    payload["semantic"]["next_step"] = "Նշե՛ք՝ կոնկրետ որ ծառայության, դեղի կամ խնդրի մասին է խոսքը"
    return payload
