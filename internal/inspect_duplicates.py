import json
from collections import defaultdict
from pathlib import Path

KB = Path(r"C:\Users\Asus\Desktop\moh-assistant\kb")
groups = defaultdict(list)

for path in sorted(KB.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cards = data if isinstance(data, list) else data["cards"]

    for card in cards:
        category = card.get("category", "")
        patterns = tuple(sorted(card.get("patterns", [])))
        key = (category, patterns[:5])
        groups[key].append({
            "file": path.name,
            "id": card.get("id"),
            "priority": card.get("priority")
        })

for key, items in groups.items():
    if len(items) > 1:
        print("POSSIBLE_DUPLICATE_GROUP")
        print("KEY=", key)
        for item in items:
            print(item)
        print("---")
