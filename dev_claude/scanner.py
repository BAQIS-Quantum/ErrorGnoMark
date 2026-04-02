from pathlib import Path
from config import EXCLUDE_DIRS

SUPPORTED_EXTENSIONS = {".py", ".ts", ".js", ".md", ".yaml", ".yml"}

def scan_paths(root: Path, include_paths=None) -> str:
    content = ""

    if include_paths is None or len(include_paths) == 0:
        include_paths = ["src"] if (root / "src").exists() else ["."]
    
    for rel_path in include_paths:
        base_path = (root / rel_path).resolve()

        if not base_path.exists():
            continue

        paths = [base_path] if base_path.is_file() else base_path.rglob("*")

        for path in paths:
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue

            if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
                try:
                    file_text = path.read_text(encoding="utf-8")
                    content += f"\n\n# FILE: {path}\n{file_text}"
                except:
                    continue

    return content
