import sys
from pathlib import Path
ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from router import get_top_candidates, normalize_text
from decision_engine import _is_admission_coverage_safety_override, is_safety_case
for phrase in ['ստացիոնար բուժումը անվճա՞ր է','շտապ վիրահատությունը անվճա՞ր է']:
    cands = get_top_candidates(phrase, top_k=3)
    print(phrase)
    print('normalized=', normalize_text(phrase))
    print('top=', cands[0]['card'].get('id') if cands else None, cands[0]['score'] if cands else None)
    print('safety=', is_safety_case(phrase))
    print('override=', _is_admission_coverage_safety_override(phrase, cands))
