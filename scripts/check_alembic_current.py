from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
REVISION_RE = re.compile(r"^\s*(?P<revision>[A-Za-z0-9][A-Za-z0-9_]*)\b")
IGNORED_LINE_PREFIXES = ("DEBUG", "INFO", "WARNING", "WARN", "ERROR")


def parse_alembic_revisions(output: str) -> list[str]:
    revisions: list[str] = []

    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(IGNORED_LINE_PREFIXES):
            continue

        match = REVISION_RE.match(stripped)
        if not match:
            continue

        revision = match.group("revision")
        if revision.lower() in {"current", "heads", "rev"}:
            continue

        if revision not in revisions:
            revisions.append(revision)

    return revisions


def alembic_current_matches_heads(current_output: str, heads_output: str) -> bool:
    current_revisions = set(parse_alembic_revisions(current_output))
    head_revisions = set(parse_alembic_revisions(heads_output))

    return (
        bool(current_revisions)
        and bool(head_revisions)
        and current_revisions == head_revisions
    )


def _run_alembic(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["alembic", *args],
        cwd=BACKEND_DIR,
        check=False,
        capture_output=True,
        text=True,
    )


def _print_completed_process(
    command: str, result: subprocess.CompletedProcess[str]
) -> None:
    print(f"$ {command}")
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)


def _format_revisions(revisions: set[str]) -> str:
    return ", ".join(sorted(revisions)) if revisions else "<none>"


def main() -> int:
    current_result = _run_alembic(["current"])
    heads_result = _run_alembic(["heads"])

    _print_completed_process("alembic current", current_result)
    _print_completed_process("alembic heads", heads_result)

    if current_result.returncode != 0:
        print("alembic current failed", file=sys.stderr)
        return current_result.returncode
    if heads_result.returncode != 0:
        print("alembic heads failed", file=sys.stderr)
        return heads_result.returncode

    current_revisions = set(
        parse_alembic_revisions(f"{current_result.stdout}\n{current_result.stderr}")
    )
    head_revisions = set(
        parse_alembic_revisions(f"{heads_result.stdout}\n{heads_result.stderr}")
    )

    if not current_revisions:
        print("failed to parse Alembic current revision", file=sys.stderr)
        return 1
    if not head_revisions:
        print("failed to parse Alembic head revision", file=sys.stderr)
        return 1

    if not alembic_current_matches_heads(
        f"{current_result.stdout}\n{current_result.stderr}",
        f"{heads_result.stdout}\n{heads_result.stderr}",
    ):
        print(
            "Alembic current revision does not match heads: "
            f"current={_format_revisions(current_revisions)}, "
            f"heads={_format_revisions(head_revisions)}",
            file=sys.stderr,
        )
        return 1

    print(f"Alembic current revision matches heads: {_format_revisions(head_revisions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
