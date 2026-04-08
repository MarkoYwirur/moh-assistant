import json
import sys
from pathlib import Path

from router import get_top_candidates, normalize_text


BASE = Path(__file__).resolve().parent
ROOT_PATH = BASE / "kb" / "service_referral_status_root.json"
SERVICE_COVERAGE_PATH = BASE / "kb" / "service_coverage.json"
FIRST_TURN_PATH = BASE / "tests_service_referral_shadow_first_turn.json"
BRANCHES_PATH = BASE / "tests_service_referral_shadow_branches.json"
TARGET_CARD_IDS = {
    "service_mri_policy_curated",
    "service_ct_policy_curated_v2",
    "service_lab_policy_curated",
    "service_specialist_policy_curated",
}
SEMANTIC_REFERRAL_STATUS = {
    "yes": "has_referral",
    "has_referral": "has_referral",
    "no": "no_referral",
    "no_referral": "no_referral",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_root_card() -> dict:
    cards = load_json(ROOT_PATH)
    for card in cards:
        if card.get("id") == "service_referral_status_root_v1":
            return card
    raise ValueError("service_referral_status_root_v1 not found")


def load_runtime_cards() -> dict[str, dict]:
    cards = {}
    for card in load_json(SERVICE_COVERAGE_PATH):
        card_id = card.get("id")
        if card_id in TARGET_CARD_IDS:
            cards[card_id] = card
    missing = TARGET_CARD_IDS - set(cards)
    if missing:
        raise ValueError(f"Missing service cards: {sorted(missing)}")
    return cards


def top_runtime_winner(message: str) -> str | None:
    candidates = get_top_candidates(message, top_k=1)
    if not candidates:
        return None
    return candidates[0].get("card", {}).get("id")


def infer_field_value(card: dict, field_name: str, text: str) -> str | None:
    normalized = normalize_text(text)
    field_values = card.get("field_values", {}).get(field_name, {})

    best_key = None
    best_len = -1
    for key, variants in field_values.items():
        for variant in variants:
            variant_norm = normalize_text(variant)
            if variant_norm and variant_norm in normalized and len(variant_norm) > best_len:
                best_key = key
                best_len = len(variant_norm)
    return best_key


def has_answer_rule(card: dict, service_type: str | None, referral_status: str | None) -> bool | None:
    if not service_type or not referral_status:
        return None

    for rule in card.get("answer_rules", []):
        when = rule.get("when", {})
        if when.get("service_type") == service_type and when.get("referral_status") == referral_status:
            return True
    return False


def infer_current_card_referral_status(card: dict, text: str) -> str | None:
    inferred = infer_field_value(card, "referral_status", text)
    if inferred is None:
        return None
    return SEMANTIC_REFERRAL_STATUS.get(inferred)


def evaluate_first_turn(root_card: dict, cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        message = case["message"]
        current_winner = top_runtime_winner(message)
        inferred_service_type = infer_field_value(root_card, "service_type", message)
        inferred_referral_status = infer_field_value(root_card, "referral_status", message)
        expected_referral_status = case.get("expected_root_referral_status_if_any")
        rule_match = has_answer_rule(root_card, inferred_service_type, inferred_referral_status)

        results.append(
            {
                "name": case["name"],
                "message": message,
                "current_top_runtime_winner": current_winner,
                "expected_current_winner": case["expected_current_winner"],
                "current_winner_matches_expectation": current_winner == case["expected_current_winner"],
                "expected_root_service_type": case["expected_root_service_type"],
                "inferred_service_type": inferred_service_type,
                "service_type_match": inferred_service_type == case["expected_root_service_type"],
                "expected_root_referral_status_if_any": expected_referral_status,
                "inferred_referral_status": inferred_referral_status,
                "referral_status_match_when_expected": (
                    inferred_referral_status == expected_referral_status if expected_referral_status is not None else None
                ),
                "matching_answer_rule_for_inferred_branch": rule_match,
                "current_card_branch_semantically_aligned": None,
            }
        )
    return results


def evaluate_branches(root_card: dict, runtime_cards: dict[str, dict], cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        first_message = case["first_message"]
        second_message = case["second_message"]
        current_winner = top_runtime_winner(first_message)
        current_card = runtime_cards[case["expected_current_second_card"]]
        inferred_service_type = infer_field_value(root_card, "service_type", first_message)
        inferred_referral_status = infer_field_value(root_card, "referral_status", second_message)
        rule_match = has_answer_rule(root_card, inferred_service_type, inferred_referral_status)
        current_card_referral_status = infer_current_card_referral_status(current_card, second_message)

        results.append(
            {
                "name": case["name"],
                "first_message": first_message,
                "second_message": second_message,
                "current_top_runtime_winner": current_winner,
                "expected_current_second_card": case["expected_current_second_card"],
                "current_winner_matches_expectation": current_winner == case["expected_current_second_card"],
                "expected_root_service_type": case["expected_root_service_type"],
                "inferred_service_type": inferred_service_type,
                "service_type_match": inferred_service_type == case["expected_root_service_type"],
                "expected_root_referral_status": case["expected_root_referral_status"],
                "inferred_referral_status": inferred_referral_status,
                "referral_status_match": inferred_referral_status == case["expected_root_referral_status"],
                "matching_answer_rule_for_branch": rule_match,
                "current_card_inferred_referral_status": current_card_referral_status,
                "current_card_branch_semantically_aligned": current_card_referral_status == inferred_referral_status,
            }
        )
    return results


def summarize(first_turn: list[dict], branches: list[dict]) -> dict:
    parity_cases = []
    needs_refinement = []
    parity_by_service_type = {}
    refinement_by_service_type = {}

    for item in first_turn + branches:
        service_type = item.get("expected_root_service_type")
        service_ok = item.get("service_type_match") is True
        referral_key = "referral_status_match" if "referral_status_match" in item else "referral_status_match_when_expected"
        referral_value = item.get(referral_key)
        referral_ok = True if referral_value is None else (referral_value is True)
        rule_key = "matching_answer_rule_for_branch" if "matching_answer_rule_for_branch" in item else "matching_answer_rule_for_inferred_branch"
        rule_value = item.get(rule_key)
        rule_ok = True if rule_value is None else (rule_value is True)
        alignment = item.get("current_card_branch_semantically_aligned")
        alignment_ok = True if alignment is None else (alignment is True)

        if service_ok and referral_ok and rule_ok and alignment_ok:
            parity_cases.append(item["name"])
            if service_type:
                parity_by_service_type.setdefault(service_type, []).append(item["name"])
        else:
            issue = {
                "name": item["name"],
                "service_type_match": item.get("service_type_match"),
                "referral_status_match": referral_value,
                "rule_match": rule_value,
                "semantic_branch_alignment": alignment,
            }
            needs_refinement.append(issue)
            if service_type:
                refinement_by_service_type.setdefault(service_type, []).append(issue)

    return {
        "parity_cases": parity_cases,
        "needs_refinement": needs_refinement,
        "parity_by_service_type": parity_by_service_type,
        "refinement_by_service_type": refinement_by_service_type,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root_card = load_root_card()
    runtime_cards = load_runtime_cards()
    first_turn_cases = load_json(FIRST_TURN_PATH)
    branch_cases = load_json(BRANCHES_PATH)

    first_turn_results = evaluate_first_turn(root_card, first_turn_cases)
    branch_results = evaluate_branches(root_card, runtime_cards, branch_cases)
    summary = summarize(first_turn_results, branch_results)

    report = {
        "first_turn": first_turn_results,
        "branches": branch_results,
        "summary": summary,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
