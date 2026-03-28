import json
from pathlib import Path

BASE = Path(r"C:\Users\Asus\Desktop\moh-assistant")
KB = BASE / "kb"

REQUIRED_CARD_FIELDS = ["id", "category", "patterns", "priority"]
CONDITIONAL_REQUIRED_FIELDS = [
    "required_fields",
    "field_questions",
    "answer_rules"
]


def load_cards(path: Path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        return data["cards"]
    raise ValueError(f"Unsupported JSON structure in {path.name}")


def main():
    all_ids = {}
    errors = []
    total_cards = 0

    for path in sorted(KB.glob("*.json")):
        try:
            cards = load_cards(path)
        except Exception as e:
            errors.append(f"[FILE_ERROR] {path.name}: {e}")
            continue

        if not isinstance(cards, list):
            errors.append(f"[TYPE_ERROR] {path.name}: cards container is not a list")
            continue

        for index, card in enumerate(cards):
            total_cards += 1
            prefix = f"{path.name} | card_index={index}"

            if not isinstance(card, dict):
                errors.append(f"[CARD_TYPE] {prefix}: card is not an object")
                continue

            for field in REQUIRED_CARD_FIELDS:
                if field not in card:
                    errors.append(f"[MISSING_FIELD] {prefix}: missing {field}")

            card_id = card.get("id")
            if card_id:
                if card_id in all_ids:
                    errors.append(f"[DUPLICATE_ID] {prefix}: duplicate id {card_id} also in {all_ids[card_id]}")
                else:
                    all_ids[card_id] = path.name

            patterns = card.get("patterns")
            if patterns is None or not isinstance(patterns, list) or len(patterns) == 0:
                errors.append(f"[BAD_PATTERNS] {prefix}: patterns missing or empty")

            answer_type = card.get("allowed_answer_type")
            if answer_type == "conditional":
                for field in CONDITIONAL_REQUIRED_FIELDS:
                    if field not in card:
                        errors.append(f"[BAD_CONDITIONAL] {prefix}: missing {field}")

                required_fields = card.get("required_fields", [])
                field_questions = card.get("field_questions", {})
                answer_rules = card.get("answer_rules", [])

                if not isinstance(required_fields, list):
                    errors.append(f"[BAD_REQUIRED_FIELDS] {prefix}: required_fields is not a list")

                if not isinstance(field_questions, dict):
                    errors.append(f"[BAD_FIELD_QUESTIONS] {prefix}: field_questions is not an object")

                if not isinstance(answer_rules, list) or len(answer_rules) == 0:
                    errors.append(f"[BAD_ANSWER_RULES] {prefix}: answer_rules missing or empty")

                if isinstance(required_fields, list) and isinstance(field_questions, dict):
                    for req in required_fields:
                        if req not in field_questions:
                            errors.append(f"[MISSING_FIELD_QUESTION] {prefix}: missing question for {req}")

                if isinstance(answer_rules, list):
                    for rule_index, rule in enumerate(answer_rules):
                        if not isinstance(rule, dict):
                            errors.append(f"[BAD_RULE] {prefix}: rule {rule_index} is not an object")
                            continue
                        if "when" not in rule:
                            errors.append(f"[BAD_RULE] {prefix}: rule {rule_index} missing when")
                        if "answer" not in rule:
                            errors.append(f"[BAD_RULE] {prefix}: rule {rule_index} missing answer")

    print(f"TOTAL_CARDS={total_cards}")
    print(f"TOTAL_ERRORS={len(errors)}")

    for err in errors:
        print(err)

    if errors:
        raise SystemExit(1)

    print("KB_VALIDATION_OK")


if __name__ == "__main__":
    main()
