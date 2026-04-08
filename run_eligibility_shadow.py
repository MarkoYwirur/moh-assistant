import json
import sys
from pathlib import Path

from router import get_top_candidates, normalize_text


BASE = Path(__file__).resolve().parent
ROOT_PATH = BASE / "kb" / "eligibility_status_coverage_root.json"
FIRST_TURN_PATH = BASE / "tests_eligibility_shadow_first_turn.json"
BRANCHES_PATH = BASE / "tests_eligibility_shadow_branches.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_root_card() -> dict:
    cards = load_json(ROOT_PATH)
    for card in cards:
        if card.get("id") == "eligibility_status_coverage_root_v1":
            return card
    raise ValueError("eligibility_status_coverage_root_v1 not found")


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
            if variant_norm and variant_norm in normalized:
                if len(variant_norm) > best_len:
                    best_key = key
                    best_len = len(variant_norm)
    return best_key


def has_answer_rule(card: dict, status_group: str | None, benefit_scope: str | None) -> bool | None:
    if not status_group or not benefit_scope:
        return None

    for rule in card.get("answer_rules", []):
        when = rule.get("when", {})
        if when.get("status_group") == status_group and when.get("benefit_scope") == benefit_scope:
            return True
    return False


def evaluate_first_turn(card: dict, cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        message = case["message"]
        current_winner = top_runtime_winner(message)
        inferred_status_group = infer_field_value(card, "status_group", message)
        inferred_benefit_scope = infer_field_value(card, "benefit_scope", message)
        expected_scope = case.get("expected_root_benefit_scope_if_any")
        rule_match = has_answer_rule(card, inferred_status_group, inferred_benefit_scope)

        results.append(
            {
                "name": case["name"],
                "message": message,
                "current_top_runtime_winner": current_winner,
                "expected_current_winner": case["expected_current_winner"],
                "current_winner_matches_expectation": current_winner == case["expected_current_winner"],
                "expected_root_status_group": case["expected_root_status_group"],
                "inferred_status_group": inferred_status_group,
                "status_group_match": inferred_status_group == case["expected_root_status_group"],
                "expected_root_benefit_scope_if_any": expected_scope,
                "inferred_benefit_scope": inferred_benefit_scope,
                "benefit_scope_match_when_expected": (
                    inferred_benefit_scope == expected_scope if expected_scope is not None else None
                ),
                "matching_answer_rule_for_inferred_branch": rule_match,
            }
        )
    return results


def evaluate_branches(card: dict, cases: list[dict]) -> list[dict]:
    results = []
    for case in cases:
        first_message = case["first_message"]
        second_message = case["second_message"]
        current_winner = top_runtime_winner(first_message)
        inferred_status_group = infer_field_value(card, "status_group", first_message)
        inferred_benefit_scope = infer_field_value(card, "benefit_scope", second_message)
        rule_match = has_answer_rule(card, inferred_status_group, inferred_benefit_scope)

        results.append(
            {
                "name": case["name"],
                "first_message": first_message,
                "second_message": second_message,
                "current_top_runtime_winner": current_winner,
                "expected_current_second_card": case["expected_current_second_card"],
                "expected_root_status_group": case["expected_root_status_group"],
                "inferred_status_group": inferred_status_group,
                "status_group_match": inferred_status_group == case["expected_root_status_group"],
                "expected_root_benefit_scope": case["expected_root_benefit_scope"],
                "inferred_benefit_scope": inferred_benefit_scope,
                "benefit_scope_match": inferred_benefit_scope == case["expected_root_benefit_scope"],
                "matching_answer_rule_for_branch": rule_match,
            }
        )
    return results


def summarize(first_turn: list[dict], branches: list[dict]) -> dict:
    branch_parity = []
    needs_refinement = []

    for item in first_turn + branches:
        status_ok = item.get("status_group_match") is True
        scope_value = item.get("benefit_scope_match_when_expected")
        if scope_value is None:
            scope_ok = True
        else:
            scope_ok = scope_value is True
        if "benefit_scope_match" in item:
            scope_ok = item["benefit_scope_match"] is True
        rule_key = (
            "matching_answer_rule_for_branch"
            if "matching_answer_rule_for_branch" in item
            else "matching_answer_rule_for_inferred_branch"
        )
        rule_ok = item.get(rule_key)
        rule_ok = True if rule_ok is None else (rule_ok is True)

        if status_ok and scope_ok and rule_ok:
            branch_parity.append(item["name"])
        else:
            needs_refinement.append(
                {
                    "name": item["name"],
                    "status_group_match": item.get("status_group_match"),
                    "benefit_scope_match": item.get("benefit_scope_match", item.get("benefit_scope_match_when_expected")),
                    "rule_match": item.get(rule_key),
                }
            )

    return {
        "branch_parity_cases": branch_parity,
        "needs_refinement": needs_refinement,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root_card = load_root_card()
    first_turn_cases = load_json(FIRST_TURN_PATH)
    branch_cases = load_json(BRANCHES_PATH)

    first_turn_results = evaluate_first_turn(root_card, first_turn_cases)
    branch_results = evaluate_branches(root_card, branch_cases)
    summary = summarize(first_turn_results, branch_results)

    report = {
        "first_turn": first_turn_results,
        "branches": branch_results,
        "summary": summary,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
