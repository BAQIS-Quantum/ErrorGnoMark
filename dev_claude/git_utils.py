from git import Repo, InvalidGitRepositoryError
from pathlib import Path

def get_git_diff(root: Path) -> str:
    try:
        repo = Repo(root)
        return repo.git.diff()
    except InvalidGitRepositoryError:
        return ""
