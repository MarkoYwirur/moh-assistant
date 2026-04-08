import json
import re
from pathlib import Path

BASE = Path(r"C:\Users\Asus\Desktop\moh-assistant")
KB = BASE / "kb"

REQUIRED_CARD_FIELDS = ["id", "category", "patterns", "priority"]
CONDITIONAL_REQUIRED_FIELDS = [
    "required_fields",
    "field_questions",
    "answer_rules"
]

ULTRA_BROAD_PATTERN_DENYLIST = {
    "բողոք",
    "համավճար",
    "ուր դիմեմ",
    "որտեղ գնամ",
    "մասնագետ",
    "specialist",
    "պոլիկլինիկա",
    "աշխատող",
    "երեխա",
    "https",
}


def load_cards(path: Path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        return data["cards"]
    raise ValueError(f"Unsupported JSON structure in {path.name}")


def is_runtime_enabled(card: dict) -> bool:
    return card.get("runtime_enabled", True) is not False


def normalize_pattern(value: str) -> str:
    text = str(value or "").lower().strip()
    text = re.sub(r"[^\w\s\+\-/]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tree_signature(card: dict) -> tuple:
    required_fields = card.get("required_fields", [])
    field_questions = card.get("field_questions", {})
    field_values = card.get("field_values", {})
    return (
        str(card.get("category", "") or "").strip().lower(),
        tuple(sorted(str(x) for x in required_fields)) if isinstance(required_fields, list) else (),
        tuple(sorted(str(x) for x in field_questions.keys())) if isinstance(field_questions, dict) else (),
        tuple(sorted(str(x) for x in field_values.keys())) if isinstance(field_values, dict) else (),
    )


def main():
    all_ids = {}
    errors = []
    total_cards = 0
    runtime_patterns = {}
    runtime_tree_signatures = {}

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
            elif is_runtime_enabled(card):
                for pattern in patterns:
                    normalized = normalize_pattern(pattern)
                    if not normalized:
                        continue

                    if normalized in ULTRA_BROAD_PATTERN_DENYLIST:
                        errors.append(
                            f"[ULTRA_BROAD_PATTERN] {prefix}: pattern '{pattern}' normalizes to '{normalized}'"
                        )

                    runtime_patterns.setdefault(normalized, []).append(
                        {"id": card.get("id"), "file": path.name, "pattern": pattern}
                    )

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

                if is_runtime_enabled(card):
                    runtime_tree_signatures.setdefault(tree_signature(card), []).append(
                        {"id": card.get("id"), "file": path.name}
                    )

    for normalized, matches in runtime_patterns.items():
        unique_cards = {(m["id"], m["file"]) for m in matches if m.get("id")}
        if len(unique_cards) > 1:
            refs = ", ".join(
                f"{m['id']} ({m['file']}, pattern='{m['pattern']}')" for m in matches
            )
            errors.append(f"[NORMALIZED_DUPLICATE_PATTERN] '{normalized}' appears across runtime cards: {refs}")

    for signature, matches in runtime_tree_signatures.items():
        unique_cards = {(m["id"], m["file"]) for m in matches if m.get("id")}
        if len(unique_cards) > 1:
            refs = ", ".join(f"{m['id']} ({m['file']})" for m in matches)
            errors.append(f"[COMPETING_RUNTIME_TREE] shared conditional signature {signature}: {refs}")

    print(f"TOTAL_CARDS={total_cards}")
    print(f"TOTAL_ERRORS={len(errors)}")

    for err in errors:
        print(err)

    if errors:
        raise SystemExit(1)

    print("KB_VALIDATION_OK")


if __name__ == "__main__":
    main()
