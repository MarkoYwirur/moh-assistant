import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

STYLE_RULES = json.loads((BASE / "style_rules.json").read_text(encoding="utf-8-sig"))
STYLE_LEXICON = json.loads((BASE / "style_lexicon.json").read_text(encoding="utf-8-sig"))
STYLE_TEMPLATES = json.loads((BASE / "style_templates.json").read_text(encoding="utf-8-sig"))


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


def render_style(payload: dict) -> str:
    answer_type = payload.get("answer_type", "direct_answer")
    category = payload.get("category", "")
    max_map = STYLE_RULES.get("length", {})
    max_sentences = {
        "direct_answer": max_map.get("max_sentences_direct", 2),
        "partial_answer_with_clarify": max_map.get("max_sentences_clarify", 2),
        "clarify": max_map.get("max_sentences_clarify", 2),
        "partial_answer_with_next_step": max_map.get("max_sentences_direct", 2),
        "escalate_true_gap": max_map.get("max_sentences_escalation", 2),
        "escalate_safety": max_map.get("max_sentences_escalation", 2),
    }.get(answer_type, 2)

    template = _template_parts(answer_type)

    field_map = {
        "policy_answer": payload.get("policy_answer", ""),
        "condition_note": payload.get("condition_note", ""),
        "partial_answer": payload.get("partial_answer", ""),
        "next_step": payload.get("next_step", ""),
        "follow_up_question": payload.get("follow_up_question", ""),
        "gap_reason_text": payload.get("gap_reason_text", ""),
        "safety_text": payload.get("safety_text", "")
    }

    parts = []
    for item in template:
        parts.append(item.format(**field_map))

    text = " ".join(_sentence(part) for part in parts if _clean(part))
    text = _apply_lexicon(text)
    text = _limit_sentences(text, max_sentences=max_sentences)

    preferred_openers = STYLE_LEXICON.get("preferred_openers", {}).get(category, [])
    if preferred_openers and payload.get("force_preferred_opener") and text:
        opener = preferred_openers[0]
        if not text.startswith(opener):
            text = _sentence(opener + " " + text)

    return text
