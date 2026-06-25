from pathlib import Path


def find_git_root() -> Path:
    """
    Traverses upwards from the current working directory to find the Git root.
    Falls back to the current working directory if no Git repository is detected.
    """
    # Start at the absolute current working directory
    current_dir = Path.cwd().resolve()

    # Check the current directory, then walk up through all parent directories
    for path in [current_dir] + list(current_dir.parents):
        if (path / ".git").exists():
            return path

    # Fallback if we hit the filesystem root without finding a .git marker
    return Path.cwd()
