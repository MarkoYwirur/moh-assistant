import json
from pathlib import Path

root = Path(r"C:\Users\Asus\Desktop\moh-assistant\kb")

def load(path: Path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data, "list"
    return data["cards"], "dict"

def save(path: Path, cards, mode: str):
    payload = cards if mode == "list" else {"cards": cards}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

for path in root.glob("*.json"):
    cards, mode = load(path)
    changed = False

    for card in cards:
        if card.get("id") == "routing_specialist_referral_confusion_v1":
            card["priority"] = 130
            card["patterns"] = [
                "նեղ մասնագետի ուղեգիր",
                "մասնագետի ուղեգիր",
                "ուղեգիր նեղ մասնագետի համար",
                "պետք է ուղեգիր մասնագետի համար",
                "սրտաբանի ուղեգիր",
                "նյարդաբանի ուղեգիր",
                "ակնաբույժի ուղեգիր",
                "ուղեգիր մասնագետի մոտ",
                "specialist referral",
                "referral to specialist"
            ]
            changed = True

        if card.get("id") == "routing_referral_where_to_go_v2":
            card["priority"] = 170
            patterns = card.get("patterns", [])
            extra = [
                "ուր դիմեմ ուղեգիր ստանալու համար",
                "որտեղ ստանամ ուղեգիր",
                "ուղեգիր որտեղից ստանամ",
                "ուղեգիր ոնց ստանամ",
                "որտեղ գնամ ուղեգրի համար"
            ]
            merged = []
            for item in patterns + extra:
                if item not in merged:
                    merged.append(item)
            card["patterns"] = merged
            changed = True

    if changed:
        save(path, cards, mode)
        print(f"UPDATED {path.name}")

print("DONE")
