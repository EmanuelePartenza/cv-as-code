#!/usr/bin/env python3
"""Refresh the automatic parts of STATUS.md: the date line and the last-commits table.

    python3 .claude/scripts/refresh_status.py

Invoked by the git post-commit hook. The manual sections (In progress, Blockers,
Next steps, ...) are never touched. Does not commit: STATUS.md is left modified
in the working tree and enters the next commit. If nothing changes, the file is
not rewritten (no hook loops). The date label may be English or Italian.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "STATUS.md"
N_COMMITS = 5

DATE_RE = re.compile(r"^\*\*(Updated|Aggiornato):\*\*.*$", re.MULTILINE)
BLOCK_RE = re.compile(r"(<!-- AUTO:COMMITS -->\n).*?(\n<!-- /AUTO:COMMITS -->)", re.DOTALL)


def last_commits(n: int) -> str:
    try:
        out = subprocess.run(
            ["git", "log", f"-{n}", "--pretty=format:%h\x1f%ad\x1f%s", "--date=short"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "_(git history not available)_"
    if not out:
        return "_(no commits)_"
    rows = ["| Hash | Date | Message |", "|---|---|---|"]
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        h, d, msg = parts
        safe = msg.replace("|", "\\|")  # no backslash inside an f-string: Python 3.10
        rows.append(f"| `{h}` | {d} | {safe} |")
    return "\n".join(rows)


def main() -> int:
    if not STATUS.exists():
        return 0
    original = STATUS.read_text(encoding="utf-8")
    updated = DATE_RE.sub(
        lambda m: f"**{m.group(1)}:** {date.today().isoformat()}", original, count=1
    )
    table = last_commits(N_COMMITS)
    if BLOCK_RE.search(updated):
        updated = BLOCK_RE.sub(lambda m: f"{m.group(1)}{table}{m.group(2)}", updated)
    if updated != original:
        STATUS.write_text(updated, encoding="utf-8")
        print("[status] STATUS.md refreshed (date + last commits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
