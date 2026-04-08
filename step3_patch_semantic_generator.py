from pathlib import Path

p = Path("semantic_generator.py")
t = p.read_text(encoding="utf-8")

old = """        payload["semantic"]["partial_answer"] = _build_partial_frame(card, collected_fields)
        payload["semantic"]["follow_up_question"] = _get_field_question(card, missing_field) if missing_field else "Կնշե՞ք ավելի կոնկրետ տվյալներ։"
        payload["semantic"]["why_this_question"] = _get_field_reason(missing_field)
"""

new = """        payload["semantic"]["partial_answer"] = _build_partial_frame(card, collected_fields)
        payload["semantic"]["follow_up_question"] = _get_field_question(card, missing_field) if missing_field else "Կնշե՞ք ավելի կոնկրետ տվյալներ։"
        payload["semantic"]["why_this_question"] = ""
"""

if old not in t:
    raise SystemExit("SEMANTIC_TARGET_NOT_FOUND")

t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("STEP3_SEMANTIC_PATCHED_OK")
