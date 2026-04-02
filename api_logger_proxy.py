import os
import json
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

app = FastAPI()

LOG_DIR = Path("ai_logs")
LOG_DIR.mkdir(exist_ok=True)

def get_log_filename():
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    unique_id = str(uuid.uuid4())[:8]
    return LOG_DIR / f"{date_str}_{unique_id}.json"

@app.post("/{full_path:path}")
async def proxy(full_path: str, request: Request):
    raw_body = await request.body()

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{OPENAI_BASE_URL}/{full_path}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            content=raw_body,
            headers=headers
        )

    # 原始数据
    log_entry = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "endpoint": full_path,
        "request_raw": json.loads(raw_body.decode()),
        "response_raw": response.json()
    }

    log_file = get_log_filename()

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    return JSONResponse(content=response.json(), status_code=response.status_code)