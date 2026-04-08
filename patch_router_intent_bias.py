from pathlib import Path
import re
import sys

path = Path("router.py")
t = path.read_text(encoding="utf-8")

new_get_top_candidates = '''def get_top_candidates(user_text: str, top_k: int = 5, forced_card: dict | None = None) -> list:
    if forced_card is not None:
        return [{"card": forced_card, "score": 99.0}]

    text = normalize_text(user_text)
    scored = []

    for card in load_all_cards():
        base_score = score_card(card, user_text)
        if base_score <= 0:
            continue

        final_score = base_score

        try:
            refined = refine_user_intent(user_text)
        except Exception:
            refined = None

        if refined:
            final_score += _intent_refinement_bias(card, text, refined)

        scored.append({
            "card": card,
            "score": round(final_score, 4),
            "base_score": round(base_score, 4),
        })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
'''

new_bias_fn = '''

def _intent_refinement_bias(card: dict, normalized_text: str, refined: dict | None) -> float:
    if not refined:
        return 0.0

    bias = 0.0

    primary_intent = str(refined.get("primary_intent", "") or "").strip().lower()
    secondary_intents = refined.get("secondary_intents", []) or []
    entities = refined.get("entities", {}) or {}
    route_target = str(entities.get("route_target", "") or "").strip().lower()
    problem_type = str(entities.get("problem_type", "") or "").strip().lower()
    service_type = str(entities.get("service_type", "") or "").strip().lower()

    card_id = str(card.get("id", "") or "").lower()
    category = str(card.get("category", "") or "").lower()
    patterns_blob = " ".join(card.get("patterns", []) or []).lower()

    def has_any(*needles: str) -> bool:
        hay = f"{card_id} {category} {patterns_blob}"
        return any(n.lower() in hay for n in needles if n)

    if primary_intent in {"where_to_go", "routing", "referral_routing"}:
        if route_target in {"referral", "ուղեգիր"}:
            if has_any("routing_referral_where_to_go", "referral_where_to_go"):
                bias += 2.5
            if has_any("specialist_service", "generic_specialist_service"):
                bias -= 1.0

        if route_target in {"specialist", "մասնագետ", "specialist_referral"}:
            if has_any("routing_specialist_referral_confusion", "specialist_referral"):
                bias += 2.5
            if has_any("routing_referral_where_to_go"):
                bias -= 0.6

    if primary_intent in {"complaint", "problem_resolution", "denied_service", "charged", "record_issue", "technical_issue"}:
        if problem_type in {"medicine_not_provided", "drug_not_given"}:
            if has_any("complaint_medicine_not_provided", "medicine_not_provided"):
                bias += 2.8

        if problem_type in {"missing_or_wrong_record", "wrong_record", "record_missing"}:
            if has_any("complaint_missing_or_wrong_record", "missing_or_wrong_record"):
                bias += 2.8

        if problem_type in {"armed_visibility_issue", "system_not_visible", "technical_visibility"}:
            if has_any("technical_armed_visibility_issue", "armed_visibility_issue"):
                bias += 2.8

        if problem_type in {"duplicate_charge", "wrong_payment_status", "payment_problem"}:
            if has_any("complaint_duplicate_charge_or_wrong_payment_status", "duplicate_charge", "wrong_payment_status"):
                bias += 2.8

    if "ուղեգիր ունեմ բայց չգիտեմ ուր գնամ" in normalized_text:
        if has_any("routing_referral_where_to_go"):
            bias += 3.0

    if "նեղ մասնագետի ուղեգիր է պետք" in normalized_text:
        if has_any("routing_specialist_referral_confusion"):
            bias += 3.0

    if "համակարգում չի երևում" in normalized_text or "չի երևում համակարգում" in normalized_text:
        if has_any("technical_armed_visibility_issue"):
            bias += 3.0

    if "ասում են վճարովի է բայց ունեմ ուղեգիր" in normalized_text:
        if has_any("complaint", "payment", "charged", "denied"):
            bias += 2.2

    if "դեղատանը չկա" in normalized_text:
        if has_any("complaint_medicine_not_provided", "medicine_not_provided"):
            bias += 2.2

    if service_type:
        if service_type in card_id or service_type in patterns_blob:
            bias += 0.8

    secondary_blob = " ".join(str(x).lower() for x in secondary_intents)
    if "clarification" in secondary_blob and "clarification" in card_id:
        bias += 0.4

    return round(bias, 4)
'''

if "from intent_refiner import refine_user_intent" not in t:
    lines = t.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, "from intent_refiner import refine_user_intent")
    t = "\n".join(lines) + "\n"

pattern_get = re.compile(
    r"def get_top_candidates\(user_text: str, top_k: int = 5, forced_card: dict \| None = None\) -> list:\r?\n(?:    .*\r?\n)+?(?=\r?\ndef |\Z)",
    re.MULTILINE
)
if not pattern_get.search(t):
    print("GET_TOP_CANDIDATES_BLOCK_NOT_FOUND")
    sys.exit(1)
t = pattern_get.sub(new_get_top_candidates + "\n", t, count=1)

pattern_score = re.compile(
    r"(def score_card\(card: dict, user_text: str\) -> float:\r?\n(?:    .*\r?\n)+?)(?=\r?\ndef |\Z)",
    re.MULTILINE
)
m = pattern_score.search(t)
if not m:
    print("SCORE_CARD_BLOCK_NOT_FOUND")
    sys.exit(1)

score_block = m.group(1)
if "def _intent_refinement_bias(" not in t:
    t = t[:m.end(1)] + new_bias_fn + t[m.end(1):]

path.write_text(t, encoding="utf-8")
print("PATCH_OK")
