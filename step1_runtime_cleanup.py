import json
from pathlib import Path
from shutil import copy2

PROJECT_DIR = Path(__file__).resolve().parent
KB_DIR = PROJECT_DIR / "kb"
BACKUP_DIR = PROJECT_DIR / "kb_step1_backup"

CATEGORY_ALIASES = {
    "medicine": "medicines",
    "medicines": "medicines",
    "complaint": "complaints",
    "complaints": "complaints",
    "routing": "routing",
    "service_coverage": "service_coverage",
    "eligibility": "eligibility",
    "faq": "faq",
}

NON_RUNTIME_ID_SUBSTRINGS = [
    "executive_summary",
    "official_sources",
    "official_complaint_channels",
    "navigation_logic",
    "top_25_citizen_routing_intents",
    "card_ready_knowledge_units",
    "missing_operational_details",
    "group_1_",
    "responsible_institution",
    "sub_unit_department",
    "cross_verification",
    "secondary_sources",
    "reports_and_research",
    "government_decision",
    "arlis",
    "official_legal_texts",
    "operational_front_door",
    "eligibility_group_matrix",
    "core_definitions",
    "safe_answer_boundaries",
    "safe_general_answer_boundaries",
    "common_citizen_questions",
    "key_facts_card_ready_units",
    "gaps_and_conflicts",
]

NON_RUNTIME_TEXT_SUBSTRINGS = [
    "executive summary",
    "official sources",
    "navigation logic",
    "top 25 citizen routing intents",
    "card-ready knowledge units",
    "missing operational details",
    "official legal texts",
    "operational front door",
    "eligibility group matrix",
    "core definitions",
    "safe general answer boundaries",
    "safe answer boundaries",
    "common citizen questions",
    "key facts",
    "gaps and conflicts",
    "cross-verification",
    "secondary sources",
    "reports and research",
    "responsible institution",
    "sub-unit department",
]


def card_text_blob(card: dict) -> str:
    patterns = card.get("patterns", [])
    if not isinstance(patterns, list):
        patterns = []
    return " ".join([
        str(card.get("id", "") or ""),
        str(card.get("subtopic", "") or ""),
        str(card.get("approved_answer", "") or "")[:250],
        *[str(p) for p in patterns],
    ]).lower()


def default_runtime_enabled(card: dict) -> bool:
    card_id = str(card.get("id", "") or "").lower()
    blob = card_text_blob(card)
    if any(fragment in card_id for fragment in NON_RUNTIME_ID_SUBSTRINGS):
        return False
    if any(fragment in blob for fragment in NON_RUNTIME_TEXT_SUBSTRINGS):
        return False
    return True


def main() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    total = 0
    runtime = 0
    research = 0

    for path in sorted(KB_DIR.glob("*.json")):
        copy2(path, BACKUP_DIR / path.name)

        with open(path, "r", encoding="utf-8-sig") as f:
            content = json.load(f)

        if isinstance(content, list):
            cards = content
            wrap = None
        elif isinstance(content, dict) and isinstance(content.get("cards"), list):
            cards = content["cards"]
            wrap = content
        else:
            print(f"SKIP {path.name}: unexpected format")
            continue

        for card in cards:
            total += 1
            category = str(card.get("category", "") or "").strip().lower()
            card["category"] = CATEGORY_ALIASES.get(category, category)
            enabled = default_runtime_enabled(card)
            card["runtime_enabled"] = enabled
            card["card_kind"] = "citizen_runtime" if enabled else "research_note"
            if enabled:
                runtime += 1
            else:
                research += 1

        payload = cards if wrap is None else {**wrap, "cards": cards}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print(f"PATCHED {path.name}")

    print("-" * 60)
    print(f"TOTAL_CARDS={total}")
    print(f"RUNTIME_ENABLED={runtime}")
    print(f"RESEARCH_DISABLED={research}")
    print(f"BACKUP_DIR={BACKUP_DIR}")


if __name__ == "__main__":
    main()
