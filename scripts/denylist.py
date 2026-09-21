#!/usr/bin/env python3
"""Keyed denylist for the publication boundary (ADR-0009).

The maintainer keeps a plain-text list of strings that must never appear in this
repository (their own contact details, employer, clients, project code names)
OUTSIDE any repository, in ~/.config/cvac/denylist.txt. This tool turns it into
HMAC-SHA256 digests committed as tests/data/denylist.hmac; the key lives next
to the list and as a CI secret. Without the key the digests reveal nothing, and
low-entropy entries (a phone number, a date) cannot be brute-forced from them.

    scripts/denylist.py seed --profile <profile.yaml> [--add "phrase" ...]
        propose entries from a profile (contact details, employer names) and
        merge them into the plain-text list for the maintainer to review
    scripts/denylist.py build           write tests/data/denylist.hmac from the list
    scripts/denylist.py check [PATH…]   scan files (default: every tracked text file)
    scripts/denylist.py check-history   scan the whole git history (before going public)

Matching: text is NFKD-normalised, ASCII-folded and case-folded, split into
alphanumeric tokens; every 1- to 3-token n-gram is hashed, and so is every run
of digits (with separators removed) longer than five digits, so a phone number
survives any spacing. A denylist entry is hashed the same way. Only locations
are ever printed, never the matched text.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Iterator
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "cvac"
LIST_FILE = CONFIG_DIR / "denylist.txt"
KEY_FILE = CONFIG_DIR / "denylist.key"
KEY_ENV = "CVAC_DENYLIST_KEY"
HMAC_FILE = REPO / "tests" / "data" / "denylist.hmac"

MAX_NGRAM = 3
MIN_TOKEN_LEN = 3
MIN_DIGITS = 6
TOKEN_RE = re.compile(r"[^\W_]+")
DIGIT_RUN_RE = re.compile(r"\d[\d\s().+/-]{4,}\d")
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".txt",
    ".typ",
    ".sh",
    ".cfg",
    ".ini",
    ".csv",
}
EXEMPT = {"LICENSE", "src/cv_as_code/templates/fonts/OFL.txt"}


# --- normalisation and hashing ------------------------------------------------------------


def normalise(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return folded.casefold()


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(normalise(text))


def candidates(line: str) -> Iterator[str]:
    """Every hashable form a line contains: token n-grams and digit runs."""
    toks = tokens(line)
    for i in range(len(toks)):
        for k in range(1, MAX_NGRAM + 1):
            if i + k <= len(toks):
                yield " ".join(toks[i : i + k])
    for m in DIGIT_RUN_RE.finditer(line):
        digits = re.sub(r"\D", "", m.group())
        if len(digits) >= MIN_DIGITS:
            yield digits


def entry_forms(entry: str) -> set[str]:
    """The forms a denylist entry is hashed as: its token phrase and, if any, its digit string."""
    forms: set[str] = set()
    toks = tokens(entry)
    # A purely numeric entry (phone, date) is matched by its digit string only: a
    # 3-token prefix of it would also match unrelated numbers sharing that prefix.
    if toks and any(not t.isdigit() for t in toks):
        forms.add(" ".join(toks[:MAX_NGRAM]))
    digits = re.sub(r"\D", "", entry)
    if len(digits) >= MIN_DIGITS:
        forms.add(digits)
    return forms


def digest(key: bytes, item: str) -> str:
    return hmac.new(key, item.encode("utf-8"), hashlib.sha256).hexdigest()


def load_key() -> bytes | None:
    value = os.environ.get(KEY_ENV, "").strip()
    if not value and KEY_FILE.is_file():
        value = KEY_FILE.read_text("utf-8").strip()
    return value.encode("utf-8") if value else None


def load_digests(path: Path = HMAC_FILE) -> set[str]:
    if not path.is_file():
        return set()
    return {
        ln.strip()
        for ln in path.read_text("utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    }


# --- scanning -----------------------------------------------------------------------------


def scan_lines(lines: Iterable[tuple[str, int, str]], key: bytes, digests: set[str]) -> list[str]:
    """(where, line_no, text) triples -> locations of denylisted content, text never shown."""
    hits: list[str] = []
    for where, no, line in lines:
        if any(digest(key, c) in digests for c in candidates(line)):
            hits.append(f"{where}:{no}: denylisted content")
    return hits


def is_text_file(path: str) -> bool:
    return Path(path).suffix in TEXT_SUFFIXES and path not in EXEMPT


def file_lines(paths: Iterable[Path], base: Path) -> Iterator[tuple[str, int, str]]:
    for p in paths:
        try:
            text = p.read_text("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        where = str(p.relative_to(base)) if p.is_relative_to(base) else str(p)
        for no, line in enumerate(text.splitlines(), start=1):
            yield where, no, line


def scan_files(
    paths: Iterable[Path], key: bytes, digests: set[str], base: Path = REPO
) -> list[str]:
    return scan_lines(file_lines(paths, base), key, digests)


def tracked_text_files(repo: Path = REPO) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    return [repo / p for p in out.split("\0") if p and is_text_file(p)]


def history_lines(repo: Path = REPO) -> Iterator[tuple[str, int, str]]:
    log = subprocess.run(
        ["git", "log", "-p", "--all", "--format=commit %h%n%B"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        errors="replace",
    ).stdout
    commit = "?"
    for no, line in enumerate(log.splitlines(), start=1):
        if line.startswith("commit "):
            commit = line.split()[1]
        yield f"history {commit}", no, line


# --- commands -----------------------------------------------------------------------------


def _require_key() -> bytes:
    key = load_key()
    if key is None:
        sys.exit(f"denylist: no key - set {KEY_ENV} or create {KEY_FILE}")
    return key


def cmd_seed(args: argparse.Namespace) -> int:
    import yaml

    proposed: list[str] = []
    if args.profile:
        profile = yaml.safe_load(Path(args.profile).read_text("utf-8")) or {}
        ident = profile.get("identity") or {}
        for value in (ident.get("email"), ident.get("phone"), ident.get("born")):
            if value:
                proposed.append(str(value))
        born = str(ident.get("born") or "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", born):
            y, m, d = born.split("-")
            proposed += [f"{d}/{m}/{y}", f"{int(d)}/{int(m)}/{y}", f"{y}{m}{d}"]
        for exp in profile.get("experiences") or []:
            name = (exp.get("company") or {}).get("name")
            if name:
                proposed.append(name)
    proposed += args.add or []

    existing = (
        [ln.rstrip("\n") for ln in LIST_FILE.read_text("utf-8").splitlines()]
        if LIST_FILE.is_file()
        else []
    )
    known = {normalise(ln) for ln in existing if ln and not ln.startswith("#")}
    added: list[str] = []
    for entry in proposed:
        entry = entry.strip()
        if not entry or normalise(entry) in known:
            continue
        toks = tokens(entry)
        if not entry_forms(entry) or (
            len(toks) == 1
            and len(toks[0]) < MIN_TOKEN_LEN
            and len(re.sub(r"\D", "", entry)) < MIN_DIGITS
        ):
            print(f"  skipped (too short to be safe): {entry!r}")
            continue
        added.append(entry)
        known.add(normalise(entry))

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    header = (
        []
        if existing
        else [
            "# cv-as-code denylist: one entry per line; never commit this file.",
            "# Rebuild the digests with: scripts/denylist.py build",
        ]
    )
    LIST_FILE.write_text("\n".join(header + existing + added) + "\n", "utf-8")
    os.chmod(LIST_FILE, 0o600)
    noun = "entry" if len(added) == 1 else "entries"
    print(f"{len(added)} {noun} added to {LIST_FILE}; review it, then build")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    key = _require_key()
    if not LIST_FILE.is_file():
        sys.exit(f"denylist: {LIST_FILE} not found; run seed first")
    entries = [
        ln.strip()
        for ln in LIST_FILE.read_text("utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    forms: set[str] = set()
    for e in entries:
        forms |= entry_forms(e)
    digests = sorted(digest(key, f) for f in forms)
    HMAC_FILE.parent.mkdir(parents=True, exist_ok=True)
    HMAC_FILE.write_text(
        "# HMAC-SHA256 digests of the maintainer's denylist (ADR-0009). The key is not in\n"
        "# this repository; without it these lines reveal nothing. Rebuilt by\n"
        "# scripts/denylist.py build.\n" + "\n".join(digests) + "\n",
        "utf-8",
    )
    print(f"{len(entries)} entries -> {len(digests)} digests in {HMAC_FILE.relative_to(REPO)}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    key = _require_key()
    digests = load_digests()
    if not digests:
        sys.exit(f"denylist: {HMAC_FILE.relative_to(REPO)} is empty; run build")
    if args.stdin:
        hits = scan_lines(
            ((("<stdin>"), no, ln) for no, ln in enumerate(sys.stdin, start=1)), key, digests
        )
    else:
        paths = [Path(p).resolve() for p in args.paths] if args.paths else tracked_text_files()
        hits = scan_files(paths, key, digests)
    for h in hits:
        print(h)
    print(f"denylist: {len(hits)} hit(s)")
    return 1 if hits else 0


def cmd_check_history(args: argparse.Namespace) -> int:
    key = _require_key()
    digests = load_digests()
    if not digests:
        sys.exit(f"denylist: {HMAC_FILE.relative_to(REPO)} is empty; run build")
    hits = scan_lines(history_lines(), key, digests)
    for h in hits:
        print(h)
    print(f"denylist: {len(hits)} hit(s) in the git history")
    return 1 if hits else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("seed", help="propose entries from a profile into the local list")
    p.add_argument("--profile", help="a profile.yaml to take contact and employer details from")
    p.add_argument("--add", action="append", metavar="PHRASE", help="extra entry (repeatable)")
    p.set_defaults(func=cmd_seed)
    p = sub.add_parser("build", help="write tests/data/denylist.hmac from the local list")
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("check", help="scan files for denylisted content")
    p.add_argument("paths", nargs="*")
    p.add_argument("--stdin", action="store_true", help="scan standard input instead")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("check-history", help="scan every commit of the repository")
    p.set_defaults(func=cmd_check_history)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
