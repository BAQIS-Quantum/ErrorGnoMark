import os
import sys
from anthropic import Anthropic
from config import MODEL
from logger import log_interaction

def call_claude(prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Please set ANTHROPIC_API_KEY")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        temperature=0.2,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    full_response_text = ""
    for block in response.content:
        if block.type == "text":
            full_response_text += block.text

    # ✅ 原始完整记录
    log_interaction(prompt, full_response_text)

    return full_response_text
