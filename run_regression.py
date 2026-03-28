import json
from pathlib import Path
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

gold_tests = json.loads(Path("tests_gold.json").read_text(encoding="utf-8-sig"))
branch_tests = json.loads(Path("tests_branches.json").read_text(encoding="utf-8-sig"))

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

    if second_response.get("action") != test["expected_second_action"]:
        ok = False

    if second_response.get("matched_card_id") != test["expected_second_card"]:
        ok = False

    print({
        "name": test["name"],
        "ok": ok,
        "first_action": first_response.get("action"),
        "second_action": second_response.get("action"),
        "second_card": second_response.get("matched_card_id")
    })
