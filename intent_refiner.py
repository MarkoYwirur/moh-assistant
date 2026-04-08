import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
REFINERS = json.loads((BASE / "intent_refiners.json").read_text(encoding="utf-8-sig"))


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(p in text for p in phrases)


def detect_refined_intent(normalized_text: str) -> dict:
    result = {
        "medicine_mode": None,
        "payment_mode": None,
        "routing_mode": None,
        "signals": []
    }

    medicine_modes = REFINERS.get("medicine_question_modes", {})
    payment_modes = REFINERS.get("payment_question_modes", {})
    routing_modes = REFINERS.get("routing_modes", {})

    for mode, phrases in medicine_modes.items():
        if _contains_any(normalized_text, phrases):
            result["medicine_mode"] = mode
            result["signals"].append(f"medicine:{mode}")
            break

    for mode, phrases in payment_modes.items():
        if _contains_any(normalized_text, phrases):
            result["payment_mode"] = mode
            result["signals"].append(f"payment:{mode}")
            break

    for mode, phrases in routing_modes.items():
        if _contains_any(normalized_text, phrases):
            result["routing_mode"] = mode
            result["signals"].append(f"routing:{mode}")
            break

    return result
