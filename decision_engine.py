from enum import Enum
from collections import Counter
from router import normalize_text


class Action(str, Enum):
    DIRECT_ANSWER = "direct_answer"
    CLARIFY = "clarify"
    PARTIAL_ANSWER_WITH_CLARIFY = "partial_answer_with_clarify"
    PARTIAL_ANSWER_WITH_NEXT_STEP = "partial_answer_with_next_step"
    ESCALATE_TRUE_GAP = "escalate_true_gap"
    ESCALATE_SAFETY = "escalate_safety"


DIRECT_ANSWER_THRESHOLD = 3.0
DOMAIN_THRESHOLD = 1.2
PARTIAL_THRESHOLD = 0.8

SAFETY_PATTERNS = [
    "ջերմություն",
    "ցավ",
    "կոկորդ",
    "շնչ",
    "արյուն",
    "հղի",
    "հղիություն",
    "ախտանիշ",
    "ինչ դեղ",
    "ինչ խմեմ",
    "ինչ անեմ",
    "բուժում",
    "դեղաչափ",
    "խմել",
    "օգնեք ինձ",
    "սիրտ",
    "գլուխս",
    "որ բժիշկ",
    "103",
    "շտապ",
    "emergency",
    "symptom",
    "treatment",
    "dose",
    "dosage",
    "pain",
    "fever",
]

REFERRAL_LOGISTICS_OWNER_IDS = {
    "routing_specialist_referral_confusion_v1",
    "routing_referral_where_to_go_v2",
    "service_referral_status_root_v1",
}

REFERRAL_LOGISTICS_SIGNALS = (
    "ուղեգ",
    "մասնագետ",
    "սրտաբան",
    "նյարդաբան",
    "ակնաբույժ",
    "ընտանեկան բժիշկ",
    "պոլիկլինիկա",
    "ուր գնամ",
    "որտեղից վերցնեմ",
    "ով պետք է տա",
    "ում դիմեմ",
    "ուղղորդ",
)

REFERRAL_LOGISTICS_OPEN_ENDED_SIGNALS = (
    "ինչ անեմ",
)

MEDICAL_RISK_SIGNALS_ARMENIAN = (
    "ջերմ",
    "ցավ",
    "կոկորդ",
    "շնչ",
    "արյուն",
    "հղի",
    "հղիություն",
    "ախտանիշ",
    "ինչ դեղ",
    "ինչ խմեմ",
    "բուժում",
    "դեղաչափ",
    "օգնեք ինձ",
    "սիրտ",
    "գլուխս",
    "շտապ",
    "103",
)

ADMISSION_LOGISTICS_SIGNALS = (
    "հոսպիտալ",
    "հիվանդանոց ընդուն",
    "ստացիոնար",
    "պառկ",
    "վիրահատ",
    "ընդունում",
    "ընդունվ",
    "անհետաձգելի",
    "պլանային",
)

ADMISSION_MEDICAL_ADVICE_DISQUALIFIERS = (
    "ցավ",
    "արյուն",
    "ինչ դեղ",
    "ինչ խմեմ",
    "ախտանիշ",
    "103",
    "ջերմ",
    "շնչ",
    "շտապ օգնություն",
    "օգնեք ինձ",
)

ELIGIBILITY_COVERAGE_SIGNALS = (
    "անվճար",
    "ծածկ",
    "ինչ է հասնում",
    "իրավունք",
    "պետպատվ",
    "արտոնյալ",
)

ELIGIBILITY_MEDICAL_ADVICE_DISQUALIFIERS = (
    "ինչ դեղ",
    "ինչ խմեմ",
    "ինչ անեմ",
    "դեղաչափ",
    "ախտանիշ",
    "ջերմ",
    "ցավ",
    "շնչ",
    "արյուն",
    "շտապ",
    "103",
    "օգնեք ինձ",
    "որ բժիշկ",
)


def _is_child_eligibility_safety_override(user_text: str, candidates: list) -> bool:
    text = normalize_text(user_text)
    if not text or not candidates:
        return False

    top_card_id = candidates[0]["card"].get("id")
    if top_card_id != "eligibility_status_coverage_root_v1":
        return False

    has_child_signal = any(term in text for term in ("երեխա", "երեխայի", "մինչև 18", "մինչեւ 18", "անչափահաս"))
    has_eligibility_anchor = any(
        term in text
        for term in ("անվճար", "ծածկ", "բժշկական օգնություն", "բուժօգնություն", "հիվանդանոց", "իրավունք")
    )
    has_medical_advice_signal = any(
        term in text
        for term in ("ինչ դեղ", "ինչ խմեմ", "ինչ անեմ", "դեղաչափ", "ախտանիշ", "ջերմություն", "ցավ", "շնչ", "արյուն")
    )

    return has_child_signal and has_eligibility_anchor and not has_medical_advice_signal


def _is_admission_coverage_safety_override(user_text: str, candidates: list) -> bool:
    text = normalize_text(user_text)
    if not text or not candidates:
        return False

    top_card_id = candidates[0]["card"].get("id")
    if top_card_id != "service_admission_type_root_v1":
        return False

    has_admission_anchor = any(
        term in text
        for term in ("հոսպիտալ", "հիվանդանոց", "ստացիոնար", "վիրահատ", "operation", "surgery")
    )
    # normalize_text can split Armenian punctuation variants, so match the stable stem.
    has_coverage_anchor = any(term in text for term in ("անվճա", "ծածկ"))
    has_medical_advice_signal = any(
        term in text
        for term in ("ինչ դեղ", "ինչ խմեմ", "ինչ անեմ", "դեղաչափ", "ախտանիշ", "ջերմություն", "ցավ", "շնչ", "արյուն")
    )

    return has_admission_anchor and has_coverage_anchor and not has_medical_advice_signal


def _is_admission_logistics_safety_override(user_text: str, candidates: list) -> bool:
    text = normalize_text(user_text)
    if not text or not candidates:
        return False

    top_card_id = candidates[0]["card"].get("id")
    if top_card_id != "service_admission_type_root_v1":
        return False

    has_admission_signal = any(term in text for term in ADMISSION_LOGISTICS_SIGNALS)
    has_medical_advice_signal = any(term in text for term in ADMISSION_MEDICAL_ADVICE_DISQUALIFIERS)

    return has_admission_signal and not has_medical_advice_signal


def _is_referral_logistics_safety_override(user_text: str, candidates: list) -> bool:
    text = normalize_text(user_text)
    if not text or not candidates:
        return False

    if not any(term in text for term in REFERRAL_LOGISTICS_OPEN_ENDED_SIGNALS):
        return False

    top_card_id = candidates[0]["card"].get("id")
    if top_card_id not in REFERRAL_LOGISTICS_OWNER_IDS:
        return False

    has_logistics_signal = any(term in text for term in REFERRAL_LOGISTICS_SIGNALS)
    has_medical_risk_signal = any(term in text for term in MEDICAL_RISK_SIGNALS_ARMENIAN)

    return has_logistics_signal and not has_medical_risk_signal


def _is_general_eligibility_safety_override(user_text: str, candidates: list) -> bool:
    text = normalize_text(user_text)
    if not text or not candidates:
        return False

    top_card_id = candidates[0]["card"].get("id")
    if top_card_id != "eligibility_status_coverage_root_v1":
        return False

    has_coverage_signal = any(term in text for term in ELIGIBILITY_COVERAGE_SIGNALS)
    has_medical_advice_signal = any(term in text for term in ELIGIBILITY_MEDICAL_ADVICE_DISQUALIFIERS)

    return has_coverage_signal and not has_medical_advice_signal


def is_safety_case(user_text: str) -> bool:
    text = normalize_text(user_text)
    if not text:
        return False
    for pattern in SAFETY_PATTERNS:
        if pattern in text:
            return True
    return False


def infer_domain(candidates: list) -> str | None:
    if not candidates:
        return None

    category_scores = Counter()
    for candidate in candidates[:5]:
        category = candidate["card"].get("category", "unknown")
        category_scores[category] += candidate["score"]

    if not category_scores:
        return None

    best_category, best_score = category_scores.most_common(1)[0]
    if best_score >= DOMAIN_THRESHOLD:
        return best_category

    return None


def all_required_fields_present(card: dict, collected_fields: dict) -> bool:
    required_fields = card.get("required_fields", [])
    if not required_fields:
        return True

    for field_name in required_fields:
        if field_name not in collected_fields:
            return False
        value = collected_fields.get(field_name)
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False

    return True


def get_missing_fields(card: dict, collected_fields: dict) -> list:
    missing = []
    for field_name in card.get("required_fields", []):
        if field_name not in collected_fields:
            missing.append(field_name)
            continue
        value = collected_fields.get(field_name)
        if value is None:
            missing.append(field_name)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field_name)
    return missing


def get_best_answerable_card(candidates: list, collected_fields: dict) -> dict | None:
    if not candidates:
        return None

    best_candidate = candidates[0]
    best_card = best_candidate["card"]
    best_score = best_candidate["score"]

    if best_score < DIRECT_ANSWER_THRESHOLD:
        return None

    if not all_required_fields_present(best_card, collected_fields):
        return None

    return {"card": best_card, "score": best_score}


def get_best_clarifiable_card(candidates: list, collected_fields: dict) -> dict | None:
    for candidate in candidates:
        card = candidate["card"]
        score = candidate["score"]
        if score < DOMAIN_THRESHOLD:
            continue

        missing_fields = get_missing_fields(card, collected_fields)
        if not missing_fields:
            continue

        clarifiable = card.get("clarifiable")
        if clarifiable is None:
            clarifiable = True

        if clarifiable:
            return {"card": card, "score": score, "missing_fields": missing_fields}

    return None


def get_best_partial_card(candidates: list) -> dict | None:
    if not candidates:
        return None

    best_candidate = candidates[0]
    if best_candidate["score"] < PARTIAL_THRESHOLD:
        return None

    card = best_candidate["card"]

    if card.get("safe_partial_answer") or card.get("next_step_if_missing") or card.get("approved_answer"):
        return {"card": card, "score": best_candidate["score"]}

    return None


def decide(user_text: str, candidates: list, collected_fields: dict | None = None) -> dict:
    if collected_fields is None:
        collected_fields = {}

    if is_safety_case(user_text) and not (
        _is_referral_logistics_safety_override(user_text, candidates)
        or
        _is_general_eligibility_safety_override(user_text, candidates)
        or
        _is_child_eligibility_safety_override(user_text, candidates)
        or _is_admission_logistics_safety_override(user_text, candidates)
        or _is_admission_coverage_safety_override(user_text, candidates)
    ):
        return {
            "action": Action.ESCALATE_SAFETY.value,
            "reason": "safety_medical",
            "domain": None,
            "card": None,
            "missing_fields": [],
            "candidates": candidates,
        }

    domain = infer_domain(candidates)

    if not candidates or domain is None:
        return {
            "action": Action.ESCALATE_TRUE_GAP.value,
            "reason": "fatal_ambiguity",
            "domain": None,
            "card": None,
            "missing_fields": [],
            "candidates": candidates,
        }

    answerable = get_best_answerable_card(candidates, collected_fields)
    if answerable:
        return {
            "action": Action.DIRECT_ANSWER.value,
            "reason": None,
            "domain": domain,
            "card": answerable["card"],
            "missing_fields": [],
            "candidates": candidates,
        }

    clarifiable = get_best_clarifiable_card(candidates, collected_fields)
    if clarifiable:
        card = clarifiable["card"]
        missing_fields = clarifiable["missing_fields"]

        if card.get("partial_answer_allowed", True):
            return {
                "action": Action.PARTIAL_ANSWER_WITH_CLARIFY.value,
                "reason": None,
                "domain": domain,
                "card": card,
                "missing_fields": missing_fields,
                "candidates": candidates,
            }

        return {
            "action": Action.CLARIFY.value,
            "reason": None,
            "domain": domain,
            "card": card,
            "missing_fields": missing_fields,
            "candidates": candidates,
        }

    partial = get_best_partial_card(candidates)
    if partial:
        return {
            "action": Action.PARTIAL_ANSWER_WITH_NEXT_STEP.value,
            "reason": None,
            "domain": domain,
            "card": partial["card"],
            "missing_fields": [],
            "candidates": candidates,
        }

    return {
        "action": Action.ESCALATE_TRUE_GAP.value,
        "reason": "true_kb_gap",
        "domain": domain,
        "card": None,
        "missing_fields": [],
        "candidates": candidates,
    }
