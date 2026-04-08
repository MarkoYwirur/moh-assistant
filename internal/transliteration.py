LATIN_ARMENIAN_MAP = [
    ("shch", "շճ"),
    ("vo", "ո"),
    ("ev", "և"),
    ("ts", "ց"),
    ("dz", "ձ"),
    ("gh", "ղ"),
    ("ch", "չ"),
    ("sh", "շ"),
    ("zh", "ժ"),
    ("kh", "խ"),
    ("th", "թ"),
    ("ph", "փ"),
    ("u", "ու")
]

SINGLE_CHAR_MAP = {
    "a": "ա",
    "b": "բ",
    "g": "գ",
    "d": "դ",
    "e": "ե",
    "z": "զ",
    "i": "ի",
    "l": "լ",
    "x": "խ",
    "c": "կ",
    "h": "հ",
    "j": "ջ",
    "m": "մ",
    "y": "յ",
    "n": "ն",
    "o": "ո",
    "p": "պ",
    "r": "ր",
    "s": "ս",
    "t": "տ",
    "v": "վ",
    "w": "վ",
    "q": "ք",
    "f": "ֆ"
}

COMMON_PHRASE_OVERRIDES = {
    "ur dimem": "ուր դիմեմ",
    "uxegir": "ուղեգիր",
    "stanalu hamar": "ստանալու համար",
    "inch anem": "ինչ անեմ",
    "degh": "դեղ",
    "petutyun": "պետություն",
    "anvjar": "անվճար",
    "mrt": "մռտ",
    "kt": "կտ",
    "chi erevum": "չի երևում",
    "armed": "արմեդ",
    "mjerel en": "մերժել են",
    "gumar": "գումար",
    "vchar": "վճար",
    "masnaget": "մասնագետ"
}

def transliterate_latin_armenian(text: str) -> str:
    if not text:
        return text

    lowered = text.lower()

    if not any("a" <= ch <= "z" for ch in lowered):
        return text

    for src, dst in COMMON_PHRASE_OVERRIDES.items():
        lowered = lowered.replace(src, dst)

    result = []
    i = 0
    while i < len(lowered):
        matched = False

        for src, dst in LATIN_ARMENIAN_MAP:
            if lowered[i:i+len(src)] == src:
                result.append(dst)
                i += len(src)
                matched = True
                break

        if matched:
            continue

        ch = lowered[i]
        if ch in SINGLE_CHAR_MAP:
            result.append(SINGLE_CHAR_MAP[ch])
        else:
            result.append(ch)
        i += 1

    return "".join(result)
