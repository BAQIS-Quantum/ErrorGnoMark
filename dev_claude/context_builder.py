import tiktoken
from config import MAX_CONTEXT_TOKENS

def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def build_context(project_text: str, git_diff: str, user_prompt: str) -> str:
    base_context = f"""
You are a senior software architect.

PROJECT SNAPSHOT:
{project_text}

GIT DIFF:
{git_diff}

USER REQUEST:
{user_prompt}
"""

    tokens = count_tokens(base_context)

    if tokens > MAX_CONTEXT_TOKENS:
        project_text = project_text[: int(len(project_text) * 0.6)]
        return build_context(project_text, git_diff, user_prompt)

    return base_context
