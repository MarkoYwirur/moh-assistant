import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(r"C:\Users\Asus\Desktop\moh-assistant\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "requests.jsonl"


def append_request_log(payload: dict):
    row = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **payload
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
