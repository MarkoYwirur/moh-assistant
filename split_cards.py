import json
from pathlib import Path

KB_DIR = Path("kb")
SOURCE_FILE = KB_DIR / "cards.json"

CATEGORY_TO_FILE = {
    "eligibility": "eligibility.json",
    "service_coverage": "service_coverage.json",
    "medicine": "medicines.json",
    "faq": "faq.json",
    "complaint": "complaints.json",
    "routing": "routing.json",
}

def main():
    if not SOURCE_FILE.exists():
        print(f"ERROR: Source file not found: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)

    buckets = {filename: [] for filename in CATEGORY_TO_FILE.values()}
    unknown = []

    for card in cards:
        category = card.get("category")
        filename = CATEGORY_TO_FILE.get(category)

        if filename:
            buckets[filename].append(card)
        else:
            unknown.append(card)

    for filename, items in buckets.items():
        target = KB_DIR / filename
        with open(target, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"Wrote {len(items)} cards -> {target}")

    if unknown:
        unknown_file = KB_DIR / "unknown.json"
        with open(unknown_file, "w", encoding="utf-8") as f:
            json.dump(unknown, f, ensure_ascii=False, indent=2)
        print(f"Wrote {len(unknown)} unknown-category cards -> {unknown_file}")
    else:
        print("No unknown-category cards found.")

if __name__ == "__main__":
    main()