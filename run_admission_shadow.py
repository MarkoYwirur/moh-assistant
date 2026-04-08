import json
from pathlib import Path

from router import get_top_candidates, normalize_text


BASE = Path(__file__).resolve().parent
ROOT_PATH = BASE / "kb" / "service_admission_type_root.json"
SERVICE_COVERAGE_PATH = BASE / "kb" / "service_coverage.json"
FIRST_TURN_PATH = BASE / "tests_admission_shadow_first_turn.json"
BRANCHES_PATH = BASE / "tests_admission_shadow_branches.json"
TARGET_CARD_IDS = {
    "service_hospitalization_policy_curated",
    "service_surgery_policy_curated",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_root_card() -> dict:
    cards = load_json(ROOT_PATH)
    for card in cards:
        if card.get("id") == "service_admission_type_root_v1":
            return card
    raise ValueError("service_admission_type_root_v1 not found")


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


def has_answer_rule(card: dict, service_type: str | None, admission_type: str | None) -> bool | None:
    if not service_type or not admission_type:
        return None

    for rule in card.get("answer_rules", []):
        when = rule.get("when", {})
        if when.get("service_type") == service_type and when.get("admission_type") == admission_type:
            return True
    return False


def infer_current_card_admission_type(card: dict, text: str) -> str | None:
    return infer_field_value(card, "admission_type", text)


def infer_current_card_service_type(card_id: str | None) -> str | None:
    mapping = {
        "service_hospitalization_policy_curated": "hospitalization",
        "service_surgery_policy_curated": "surgery",
    }
    return mapping.get(card_id)


def current_card_has_matching_branch(card: dict, admission_type: str | None) -> bool | None:
    if not admission_type:
        return None
    for rule in card.get("answer_rules", []):
        when = rule.get("when", {})
        if when.get("admission_type") == admission_type:
            return True
    return False


def evaluate_first_turn(root_card: dict, cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        message = case["message"]
        current_winner = top_runtime_winner(message)
        inferred_service_type = infer_field_value(root_card, "service_type", message)
        inferred_admission_type = infer_field_value(root_card, "admission_type", message)
        expected_admission_type = case.get("expected_root_admission_type_if_any")
        rule_match = has_answer_rule(root_card, inferred_service_type, inferred_admission_type)

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
                "expected_root_admission_type_if_any": expected_admission_type,
                "inferred_admission_type": inferred_admission_type,
                "admission_type_match_when_expected": (
                    inferred_admission_type == expected_admission_type if expected_admission_type is not None else None
                ),
                "matching_answer_rule_for_inferred_branch": rule_match,
                "current_card_semantically_aligned": (
                    infer_current_card_service_type(current_winner) == inferred_service_type
                    if current_winner in TARGET_CARD_IDS and inferred_service_type is not None
                    else None
                ),
            }
        )
    return results


def evaluate_branches(root_card: dict, runtime_cards: dict[str, dict], cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        first_message = case["first_message"]
        second_message = case["second_message"]
        current_winner = top_runtime_winner(first_message)
        current_card = runtime_cards.get(case["expected_current_second_card"])
        inferred_service_type = infer_field_value(root_card, "service_type", first_message)
        inferred_admission_type = infer_field_value(root_card, "admission_type", second_message)
        rule_match = has_answer_rule(root_card, inferred_service_type, inferred_admission_type)

        current_card_admission_type = None
        current_card_branch_match = None
        current_card_service_type = infer_current_card_service_type(case["expected_current_second_card"])
        if current_card is not None:
            current_card_admission_type = infer_current_card_admission_type(current_card, second_message)
            current_card_branch_match = current_card_has_matching_branch(current_card, current_card_admission_type)

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
                "expected_root_admission_type": case["expected_root_admission_type"],
                "inferred_admission_type": inferred_admission_type,
                "admission_type_match": inferred_admission_type == case["expected_root_admission_type"],
                "matching_answer_rule_for_branch": rule_match,
                "current_card_service_type": current_card_service_type,
                "current_card_inferred_admission_type": current_card_admission_type,
                "current_card_has_matching_branch": current_card_branch_match,
                "current_card_semantically_aligned": (
                    current_card_service_type == inferred_service_type and current_card_admission_type == inferred_admission_type
                    if current_card_service_type is not None and current_card_admission_type is not None
                    else None
                ),
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
        admission_key = "admission_type_match" if "admission_type_match" in item else "admission_type_match_when_expected"
        admission_value = item.get(admission_key)
        admission_ok = True if admission_value is None else (admission_value is True)
        rule_key = "matching_answer_rule_for_branch" if "matching_answer_rule_for_branch" in item else "matching_answer_rule_for_inferred_branch"
        rule_value = item.get(rule_key)
        rule_ok = True if rule_value is None else (rule_value is True)
        semantic_alignment = item.get("current_card_semantically_aligned")
        semantic_ok = True if semantic_alignment is None else (semantic_alignment is True)

        clean = service_ok and admission_ok and rule_ok and semantic_ok
        if clean:
            parity_cases.append(item["name"])
            parity_by_service_type.setdefault(service_type, []).append(item["name"])
        else:
            detail = {
                "name": item["name"],
                "service_type_match": item.get("service_type_match"),
                "admission_type_match": item.get(admission_key),
                "rule_match": item.get(rule_key),
                "semantic_alignment": semantic_alignment,
            }
            needs_refinement.append(detail)
            refinement_by_service_type.setdefault(service_type, []).append(detail)

    return {
        "parity_cases": parity_cases,
        "needs_refinement": needs_refinement,
        "parity_by_service_type": parity_by_service_type,
        "refinement_by_service_type": refinement_by_service_type,
    }


def main():
    root_card = load_root_card()
    runtime_cards = load_runtime_cards()
    first_turn_cases = load_json(FIRST_TURN_PATH)
    branch_cases = load_json(BRANCHES_PATH)

    first_turn = evaluate_first_turn(root_card, first_turn_cases)
    branches = evaluate_branches(root_card, runtime_cards, branch_cases)
    summary = summarize(first_turn, branches)

    print(
        json.dumps(
            {
                "first_turn": first_turn,
                "branches": branches,
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
