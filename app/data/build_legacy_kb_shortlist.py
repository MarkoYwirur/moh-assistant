import json
from pathlib import Path

IN_PATH = Path("app/data/legacy_kb_inventory.json")
OUT_PATH = Path("app/data/legacy_kb_shortlist.json")

rows = json.loads(IN_PATH.read_text(encoding="utf-8"))

keep_categories = {"complaints", "eligibility", "service_coverage", "faq", "routing"}

shortlist = []
for r in rows:
    if "id" not in r:
        continue
    if r.get("runtime_enabled") is not True:
        continue
    if r.get("card_kind") != "citizen_runtime":
        continue
    if r.get("category") not in keep_categories:
        continue

    useful_signal = (
        r.get("has_required_fields")
        or r.get("has_answer_rules")
        or (r.get("category") == "faq")
        or (r.get("category") == "routing")
    )

    if not useful_signal:
        continue

    shortlist.append(r)

OUT_PATH.write_text(json.dumps(shortlist, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"WROTE {OUT_PATH}")
print(f"SHORTLIST_ROWS={len(shortlist)}")
