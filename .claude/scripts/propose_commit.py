#!/usr/bin/env python3
"""Propose Conventional Commits grouped by category, so that code, tests,
documentation and configuration do not land in the same commit.

    python3 .claude/scripts/propose_commit.py            # print the proposal
    python3 .claude/scripts/propose_commit.py --apply    # ask, then stage group by group

Deterministic, no LLM: the type is inferred from the paths; title and body are
left to be written, which is where judgement belongs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Order matters: the first matching pattern wins.
RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("TESTS", "test", ("tests/", "test/", "spec/", "_test.py", ".test.ts", ".spec.ts")),
    ("DOCS", "docs", (".md", "docs/", "CLAUDE.md", "LICENSE")),
    ("CI", "ci", (".github/", ".gitlab-ci", "azure-pipelines")),
    (
        "CONFIG",
        "chore",
        (
            ".claude/",
            ".githooks/",
            ".gitignore",
            ".gitattributes",
            ".editorconfig",
            "pyproject.toml",
            "setup.cfg",
            "requirements",
            "package.json",
            "package-lock",
            "uv.lock",
            "poetry.lock",
            "tsconfig.json",
            "Makefile",
            "Dockerfile",
            ".env.example",
        ),
    ),
]
DEFAULT_CATEGORY = ("CODE", "feat")


def changed_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("propose_commit: not a git repository (or git is not available).")
        return []
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip('"'))
    return paths


def category(path: str) -> tuple[str, str]:
    normalised = path.replace("\\", "/")
    for name, kind, patterns in RULES:
        if any(p in normalised or normalised.endswith(p) for p in patterns):
            return name, kind
    return DEFAULT_CATEGORY


def common_scope(paths: list[str]) -> str:
    """The first directory segment shared by every file, if there is one."""
    firsts = {p.replace("\\", "/").split("/")[0] for p in paths if "/" in p}
    if len(firsts) == 1:
        only = firsts.pop()
        if only not in {".claude", ".github", ".githooks", "docs", "tests", "src"}:
            return only
    return ""


def main() -> int:
    apply = "--apply" in sys.argv
    paths = changed_files()
    if not paths:
        print("propose_commit: nothing to commit.")
        return 0

    groups: dict[tuple[str, str], list[str]] = {}
    for path in paths:
        groups.setdefault(category(path), []).append(path)

    order = ["CODE", "TESTS", "DOCS", "CONFIG", "CI"]
    keys = sorted(groups, key=lambda k: order.index(k[0]) if k[0] in order else 99)

    print(f"{len(paths)} changed files, {len(keys)} commits proposed.\n")
    commands: list[list[str]] = []
    for index, (name, kind) in enumerate(keys, start=1):
        files = sorted(groups[(name, kind)])
        scope = common_scope(files)
        header = f"{kind}({scope}): <title>" if scope else f"{kind}: <title>"
        print(f"--- commit {index}/{len(keys)} - {name} ---")
        print(f"  message: {header}")
        print("  body:    <the why, not the what>")
        for f in files:
            print(f"    - {f}")
        print()
        commands.append(["git", "add", "--", *files])

    print("First line <= 72 characters. The why goes in the body, not in the CHANGELOG.")
    if not apply:
        print("\nRe-run with --apply to stage group by group.")
        return 0

    print()
    for index, command in enumerate(commands, start=1):
        answer = input(f"Stage group {index}? [y/N] ").strip().lower()
        if answer == "y":
            subprocess.run(command, cwd=ROOT, check=False)
            print(f"  staged. Now: git commit  (message: group {index})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
