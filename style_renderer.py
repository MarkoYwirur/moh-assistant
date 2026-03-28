import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

STYLE_RULES = json.loads((BASE / "style_rules.json").read_text(encoding="utf-8-sig"))
STYLE_LEXICON = json.loads((BASE / "style_lexicon.json").read_text(encoding="utf-8-sig"))
STYLE_TEMPLATES = json.loads((BASE / "style_templates.json").read_text(encoding="utf-8-sig"))
STYLE_EXAMPLES = json.loads((BASE / "style_examples.json").read_text(encoding="utf-8-sig"))
STYLE_PROFILE = json.loads((BASE / "style_profile.json").read_text(encoding="utf-8-sig"))


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).strip().split())


def _sentence(text: str | None) -> str:
    text = _clean(text)
    if not text:
        return ""
    if text[-1] not in ".։!?՞":
        text += "։"
    return text


def _apply_lexicon(text: str) -> str:
    out = text

    for old, new in STYLE_LEXICON.get("preferred_rewrites", {}).items():
        out = out.replace(old, new)
        out = out.replace(old.capitalize(), new.capitalize())

    for phrase in STYLE_LEXICON.get("forbidden_phrases", []):
        out = out.replace(phrase, "")
        out = out.replace(phrase.capitalize(), "")

    out = " ".join(out.split())
    out = out.replace("։։", "։")
    out = out.replace("  ", " ")
    return out.strip()


def _limit_sentences(text: str, max_sentences: int) -> str:
    if not text:
        return ""
    normalized = text.replace("?", "։").replace("!", "։")
    parts = [p.strip() for p in normalized.split("։") if p.strip()]
    parts = parts[:max_sentences]
    if not parts:
        return ""
    return "։ ".join(parts) + "։"


def _template_parts(answer_type: str) -> list[str]:
    section = STYLE_TEMPLATES.get(answer_type, {})
    return section.get("default", [])


def _best_example(category: str, answer_type: str) -> str:
    for item in STYLE_EXAMPLES:
        if item.get("category") == category and item.get("answer_type") == answer_type:
            return _clean(item.get("text", ""))
    for item in STYLE_EXAMPLES:
        if item.get("answer_type") == answer_type:
            return _clean(item.get("text", ""))
    return ""


def _extract_question_style(example_text: str, fallback: str) -> str:
    parts = [p.strip() for p in example_text.split("։") if p.strip()]
    if parts:
        last_part = parts[-1]
        if "՞" in last_part:
            return last_part
    return fallback


def _extract_opening_style(example_text: str, fallback: str) -> str:
    parts = [p.strip() for p in example_text.split("։") if p.strip()]
    if parts:
        return parts[0]
    return fallback


def _polish_question(text: str) -> str:
    if not text:
        return text

    starters = STYLE_PROFILE.get("preferred_patterns", {}).get("clarifying_question", [])
    if starters:
        if not any(text.startswith(s) for s in starters):
            if text.startswith("Նշեք"):
                return text
            return starters[0] + "՝ " + text[0].lower() + text[1:] if len(text) > 1 else starters[0]

    return text


def render_style(payload: dict) -> str:
    answer_type = payload.get("answer_type", "direct_answer")
    category = payload.get("category", "")
    max_map = STYLE_RULES.get("length", {})
    max_sentences = {
        "direct_answer": max_map.get("max_sentences_direct", 2),
        "partial_answer_with_clarify": max_map.get("max_sentences_clarify", 2),
        "clarify": max_map.get("max_sentences_clarify", 1),
        "partial_answer_with_next_step": max_map.get("max_sentences_direct", 2),
        "escalate_true_gap": max_map.get("max_sentences_escalation", 2),
        "escalate_safety": max_map.get("max_sentences_escalation", 2),
    }.get(answer_type, 2)

    template = _template_parts(answer_type)
    example_text = _best_example(category, answer_type)

    field_map = {
        "policy_answer": payload.get("policy_answer", ""),
        "condition_note": payload.get("condition_note", ""),
        "partial_answer": payload.get("partial_answer", ""),
        "next_step": payload.get("next_step", ""),
        "follow_up_question": payload.get("follow_up_question", ""),
        "gap_reason_text": payload.get("gap_reason_text", ""),
        "safety_text": payload.get("safety_text", "")
    }

    if answer_type in {"clarify", "partial_answer_with_clarify"}:
        field_map["follow_up_question"] = _extract_question_style(example_text, field_map["follow_up_question"])
        field_map["follow_up_question"] = _polish_question(field_map["follow_up_question"])

    if answer_type == "direct_answer" and field_map["policy_answer"]:
        field_map["policy_answer"] = _extract_opening_style(example_text, field_map["policy_answer"])

    if answer_type == "partial_answer_with_clarify" and field_map["partial_answer"]:
        field_map["partial_answer"] = _extract_opening_style(example_text, field_map["partial_answer"])

    if answer_type == "partial_answer_with_next_step" and field_map["partial_answer"]:
        field_map["partial_answer"] = _extract_opening_style(example_text, field_map["partial_answer"])

    if answer_type == "escalate_true_gap" and field_map["gap_reason_text"]:
        field_map["gap_reason_text"] = _extract_opening_style(example_text, field_map["gap_reason_text"])

    parts = []
    for item in template:
        value = item.format(**field_map)
        if _clean(value):
            parts.append(_sentence(value))

    text = " ".join(parts)
    text = _apply_lexicon(text)
    text = _limit_sentences(text, max_sentences=max_sentences)

    return text
