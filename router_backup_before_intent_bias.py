import json
import re
from transliteration import transliterate_latin_armenian
from intent_refiner import detect_refined_intent
from functools import lru_cache
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
KB_DIR = PROJECT_DIR / "kb"

YES_WORDS = {
    "այո",
    "ունեմ",
    "կա",
    "yes",
    "have",
    "has",
}

NO_WORDS = {
    "ոչ",
    "չունեմ",
    "չկա",
    "no",
    "dont",
    "don't",
    "not",
}

CATEGORY_HINTS = {
    "medicines": [
        "դեղ",
        "դեղորայք",
        "դեղամիջոց",
        "աբիրատերոն",
        "abiraterone",
        "tablet",
        "mg",
        "մգ",
        "capsule",
        "caps",
        "սուբսիդ",
        "անվճար",
        "ծածկ",
    ],
    "service_coverage": [
        "մռտ",
        "mri",
        "մագնիսառեզոնանսային",
        "կտ",
        "ct",
        "հետազոտ",
        "ախտորոշ",
        "լաբորատոր",
        "անալիզ",
        "ուղեգիր",
        "ծածկ",
        "անվճար",
        "վճար",
        "համավճար",
    ],
    "eligibility": [
        "ովքեր",
        "իրավունք",
        "իրավասու",
        "խումբ",
        "սոցիալական",
        "eligible",
        "eligibility",
        "benefit",
    ],
    "complaints": [
        "բողոք",
        "մերժել",
        "գումար ուզել",
        "պահանջել",
        "չեն սպասարկել",
        "չեն տվել",
        "խախտում",
        "dispute",
        "complaint",
    ],
    "routing": [
        "որտեղ գնամ",
        "ուր դիմեմ",
        "ով պետք է",
        "պոլիկլինիկա",
        "ընտանեկան բժիշկ",
        "ուղեգիր",
        "which clinic",
        "where should i go",
    ],
    "faq": [
        "8003",
        "նախարարություն",
        "moh",
        "մոհ",
        "տեղեկանք",
        "փաստաթուղթ",
        "info",
        "հաճախ տրվող",
    ],
}

STRONG_DOMAIN_TERMS = {
    "service_coverage": {"մռտ", "mri", "կտ", "ct", "ուղեգիր", "հետազոտ", "ախտորոշ"},
    "medicines": {"դեղ", "դեղորայք", "դեղամիջոց", "աբիրատերոն", "abiraterone", "մգ", "tablet", "capsule"},
    "complaints": {"բողոք", "մերժել", "պահանջել", "գումար", "խախտում"},
    "routing": {"որտեղ", "ուր", "դիմեմ", "պոլիկլինիկա", "բժիշկ"},
    "eligibility": {"իրավունք", "իրավասու", "խումբ", "սոցիալական"},
    "faq": {"8003", "նախարարություն", "մոհ", "տեղեկանք"},
}


def normalize_text(text: str) -> str:
    if text is None:
        return ""

    text = transliterate_latin_armenian(text)
    text = text.lower().strip()
    text = text.replace("?", "??")
    text = text.replace("?", " ")
    text = text.replace("?", " ")
    text = text.replace("?", " ")
    text = text.replace("?", " ")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _load_json_file(file_path: Path) -> list:
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    if isinstance(content, list):
        cards = content
    elif isinstance(content, dict) and isinstance(content.get("cards"), list):
        cards = content["cards"]
    else:
        cards = []

    cleaned = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        card_copy = dict(card)
        card_copy["_source_file"] = file_path.name
        cleaned.append(card_copy)

    return cleaned


@lru_cache(maxsize=1)
def load_all_cards() -> list:
    cards = []
    if not KB_DIR.exists():
        return cards

    for file_path in sorted(KB_DIR.glob("*.json")):
        try:
            cards.extend(_load_json_file(file_path))
        except Exception as e:
            print(f"ERROR loading {file_path}: {e}")

    return cards


@lru_cache(maxsize=1)
def get_card_index() -> dict:
    index = {}
    for card in load_all_cards():
        card_id = card.get("id")
        if card_id:
            index[card_id] = card
    return index


def get_card_by_id(card_id: str) -> dict | None:
    if not card_id:
        return None
    return get_card_index().get(card_id)


def _pattern_score(pattern: str, text: str) -> float:
    pattern_norm = normalize_text(pattern)
    if not pattern_norm or not text:
        return 0.0

    if text == pattern_norm:
        return 7.0

    if pattern_norm in text:
        return 4.0

    pattern_tokens = set(pattern_norm.split())
    text_tokens = set(text.split())

    if not pattern_tokens:
        return 0.0

    overlap = len(pattern_tokens & text_tokens)
    if overlap == 0:
        return 0.0

    return 1.0 + (overlap / max(1, len(pattern_tokens)))


def _category_hint_score(category: str, text: str) -> float:
    hints = CATEGORY_HINTS.get(category, [])
    score = 0.0
    for hint in hints:
        if normalize_text(hint) in text:
            score += 0.5
    return score


def _strong_domain_bonus(card: dict, text: str) -> float:
    category = card.get("category", "")
    terms = STRONG_DOMAIN_TERMS.get(category, set())
    if not terms:
        return 0.0

    text_tokens = set(text.split())
    overlap = len(text_tokens & terms)

    if overlap == 0:
        return 0.0

    return overlap * 2.0


def _faq_penalty(card: dict, text: str) -> float:
    category = card.get("category", "")
    if category != "faq":
        return 0.0

    service_terms = STRONG_DOMAIN_TERMS["service_coverage"]
    medicine_terms = STRONG_DOMAIN_TERMS["medicines"]
    complaint_terms = STRONG_DOMAIN_TERMS["complaints"]

    text_tokens = set(text.split())

    if text_tokens & service_terms:
        return -3.0
    if text_tokens & medicine_terms:
        return -3.0
    if text_tokens & complaint_terms:
        return -2.0

    return 0.0


def score_card(card: dict, user_text: str) -> float:
    text = normalize_text(user_text)
    if not text:
        return 0.0

    score = 0.0

    patterns = card.get("patterns", [])
    for pattern in patterns:
        score += _pattern_score(pattern, text)

    category = card.get("category", "")
    score += _category_hint_score(category, text)
    score += _strong_domain_bonus(card, text)
    score += _faq_penalty(card, text)

    priority = card.get("priority", 0)
    try:
        score += float(priority) / 1000.0
    except Exception:
        pass

    return round(score, 4)


def get_top_candidates(user_text: str, top_k: int = 5, forced_card: dict | None = None) -> list:
    if forced_card is not None:
        return [{"card": forced_card, "score": 99.0}]

    scored = []
    for card in load_all_cards():
        score = score_card(card, user_text)
        if score > 0:
            scored.append({"card": card, "score": score})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def _match_field_values_from_card(field_name: str, user_text: str, card: dict | None) -> str | None:
    if not card:
        return None

    field_values = card.get("field_values", {})
    options = field_values.get(field_name)

    if not isinstance(options, dict):
        return None

    text = normalize_text(user_text)

    for canonical_value, aliases in options.items():
        candidates = [canonical_value]
        if isinstance(aliases, list):
            candidates.extend(aliases)
        elif isinstance(aliases, str):
            candidates.append(aliases)

        for candidate in candidates:
            if normalize_text(candidate) in text:
                return canonical_value

    return None


def coerce_field_value(field_name: str, user_text: str, card: dict | None = None):
    text = normalize_text(user_text)

    matched_from_card = _match_field_values_from_card(field_name, user_text, card)
    if matched_from_card is not None:
        return matched_from_card

    if field_name == "referral_status":
        if "ուղեգիր ունեմ" in text:
            return "has_referral"
        if "ուղեգիր չունեմ" in text:
            return "no_referral"
        if any(word in text.split() for word in YES_WORDS):
            return "has_referral"
        if any(word in text.split() for word in NO_WORDS):
            return "no_referral"

    if field_name.startswith("has_") or field_name.endswith("_available"):
        if any(word in text.split() for word in YES_WORDS):
            return "yes"
        if any(word in text.split() for word in NO_WORDS):
            return "no"

    if text:
        return user_text.strip()

    return None


def should_continue_pending_flow(user_text: str, pending_field: str | None) -> bool:
    text = normalize_text(user_text)
    if not text:
        return False

    tokens = text.split()
    if len(tokens) <= 5:
        return True

    if any(word in tokens for word in YES_WORDS):
        return True

    if any(word in tokens for word in NO_WORDS):
        return True

    if pending_field and normalize_text(pending_field) in text:
        return True

    if pending_field == "referral_status" and "ուղեգիր" in text:
        return True

    return False
