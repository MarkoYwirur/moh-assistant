import json, sys
from pathlib import Path
from fastapi.testclient import TestClient
ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from main import app
from router import get_top_candidates
phrases = '+repr(phrases)+'
client=TestClient(app)
out=[]
for phrase in phrases:
    top3=[{"id":c["card"].get("id"),"score":round(c["score"],4)} for c in get_top_candidates(phrase, top_k=3)]
    resp=client.post("/chat", json={"message":phrase,"state":{}}).json()
    out.append({"phrase":phrase,"top3":top3,"action":resp.get("action"),"matched":resp.get("matched_card_id"),"followup":resp.get("follow_up_question")})
print(json.dumps(out, ensure_ascii=False, indent=2))
