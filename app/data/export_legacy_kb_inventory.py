from pathlib import Path
import json

KB_DIR = Path("kb")
OUT_PATH = Path("app/data/legacy_kb_inventory.json")

rows = []

for path in sorted(KB_DIR.glob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        rows.append({
            "source_file": path.name,
            "error": str(e),
        })
        continue

    if not isinstance(data, list):
        rows.append({
            "source_file": path.name,
            "error": "top-level is not a list",
        })
        continue

    for card in data:
        if not isinstance(card, dict):
            continue

        rows.append({
            "source_file": path.name,
            "id": card.get("id"),
            "category": card.get("category"),
            "runtime_enabled": card.get("runtime_enabled"),
            "card_kind": card.get("card_kind"),
            "priority": card.get("priority"),
            "has_patterns": bool(card.get("patterns")),
            "has_required_fields": bool(card.get("required_fields")),
            "has_answer_rules": bool(card.get("answer_rules")),
            "approved_answer_preview": (card.get("approved_answer") or "")[:160],
        })

OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"WROTE {OUT_PATH}")
print(f"TOTAL_ROWS={len(rows)}")
