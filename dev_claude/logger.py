import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.cwd() / "ai_logs" / "raw"

def get_today_logfile():
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"{today}.log"

def ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_interaction(prompt, response):
    ensure_log_dir()
    logfile = get_today_logfile()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "response": response
    }

    with open(logfile, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False))
        f.write("\n")
