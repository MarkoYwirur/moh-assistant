import json
from pathlib import Path

from fastapi.testclient import TestClient
from main import app

CASES_PATH = Path("app/data/regression/v2_regression_cases.json")
OUT_PATH = Path("app/data/regression/old_vs_v2_results.json")


def norm_behavior_from_response(payload: dict) -> str:
    action = payload.get("action")
    if action in {"clarify", "partial_answer_with_clarify"}:
        return "clarify"
    return "answer"


def main():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8-sig"))
    client = TestClient(app)
    rows = []

    for case in cases:
        message = case["message"]

        old_resp = client.post("/chat", json={"message": message, "state": {}})
        old_payload = old_resp.json()

        new_resp = client.post("/chat-v2", json={"message": message, "state": {}})
        new_payload = new_resp.json()

        old_behavior = norm_behavior_from_response(old_payload)
        new_behavior = norm_behavior_from_response(new_payload)

        old_family = old_payload.get("matched_card_id")
        new_family = new_payload.get("matched_family")

        row = {
            "id": case["id"],
            "message": message,
            "expected_family": case["family"],
            "expected_behavior": case["expected_behavior"],

            "old_action": old_payload.get("action"),
            "old_behavior": old_behavior,
            "old_family_proxy": old_family,
            "old_answer": old_payload.get("answer"),
            "old_follow_up_question": old_payload.get("follow_up_question"),
            "old_next_step": old_payload.get("next_step"),

            "new_action": new_payload.get("action"),
            "new_behavior": new_behavior,
            "new_family": new_family,
            "new_answer": new_payload.get("answer"),
            "new_follow_up_question": new_payload.get("follow_up_question"),
            "new_next_step": new_payload.get("next_step"),

            "old_behavior_match": old_behavior == case["expected_behavior"],
            "new_behavior_match": new_behavior == case["expected_behavior"],
            "new_family_match": new_family == case["family"],
        }

        if row["new_behavior_match"] and not row["old_behavior_match"]:
            row["winner"] = "v2"
        elif row["old_behavior_match"] and not row["new_behavior_match"]:
            row["winner"] = "old"
        else:
            row["winner"] = "tie"

        rows.append(row)

    OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {OUT_PATH}")
    print(f"TOTAL={len(rows)}")
    print(f"OLD_BEHAVIOR_MATCHES={sum(1 for r in rows if r['old_behavior_match'])}")
    print(f"NEW_BEHAVIOR_MATCHES={sum(1 for r in rows if r['new_behavior_match'])}")
    print(f"NEW_FAMILY_MATCHES={sum(1 for r in rows if r['new_family_match'])}")
    print(f"V2_WINS={sum(1 for r in rows if r['winner']=='v2')}")
    print(f"OLD_WINS={sum(1 for r in rows if r['winner']=='old')}")
    print(f"TIES={sum(1 for r in rows if r['winner']=='tie')}")


if __name__ == "__main__":
    main()
