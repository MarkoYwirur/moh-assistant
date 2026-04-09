import json
from pathlib import Path
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def _load_fixture(name: str):
    for path in (Path(name), Path("internal") / name):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig"))
    raise FileNotFoundError(f"Missing regression fixture: {name}")


gold_tests = _load_fixture("tests_gold.json")
branch_tests = _load_fixture("tests_branches.json")

print("=== FIRST TURN TESTS ===")
for test in gold_tests:
    payload = {
        "message": test["message"],
        "state": {}
    }
    response = client.post("/chat", json=payload)
    data = response.json()

    ok = True

    if "expected_action" in test and data.get("action") != test["expected_action"]:
        ok = False

    if "expected_matched_card_id" in test and data.get("matched_card_id") != test["expected_matched_card_id"]:
        ok = False

    print({
        "name": test["name"],
        "ok": ok,
        "action": data.get("action"),
        "matched_card_id": data.get("matched_card_id")
    })

print("=== BRANCH TESTS ===")
for test in branch_tests:
    first_response = client.post("/chat", json={
        "message": test["first_message"],
        "state": {}
    }).json()

    second_response = client.post("/chat", json={
        "message": test["second_message"],
        "state": first_response.get("state", {})
    }).json()

    ok = True

    if "expected_second_action" in test and second_response.get("action") != test["expected_second_action"]:
        ok = False

    if "expected_second_card" in test and second_response.get("matched_card_id") != test["expected_second_card"]:
        ok = False

    if "third_message" in test:
        third_response = client.post("/chat", json={
            "message": test["third_message"],
            "state": second_response.get("state", {})
        }).json()

        if "expected_third_action" in test and third_response.get("action") != test["expected_third_action"]:
            ok = False

        if "expected_third_card" in test and third_response.get("matched_card_id") != test["expected_third_card"]:
            ok = False

        print({
            "name": test["name"],
            "ok": ok,
            "first_action": first_response.get("action"),
            "second_action": second_response.get("action"),
            "third_action": third_response.get("action"),
            "third_card": third_response.get("matched_card_id")
        })
    else:
        print({
            "name": test["name"],
            "ok": ok,
            "first_action": first_response.get("action"),
            "second_action": second_response.get("action"),
            "second_card": second_response.get("matched_card_id")
        })
