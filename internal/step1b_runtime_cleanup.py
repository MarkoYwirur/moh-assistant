from pathlib import Path
import json
import re
import shutil

KB_DIR = Path("kb")
BACKUP_DIR = Path("kb_step1b_backup")

ROUTING_ALLOWLIST = {
    "routing_referral_where_to_go_v2",
    "routing_specialist_referral_confusion_v1",
}

META_ID_PATTERNS = [
    r"executive_summary",
    r"official_sources",
    r"navigation_logic",
    r"card_ready",
    r"missing_operational_details",
    r"cross_verification",
    r"_sources$",
    r"_source$",
    r"_summary$",
    r"_matrix$",
]

def is_meta_id(card_id: str) -> bool:
    cid = (card_id or "").lower()
    return any(re.search(p, cid) for p in META_ID_PATTERNS)

def patch_card(card: dict, file_name: str) -> dict:
    c = dict(card)
    cid = c.get("id", "")
    category = c.get("category", "")

    # normalize category drift
    if category == "complaint":
        category = "complaints"
    if category == "medicine":
        category = "medicines"
    c["category"] = category

    runtime_enabled = True
    card_kind = "citizen_runtime"

    # hard-disable obvious meta/research cards everywhere
    if is_meta_id(cid):
        runtime_enabled = False
        card_kind = "research_reference"

    # routing file: disable everything except explicit citizen runtime cards
    if file_name == "routing.json":
        if cid in ROUTING_ALLOWLIST or re.search(r"(_v\d+|_curated)$", cid):
            runtime_enabled = True
            card_kind = "citizen_runtime"
        else:
            runtime_enabled = False
            card_kind = "research_reference"

    c["runtime_enabled"] = runtime_enabled
    c["card_kind"] = card_kind
    return c

def main():
    BACKUP_DIR.mkdir(exist_ok=True)

    total = 0
    enabled = 0
    disabled = 0

    for path in sorted(KB_DIR.glob("*.json")):
        backup_path = BACKUP_DIR / path.name
        if not backup_path.exists():
            shutil.copy2(path, backup_path)

        data = json.loads(path.read_text(encoding="utf-8"))
        patched = []

        for card in data:
            total += 1
            pc = patch_card(card, path.name)
            if pc.get("runtime_enabled"):
                enabled += 1
            else:
                disabled += 1
            patched.append(pc)

        path.write_text(json.dumps(patched, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PATCHED {path.name}")

    print("-" * 60)
    print(f"TOTAL_CARDS={total}")
    print(f"RUNTIME_ENABLED={enabled}")
    print(f"RESEARCH_DISABLED={disabled}")
    print(f"BACKUP_DIR={BACKUP_DIR.resolve()}")

if __name__ == '__main__':
    main()
