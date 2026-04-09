from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import main
from app.issue_family_classifier import normalize_text_v2


PACK_PATH = Path("internal/phase5_rights_governance_legal_basis_pack.json")
SHADOW_FAMILY_ID = "info_rights_governance_legal_basis_v1"

POSITIVE_MARKERS = (
    "գաղտնի",
    "անձնական տվյալ",
    "բժշկական տվյալ",
    "կարող է տեսնել",
    "օտարերկր",
    "միջազգային պայմանագիր",
    "իրավական ակտ",
    "իրավական հիմ",
    "օրենսդր",
    "վերահսկ",
    "դեղերի որակ",
    "դեղատ",
    "պատասխանատվ",
    "մեղքով վնաս",
    "իրավունքներ",
    "ամրագրված",
    "արտոնյալ բուժօգն",
)

NEGATIVE_MARKERS = (
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "հոսպիտալ",
    "վիրահատ",
    "ընդունում",
    "պետպատվերով չի անցնում",
    "փող են ուզում",
    "վճարել եմ",
    "ինչ է հասնում",
    "ովքեր կարող են",
)


def classify_shadow(text: str) -> str:
    normalized = normalize_text_v2(text)
    if any(marker in normalized for marker in NEGATIVE_MARKERS):
        return "out_of_scope"
    if any(marker in normalized for marker in POSITIVE_MARKERS):
        return SHADOW_FAMILY_ID
    return "out_of_scope"


def main_cli() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    client = TestClient(main.app)

    positives = pack["positive_parity_examples"]
    negatives = []
    for values in pack["negative_boundary_probes"].values():
        negatives.extend(values)

    print("=== POSITIVE PARITY ===")
    positive_hits = 0
    for text in positives:
        response = client.post("/chat", json={"message": text, "state": {}}).json()
        shadow = classify_shadow(text)
        runtime = response.get("matched_card_id")
        action = response.get("action")
        if shadow == SHADOW_FAMILY_ID:
            positive_hits += 1
        print(f"text={text}")
        print(f"shadow={shadow}")
        print(f"runtime_action={action}")
        print(f"runtime_owner={runtime}")
        print("-" * 80)

    print("=== NEGATIVE BOUNDARIES ===")
    negative_clean = 0
    for text in negatives:
        response = client.post("/chat", json={"message": text, "state": {}}).json()
        shadow = classify_shadow(text)
        runtime = response.get("matched_card_id")
        action = response.get("action")
        if shadow != SHADOW_FAMILY_ID:
            negative_clean += 1
        print(f"text={text}")
        print(f"shadow={shadow}")
        print(f"runtime_action={action}")
        print(f"runtime_owner={runtime}")
        print("-" * 80)

    print("=== SUMMARY ===")
    print(f"positive_examples={len(positives)}")
    print(f"positive_shadow_hits={positive_hits}")
    print(f"negative_examples={len(negatives)}")
    print(f"negative_shadow_clean={negative_clean}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
