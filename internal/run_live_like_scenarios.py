import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from main import app


SCENARIOS_PATH = ROOT / "tests_live_like.json"
REPORT_PATH = ROOT / "live_like_scenarios_report.json"


def owner_matches(expected_owner: str, actual_owner: str | None) -> bool:
    if actual_owner is None:
        return False
    if actual_owner == expected_owner:
        return True
    if expected_owner.startswith("faq_"):
        return actual_owner.startswith(expected_owner)
    return False


def main() -> None:
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8-sig"))
    client = TestClient(app)
    results = []
    passed = 0

    for scenario in scenarios:
        state = {}
        turn_results = []
        scenario_ok = True

        for turn in scenario["turns"]:
            response = client.post(
                "/chat",
                json={"message": turn["message"], "state": state},
            ).json()
            actual_action = response.get("action")
            actual_card = response.get("matched_card_id")
            turn_ok = (
                actual_action == turn["expected_action"]
                and owner_matches(turn["expected_matched_card_id"], actual_card)
            )
            if not turn_ok:
                scenario_ok = False

            turn_results.append(
                {
                    "message": turn["message"],
                    "expected_action": turn["expected_action"],
                    "expected_matched_card_id": turn["expected_matched_card_id"],
                    "actual_action": actual_action,
                    "actual_matched_card_id": actual_card,
                    "pass": turn_ok,
                }
            )
            state = response.get("state") or {}

        if scenario_ok:
            passed += 1

        results.append(
            {
                "name": scenario["name"],
                "pass": scenario_ok,
                "turns": turn_results,
            }
        )

    report = {
        "scenario_count": len(scenarios),
        "passed": passed,
        "failed": len(scenarios) - passed,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "scenario_count": report["scenario_count"],
                "passed": report["passed"],
                "failed": report["failed"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
