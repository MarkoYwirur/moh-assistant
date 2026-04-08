from fastapi.testclient import TestClient
import json
import main

client = TestClient(main.app)
phrases = [
    "ինչ տվյալներ պետք է բողոքի համար",
    "բողոքից հետո ինչ է լինում",
    "ինչպես բողոք ներկայացնել",
    "8003",
    "երեխայի բժշկական օգնության բողոք",
    "երեխայի համար դեղ է ծածկվում",
]

rows = []
for phrase in phrases:
    response = client.post("/chat", json={"message": phrase}).json()
    answer = response.get("answer", "")
    sentence_count = sum(answer.count(mark) for mark in ["։", "?", "!"])
    rows.append(
        {
            "phrase": phrase,
            "action": response.get("action"),
            "matched_card_id": response.get("matched_card_id"),
            "sentence_count": sentence_count,
            "answer": answer,
        }
    )

print(json.dumps(rows, ensure_ascii=False, indent=2))
