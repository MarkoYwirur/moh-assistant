from typing import Any, Dict

from app.answer_composer import compose_answer
from app.issue_family_classifier import classify_issue_family
from app.workflow_engine import get_workflow_by_family


def _get_missing_fields(workflow: Dict[str, Any], collected_fields: Dict[str, Any]) -> list[str]:
    required = workflow.get("required_fields", []) or []
    missing = []

    for field in required:
        value = collected_fields.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)

    return missing


def _match_branch(branch_when: Dict[str, Any], collected_fields: Dict[str, Any]) -> bool:
    for key, expected in branch_when.items():
        actual = collected_fields.get(key)

        if expected == "__any__":
            if actual is None:
                return False
            if isinstance(actual, str) and not actual.strip():
                return False
            continue

        if actual != expected:
            return False

    return True


def _resolve_branch(workflow: Dict[str, Any], collected_fields: Dict[str, Any]) -> Dict[str, Any] | None:
    branches = workflow.get("branches", []) or []
    for branch in branches:
        when = branch.get("when", {}) or {}
        if _match_branch(when, collected_fields):
            return branch
    return None


def _coerce_field_value(field_name: str, message: str) -> str:
    text = (message or "").lower().strip()

    if field_name == "need_type":
        if any(x in text for x in [
            "մասնագետ", "նեղ մասնագետ", "սրտաբան", "նյարդաբան", "ակնաբույժ",
            "գինեկոլոգ", "ուռոլոգ", "էնդոկրինոլոգ", "օրթոպեդ", "վիրաբույժ",
            "specialist"
        ]):
            return "specialist"

        if any(x in text for x in [
            "հետազոտ", "մռտ", "կտ", "անալիզ", "diagnostic", "mri", "ct"
        ]):
            return "diagnostic"

        if any(x in text for x in [
            "ընդհանուր", "բուժօգն", "պոլիկլինիկա", "ընտանեկան բժիշկ", "general"
        ]):
            return "general"

    if field_name == "person_group":
        if "65" in text:
            return "elderly_65_plus"
        if "թոշակառու" in text:
            return "pensioner"
        if "հաշմանդամ" in text:
            return "disability"
        if "հղի" in text:
            return "pregnancy"
        if "երեխա" in text:
            return "child"
        if "սոցիալապես անապահով" in text:
            return "social_vulnerability"
        if "աշխատող" in text or "ապահովագրված" in text:
            return "worker_insured"

    if field_name == "service_type":
        if "մռտ" in text:
            return "mri"
        if "կտ" in text:
            return "ct"
        if "հոսպիտալ" in text:
            return "hospitalization"
        if "լաբորատոր" in text or "անալիզ" in text:
            return "lab"
        if "մասնագետ" in text or "սրտաբան" in text or "նյարդաբան" in text:
            return "specialist"
        if "վիրահատ" in text:
            return "surgery"

    return message.strip()


def _extract_specialist_or_service(message: str) -> str | None:
    text = (message or "").lower().strip()
    exact_terms = [
        "սրտաբան", "նյարդաբան", "ակնաբույժ", "գինեկոլոգ", "ուռոլոգ",
        "էնդոկրինոլոգ", "օրթոպեդ", "վիրաբույժ", "մռտ", "կտ", "անալիզ",
    ]
    for term in exact_terms:
        if term in text:
            return term
    return None


def _extract_payment_fields(message: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = text.lower()
    out: Dict[str, Any] = {}
    service = None
    institution = None

    if "մռտ" in lowered:
        service = "ՄՌՏ"
    elif "կտ" in lowered:
        service = "ԿՏ"
    elif "անալիզ" in lowered:
        service = "անալիզ"
    elif "սրտաբան" in lowered:
        service = "սրտաբանի դիմում"
    elif "ծառայ" in lowered:
        service = "ծառայություն"

    if "պոլիկլինիկա" in lowered:
        institution = "պոլիկլինիկայում"
    elif "հիվանդանոց" in lowered:
        institution = "հիվանդանոցում"
    elif "կլինիկա" in lowered:
        institution = "կլինիկայում"
    elif "բուժհաստատ" in lowered:
        institution = "բուժհաստատությունում"

    if service:
        out["service_name_or_type"] = service
    if institution:
        out["institution_context"] = institution
    if "ուղեգիր" in lowered:
        out["has_referral_context"] = True
    return out


def _extract_record_fields(message: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = text.lower()
    out: Dict[str, Any] = {}

    if "արմեդ" in lowered or "armed" in lowered:
        out["issue_system"] = "armed"

    if "դեղատոմս" in lowered:
        out["issue_target"] = "դեղատոմս"
    elif "ուղեգիր" in lowered:
        out["issue_target"] = "ուղեգիր"
    elif "գրառում" in lowered:
        out["issue_target"] = "գրառում"
    elif "տվյալ" in lowered:
        out["issue_target"] = "տվյալ"

    if "դեղատուն" in lowered or "դեղատանը" in lowered:
        out["issue_place"] = "դեղատանը"
    elif "պոլիկլինիկա" in lowered:
        out["issue_place"] = "պոլիկլինիկայում"
    elif "հիվանդանոց" in lowered:
        out["issue_place"] = "հիվանդանոցում"

    return out


def _extract_medicine_fields(message: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = text.lower()
    out: Dict[str, Any] = {}
    medicine = None
    place = None

    if "աբիրատերոն" in lowered:
        medicine = "Աբիրատերոն"

    if "դեղատուն" in lowered or "դեղատանը" in lowered:
        place = "դեղատանը"
    elif "հիվանդանոց" in lowered:
        place = "հիվանդանոցում"
    elif "պոլիկլինիկա" in lowered:
        place = "պոլիկլինիկայում"

    if medicine:
        out["medicine_name_or_type"] = medicine
    if place:
        out["dispense_place"] = place
    if "դեղատոմս" in lowered or "դուրս է գրված" in lowered:
        out["has_prescription_context"] = True
    return out


def _extract_denied_service_fields(message: str) -> Dict[str, Any]:
    text = (message or "").strip()
    lowered = text.lower()
    out: Dict[str, Any] = {}
    service = None
    institution = None

    if "մռտ" in lowered:
        service = "ՄՌՏ"
    elif "կտ" in lowered:
        service = "ԿՏ"
    elif "սրտաբան" in lowered:
        service = "սրտաբանի ծառայություն"
    elif "վիրահատ" in lowered:
        service = "վիրահատություն"
    elif "ծառայ" in lowered:
        service = "ծառայություն"

    if "պոլիկլինիկա" in lowered:
        institution = "պոլիկլինիկայում"
    elif "հիվանդանոց" in lowered:
        institution = "հիվանդանոցում"
    elif "կլինիկա" in lowered:
        institution = "կլինիկայում"
    elif "բուժհաստատ" in lowered:
        institution = "բուժհաստատությունում"

    if service:
        out["service_name_or_type"] = service
    if institution:
        out["institution_context"] = institution
    return out


def _extract_eligibility_fields(message: str) -> Dict[str, Any]:
    text = (message or "").strip().lower()
    out: Dict[str, Any] = {}

    if "65" in text:
        out["person_group"] = "elderly_65_plus"
    elif "թոշակառու" in text:
        out["person_group"] = "pensioner"
    elif "հաշմանդամ" in text:
        out["person_group"] = "disability"
    elif "հղի" in text:
        out["person_group"] = "pregnancy"
    elif "երեխա" in text:
        out["person_group"] = "child"
    elif "սոցիալապես անապահով" in text:
        out["person_group"] = "social_vulnerability"
    elif "աշխատող" in text or "ապահովագրված" in text:
        out["person_group"] = "worker_insured"

    return out


def _extract_service_coverage_fields(message: str) -> Dict[str, Any]:
    text = (message or "").strip().lower()
    out: Dict[str, Any] = {}

    if "մռտ" in text:
        out["service_type"] = "mri"
    elif "կտ" in text:
        out["service_type"] = "ct"
    elif "հոսպիտալ" in text:
        out["service_type"] = "hospitalization"
    elif "լաբորատոր" in text or "անալիզ" in text:
        out["service_type"] = "lab"
    elif "մասնագետ" in text or "սրտաբան" in text or "նյարդաբան" in text:
        out["service_type"] = "specialist"
    elif "վիրահատ" in text:
        out["service_type"] = "surgery"

    return out


def _has_specific_payment_context(fields: Dict[str, Any]) -> bool:
    return bool(fields.get("service_name_or_type") or fields.get("institution_context"))


def _has_specific_medicine_context(fields: Dict[str, Any]) -> bool:
    return bool(fields.get("medicine_name_or_type"))


def _has_specific_denial_context(fields: Dict[str, Any]) -> bool:
    return bool(fields.get("service_name_or_type"))


def _infer_initial_fields(message: str, family: str) -> Dict[str, Any]:
    inferred: Dict[str, Any] = {}
    text = (message or "").strip().lower()

    if family == "referral_specialist":
        need_type = _coerce_field_value("need_type", message)
        if need_type in {"specialist", "diagnostic", "general"}:
            inferred["need_type"] = need_type

        detail = _extract_specialist_or_service(message)
        broad_referral_phrases = {
            "մասնագետի մոտ ուզում եմ գնալ",
            "մասնագետի մոտ ուզում եմ",
            "ուզում եմ գնալ մասնագետի մոտ",
        }
        if detail and text not in broad_referral_phrases:
            inferred["specialist_or_service"] = detail

    elif family == "payment_dispute":
        payment_fields = _extract_payment_fields(message)
        inferred.update(payment_fields)
        if _has_specific_payment_context(payment_fields):
            inferred["service_context"] = message.strip()

    elif family == "record_or_visibility_issue":
        inferred.update(_extract_record_fields(message))

    elif family == "medicine_not_provided":
        medicine_fields = _extract_medicine_fields(message)
        inferred.update(medicine_fields)
        if _has_specific_medicine_context(medicine_fields):
            inferred["medicine_context"] = message.strip()

    elif family == "denied_service":
        denied_fields = _extract_denied_service_fields(message)
        inferred.update(denied_fields)
        if _has_specific_denial_context(denied_fields):
            inferred["denial_context"] = message.strip()

    elif family == "eligibility_check":
        inferred.update(_extract_eligibility_fields(message))

    elif family == "service_coverage_check":
        inferred.update(_extract_service_coverage_fields(message))

    return inferred


def run_controller_v2(message: str, state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state = state or {}
    collected_fields = dict(state.get("collected_fields", {}) or {})
    pending_field = state.get("pending_field")
    existing_family = state.get("family")

    if existing_family and pending_field:
        coerced_value = _coerce_field_value(pending_field, message)
        if coerced_value:
            collected_fields[pending_field] = coerced_value
        else:
            collected_fields[pending_field] = message.strip()

        family = existing_family

        if family == "payment_dispute":
            for k, v in _extract_payment_fields(message).items():
                if k not in collected_fields:
                    collected_fields[k] = v
        elif family == "record_or_visibility_issue":
            for k, v in _extract_record_fields(message).items():
                if k not in collected_fields:
                    collected_fields[k] = v
        elif family == "medicine_not_provided":
            for k, v in _extract_medicine_fields(message).items():
                if k not in collected_fields:
                    collected_fields[k] = v
        elif family == "denied_service":
            for k, v in _extract_denied_service_fields(message).items():
                if k not in collected_fields:
                    collected_fields[k] = v
        elif family == "eligibility_check":
            for k, v in _extract_eligibility_fields(message).items():
                if k not in collected_fields:
                    collected_fields[k] = v
        elif family == "service_coverage_check":
            for k, v in _extract_service_coverage_fields(message).items():
                if k not in collected_fields:
                    collected_fields[k] = v
    else:
        family = classify_issue_family(message)
        collected_fields.update(_infer_initial_fields(message, family))

    audit_entry = {
        "message": message,
        "family": family,
        "state_before": state,
        "collected_fields_after": collected_fields,
    }

    if family == "unknown":
        return {
            "action": "fallback_legacy",
            "answer": "Այս հարցը դեռ V2 հոսքով չի մշակվում։",
            "follow_up_question": None,
            "next_step": None,
            "state": {
                "family": None,
                "pending_field": None,
                "collected_fields": {},
                "audit": [audit_entry],
            },
            "matched_family": "unknown",
            "cited_sources": [],
        }

    workflow = get_workflow_by_family(family)
    missing_fields = _get_missing_fields(workflow, collected_fields)

    if missing_fields:
        next_pending_field = missing_fields[0]
        field_questions = workflow.get("field_questions", {}) or {}
        question = field_questions.get(next_pending_field, "Կնշե՞ք ավելի կոնկրետ տվյալներ։")

        return {
            "action": "clarify",
            "answer": "",
            "follow_up_question": question,
            "next_step": None,
            "state": {
                "family": family,
                "pending_field": next_pending_field,
                "collected_fields": collected_fields,
                "audit": [audit_entry],
            },
            "matched_family": family,
            "cited_sources": workflow.get("source_preferences", []) or [],
        }

    branch = _resolve_branch(workflow, collected_fields)

    if not branch:
        return {
            "action": "escalate",
            "answer": "Այս պահին հստակ ճյուղ չի գտնվել։",
            "follow_up_question": None,
            "next_step": "Պետք է փոխանցել ավելի մանրամասն դիտարկման։",
            "state": {
                "family": family,
                "pending_field": None,
                "collected_fields": collected_fields,
                "audit": [audit_entry],
            },
            "matched_family": family,
            "cited_sources": workflow.get("source_preferences", []) or [],
        }

    answer, next_step = compose_answer(family, branch, collected_fields)

    return {
        "action": "answer",
        "answer": answer,
        "follow_up_question": None,
        "next_step": next_step,
        "state": {
            "family": family,
            "pending_field": None,
            "collected_fields": collected_fields,
            "audit": [audit_entry],
        },
        "matched_family": family,
        "cited_sources": workflow.get("source_preferences", []) or [],
    }
