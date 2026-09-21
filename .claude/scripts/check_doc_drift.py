#!/usr/bin/env python3
"""Advisory check for documentation drift: broken relative markdown links and
template placeholders (`<<...>>`) left behind.

    python3 .claude/scripts/check_doc_drift.py            # the whole repository
    python3 .claude/scripts/check_doc_drift.py --staged   # only the staged .md files

Never blocks: prints and always returns 0. It is a nudge, not a gate.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".obsidian", "dist", "build"}

# [text](target) - images ![...](...) are excluded by the lookbehind
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
PLACEHOLDER_RE = re.compile(r"<<[^<>\n]{1,120}>>")


def markdown_files(staged_only: bool) -> list[Path]:
    if staged_only:
        try:
            out = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
        return [ROOT / r for r in out.split() if r.endswith(".md") and (ROOT / r).is_file()]
    return [p for p in ROOT.rglob("*.md") if not IGNORED.intersection(p.relative_to(ROOT).parts)]


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#", "<"))


def resolve(source: Path, target: str) -> Path:
    path = target.split("#", 1)[0].split("?", 1)[0].strip()
    path = path.strip("<>").replace("%20", " ")
    return (source.parent / path).resolve()


def main() -> int:
    staged_only = "--staged" in sys.argv
    documents = markdown_files(staged_only)

    broken: list[str] = []
    placeholders: list[str] = []

    for doc in documents:
        try:
            text = doc.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = doc.relative_to(ROOT)
        in_fence = False

        for number, line in enumerate(text.splitlines(), start=1):
            # Fenced blocks hold examples and templates: skip them, or every
            # example path would count as a broken link.
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            for target in LINK_RE.findall(line):
                if is_external(target) or not target.split("#")[0].strip():
                    continue
                if "<<" in target:  # placeholder not filled in yet
                    continue
                if not resolve(doc, target).exists():
                    broken.append(f"  {rel}:{number}  ->  {target}")
            for found in dict.fromkeys(PLACEHOLDER_RE.findall(line)):
                short = found if len(found) <= 60 else found[:57] + "...>>"
                placeholders.append(f"  {rel}:{number}  {short}")

    if broken:
        print(f"[doc-drift] {len(broken)} broken relative links:")
        print("\n".join(broken[:40]))
        if len(broken) > 40:
            print(f"  ... and {len(broken) - 40} more")

    if placeholders:
        print(f"[doc-drift] {len(placeholders)} template placeholders still to fill in:")
        print("\n".join(placeholders[:20]))
        if len(placeholders) > 20:
            print(f"  ... and {len(placeholders) - 20} more")

    if not broken and not placeholders:
        print(f"[doc-drift] {len(documents)} markdown files checked, no problems.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
