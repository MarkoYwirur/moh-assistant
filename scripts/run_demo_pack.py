import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app
from router import get_top_candidates


PACK_PATH = ROOT / "demo" / "demo_phrase_pack.json"


def main() -> None:
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    client = TestClient(app)
    results = []

    for item in pack:
        phrase = item["phrase"]
        top3 = [
            {
                "id": candidate["card"].get("id"),
                "score": round(candidate["score"], 4),
            }
            for candidate in get_top_candidates(phrase, top_k=3)
        ]
        response = client.post("/chat", json={"message": phrase, "state": {}}).json()
        observed_risk = ""
        if item.get("expected_family_hint") and response.get("matched_card_id") != item["expected_family_hint"]:
            observed_risk = f"expected {item['expected_family_hint']}, got {response.get('matched_card_id')}"

        results.append(
            {
                "phrase": phrase,
                "group": item["group"],
                "demo_status": item["demo_status"],
                "top_winner": top3[0]["id"] if top3 else None,
                "top3": top3,
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "risk_note": item.get("risk_note", ""),
                "observed_risk": observed_risk,
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
