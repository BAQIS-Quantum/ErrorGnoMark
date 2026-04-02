import argparse
from pathlib import Path
from scanner import scan_paths
from git_utils import get_git_diff
from context_builder import build_context
from claude_client import call_claude

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Your architectural question")
    parser.add_argument(
        "--include",
        nargs="*",
        help="Specify folders or files to include",
    )
    args = parser.parse_args()

    root = Path.cwd()

    print("📂 Scanning selected paths...")
    project_text = scan_paths(root, args.include)

    print("🔍 Reading git diff...")
    git_diff = get_git_diff(root)

    print("🧠 Building context...")
    context = build_context(project_text, git_diff, args.prompt)

    print("🚀 Calling Claude...")
    result = call_claude(context)

    print("\n========== CLAUDE RESPONSE ==========\n")
    print(result)

if __name__ == "__main__":
    main()
