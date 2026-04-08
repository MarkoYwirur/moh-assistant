from pathlib import Path
import sys

path = Path("router.py")
t = path.read_text(encoding="utf-8")

t = t.replace("from intent_refiner import refine_user_intent", "from intent_refiner import detect_refined_intent")

if "def _call_refine_user_intent(" not in t:
    marker = "def _intent_refinement_bias("
    helper = '''

def _call_refine_user_intent(user_text: str):
    normalized = normalize_text(user_text)
    if not normalized:
        return None
    try:
        return detect_refined_intent(normalized)
    except Exception:
        return None

'''
    idx = t.find(marker)
    if idx == -1:
        print("INTENT_BIAS_FUNCTION_NOT_FOUND")
        sys.exit(1)
    t = t[:idx] + helper + t[idx:]

t = t.replace("refined = refine_user_intent(user_text)", "refined = _call_refine_user_intent(user_text)")

start = t.find("def _intent_refinement_bias(")
if start == -1:
    print("INTENT_BIAS_START_NOT_FOUND")
    sys.exit(1)

next_def = t.find("\ndef ", start + 1)
if next_def == -1:
    next_def = len(t)

new_bias = '''def _intent_refinement_bias(card: dict, normalized_text: str, refined: dict | None) -> float:
    if not refined:
        return 0.0

    bias = 0.0

    routing_mode = str(refined.get("routing_mode", "") or "").strip().lower()
    payment_mode = str(refined.get("payment_mode", "") or "").strip().lower()
    medicine_mode = str(refined.get("medicine_mode", "") or "").strip().lower()
    signals = [str(x).lower() for x in (refined.get("signals", []) or [])]

    card_id = str(card.get("id", "") or "").lower()
    category = str(card.get("category", "") or "").lower()
    patterns_blob = " ".join(card.get("patterns", []) or []).lower()
    hay = f"{card_id} {category} {patterns_blob}"

    def has_any(*needles: str) -> bool:
        return any(n.lower() in hay for n in needles if n)

    # routing bias
    if routing_mode:
        if routing_mode in {"referral_where_to_go", "where_to_go_referral", "referral"}:
            if has_any("routing_referral_where_to_go", "referral_where_to_go"):
                bias += 2.8
            if has_any("specialist_service", "generic_specialist_service"):
                bias -= 1.0

        if routing_mode in {"specialist_referral_confusion", "specialist_referral", "specialist"}:
            if has_any("routing_specialist_referral_confusion", "specialist_referral_confusion", "specialist_referral"):
                bias += 2.8
            if has_any("routing_referral_where_to_go"):
                bias -= 0.5

    # payment / denial bias
    if payment_mode:
        if payment_mode in {"charged_despite_referral", "unexpected_payment", "payment_dispute", "paid_but_should_be_covered"}:
            if has_any("complaint_duplicate_charge_or_wrong_payment_status", "payment", "charged", "denied", "co_pay", "copay"):
                bias += 2.6

    # medicine bias
    if medicine_mode:
        if medicine_mode in {"not_provided", "not_available", "pharmacy_missing", "medicine_not_provided"}:
            if has_any("complaint_medicine_not_provided", "medicine_not_provided"):
                bias += 2.8

        if medicine_mode in {"generic_name_only", "generic_medicine_name", "needs_exact_medicine"}:
            if has_any("medicine_coverage_exact_name_dosage_form", "exact_name_dosage_form"):
                bias += 2.3

    # direct phrase rescue
    if "ուղեգիր ունեմ բայց չգիտեմ ուր գնամ" in normalized_text:
        if has_any("routing_referral_where_to_go"):
            bias += 3.2

    if "ուր դիմեմ ուղեգիր ստանալու համար" in normalized_text:
        if has_any("routing_referral_where_to_go"):
            bias += 3.0

    if "նեղ մասնագետի ուղեգիր է պետք" in normalized_text:
        if has_any("routing_specialist_referral_confusion"):
            bias += 3.2

    if "համակարգում չի երևում" in normalized_text or "չի երևում համակարգում" in normalized_text:
        if has_any("technical_armed_visibility_issue", "armed_visibility_issue"):
            bias += 3.0

    if "ասում են վճարովի է բայց ունեմ ուղեգիր" in normalized_text:
        if has_any("complaint_duplicate_charge_or_wrong_payment_status", "payment", "charged", "denied"):
            bias += 3.0

    if "դեղատանը չկա" in normalized_text:
        if has_any("complaint_medicine_not_provided", "medicine_not_provided"):
            bias += 3.0

    # weak signal bonus
    if any("routing:" in s for s in signals):
        if "routing" in category or "routing_" in card_id:
            bias += 0.4

    if any("payment:" in s for s in signals):
        if has_any("payment", "charge", "charged", "wrong_payment_status", "duplicate_charge"):
            bias += 0.4

    if any("medicine:" in s for s in signals):
        if has_any("medicine", "drug", "pharmacy", "dosage", "coverage_exact"):
            bias += 0.4

    return round(bias, 4)
'''

t = t[:start] + new_bias.rstrip() + "\n\n" + t[next_def:].lstrip("\n")

path.write_text(t, encoding="utf-8")
print("ROUTER_REFINER_SCHEMA_PATCH_OK")
