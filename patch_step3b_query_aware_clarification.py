from pathlib import Path

# ---------- main.py ----------
main_path = Path("main.py")
main_text = main_path.read_text(encoding="utf-8")

old_main = """    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
    )
"""

new_main = """    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
        user_text=request.message,
    )
"""

if old_main not in main_text:
    raise SystemExit("MAIN_BUILD_RESPONSE_CALL_NOT_FOUND")

main_text = main_text.replace(old_main, new_main, 1)
main_path.write_text(main_text, encoding="utf-8")

# ---------- generator.py ----------
gen_path = Path("generator.py")
gen_text = gen_path.read_text(encoding="utf-8")

old_gen = """def build_response(decision: dict, collected_fields: dict | None = None) -> dict:
    payload = build_semantic_payload(decision, collected_fields)
"""

new_gen = """def build_response(decision: dict, collected_fields: dict | None = None, user_text: str = "") -> dict:
    payload = build_semantic_payload(decision, collected_fields, user_text=user_text)
"""

if old_gen not in gen_text:
    raise SystemExit("GENERATOR_BUILD_RESPONSE_SIGNATURE_NOT_FOUND")

gen_text = gen_text.replace(old_gen, new_gen, 1)
gen_path.write_text(gen_text, encoding="utf-8")

# ---------- semantic_generator.py ----------
sem_path = Path("semantic_generator.py")
sem_text = sem_path.read_text(encoding="utf-8")

old_sig = """def build_semantic_payload(decision: dict, collected_fields: dict | None = None) -> dict:
"""

new_sig = """def build_semantic_payload(decision: dict, collected_fields: dict | None = None, user_text: str = "") -> dict:
"""

if old_sig not in sem_text:
    raise SystemExit("SEMANTIC_SIGNATURE_NOT_FOUND")

sem_text = sem_text.replace(old_sig, new_sig, 1)

insert_after = """def _get_field_question(card: dict, field_name: str) -> str:
    field_questions = card.get("field_questions", {})
    if isinstance(field_questions, dict):
        question = field_questions.get(field_name)
        if isinstance(question, str) and question.strip():
            return question.strip()

    return "Կնշե՞ք ավելի կոնկրետ տվյալներ։"


"""

helper_block = """def _select_best_missing_field(card: dict, collected_fields: dict, user_text: str = "") -> str | None:
    missing_fields = _get_missing_fields(card, collected_fields)
    if not missing_fields:
        return None

    if len(missing_fields) == 1:
        return missing_fields[0]

    text = (user_text or "").lower()
    card_id = str(card.get("id", "") or "").lower()

    def has_any(*parts: str) -> bool:
        return any(p in text for p in parts)

    # Payment dispute: service context first is the highest leverage.
    if card_id == "complaint_unexpected_payment_dispute_v2":
        if "service_context" in missing_fields:
            return "service_context"

    # Duplicate charge / wrong status: first identify issue type if user already hints it.
    if card_id == "complaint_duplicate_charge_or_wrong_payment_status_v1":
        if "payment_issue_type" in missing_fields and has_any("կրկն", "երկու անգամ", "սխալ է երևում", "կարգավիճակ", "wrong status", "duplicate"):
            return "payment_issue_type"
        if "payment_context" in missing_fields and has_any("վճար", "գանձ", "ծառայություն"):
            return "payment_context"

    # Medicine not provided:
    # If user already told us the location context (e.g. pharmacy), ask medicine details first.
    # If user clearly told us the medicine but not where, ask location first.
    if card_id == "complaint_medicine_not_provided_v1":
        location_markers = ("դեղատ", "pharmacy", "բուժհաստատ", "հաստատությ", "կետ")
        medicine_markers = ("մգ", "mg", "մլ", "ml", "հաբ", "սրվակ", "դեղաչափ", "tablet", "capsule")
        has_location = has_any(*location_markers)
        has_medicine_details = has_any(*medicine_markers)

        if "medicine_name_details" in missing_fields and has_location:
            return "medicine_name_details"
        if "dispense_location" in missing_fields and has_medicine_details:
            return "dispense_location"

    # ArMed visibility: ask what item is missing before anything else.
    if card_id == "technical_armed_visibility_issue_v1":
        if "armed_item_type" in missing_fields:
            return "armed_item_type"
        if "armed_issue_context" in missing_fields:
            return "armed_issue_context"

    # Generic routing: if specialist is already mentioned, don't ask broad/general-care style first.
    if card_id == "routing_referral_where_to_go_v2":
        if "routing_need_type" in missing_fields:
            return "routing_need_type"

    if card_id == "routing_specialist_referral_confusion_v1":
        if "specialist_type_or_purpose" in missing_fields:
            return "specialist_type_or_purpose"

    return missing_fields[0]


"""

if insert_after not in sem_text:
    raise SystemExit("FIELD_QUESTION_BLOCK_NOT_FOUND")

sem_text = sem_text.replace(insert_after, insert_after + helper_block, 1)

old_missing = """        missing_fields = _get_missing_fields(card, collected_fields)
        missing_field = missing_fields[0] if missing_fields else None
"""

new_missing = """        missing_fields = _get_missing_fields(card, collected_fields)
        missing_field = _select_best_missing_field(card, collected_fields, user_text=user_text)
"""

if old_missing not in sem_text:
    raise SystemExit("MISSING_FIELD_SELECTION_BLOCK_NOT_FOUND")

sem_text = sem_text.replace(old_missing, new_missing, 1)
sem_path.write_text(sem_text, encoding="utf-8")

print("STEP3B_PATCHED_OK")
