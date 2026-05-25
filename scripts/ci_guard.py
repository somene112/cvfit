from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import PurePosixPath


FORBIDDEN_TRACKED_PATTERNS = (
    "*.pyc",
    "*.dir.tar.gz",
)

FORBIDDEN_TRACKED_PARTS = (
    ".env",
    "__pycache__",
    "pytest-cache-files-local",
)


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _is_forbidden(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if any(part in FORBIDDEN_TRACKED_PARTS for part in parts):
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in FORBIDDEN_TRACKED_PATTERNS)


def main() -> int:
    forbidden = sorted(path for path in _tracked_files() if _is_forbidden(path))
    if forbidden:
        print("Tracked generated or secret-like files are not allowed:", file=sys.stderr)
        for path in forbidden:
            print(f"  {path}", file=sys.stderr)
        return 1

    print("ci_guard: tracked generated/secret-like file check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
