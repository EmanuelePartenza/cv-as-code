"""Publication boundary: nothing personal is ever tracked in this repository (ADR-0009).

Structural rules need no secret and run everywhere: no user data outside the
example data root, no PDF or office documents, no private directories, no
e-mail, phone or date-of-birth shaped strings outside the example's reserved
fake values. The keyed denylist (the maintainer's own private strings, matched
through an HMAC so they never appear here) is added by WP-03.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

EXAMPLE_PREFIX = "example/"
EXAMPLE_USERS = {"robin"}
EXAMPLE_PHONE_DIGITS = "441632960123"  # Ofcom-reserved fictional range, +44 1632 960xxx

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
ALLOWED_EMAIL_RE = re.compile(r"@example\.(com|org|net)$")
PHONE_RE = re.compile(r"\+\d[\d\s().-]{7,}\d")
DOB_RE = re.compile(r'born:\s*"\d{4}-\d{2}-\d{2}"')
OFFICE_DOC_RE = re.compile(r"\.(pdf|docx?|odt)$", re.IGNORECASE)
PRIVATE_DIRS = {"interviews", "sources", "inbox", "00_personal"}
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
# Third-party licence texts may carry their authors' contact details, and this file
# holds forbidden-shaped strings on purpose, as negative cases for the rules below.
CONTENT_EXEMPT = {
    "LICENSE",
    "src/cv_as_code/templates/fonts/OFL.txt",
    "tests/test_publication_boundary.py",
}


def tracked_files(repo: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.split("\0") if p]


def structural_violations(paths: list[str], read: Callable[[str], str | None]) -> list[str]:
    """Pure rule engine over (path, content) so the rules themselves can be tested."""
    found: list[str] = []
    for path in paths:
        parts = path.split("/")
        in_example = path.startswith(EXAMPLE_PREFIX)
        if "users" in parts:
            idx = parts.index("users")
            if not in_example:
                found.append(f"{path}: user data outside {EXAMPLE_PREFIX}")
            elif len(parts) > idx + 1 and parts[idx + 1] not in EXAMPLE_USERS | {".gitkeep"}:
                found.append(f"{path}: example user `{parts[idx + 1]}` is not allow-listed")
        if OFFICE_DOC_RE.search(path):
            found.append(f"{path}: PDF/office documents are never tracked")
        if not in_example and PRIVATE_DIRS.intersection(parts):
            found.append(f"{path}: private directory outside {EXAMPLE_PREFIX}")
        if path in CONTENT_EXEMPT or Path(path).suffix not in TEXT_SUFFIXES:
            continue
        text = read(path)
        if text is None:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for m in EMAIL_RE.finditer(line):
                if not ALLOWED_EMAIL_RE.search(m.group()):
                    found.append(f"{path}:{line_no}: e-mail address `{m.group()}`")
            for m in PHONE_RE.finditer(line):
                digits = re.sub(r"\D", "", m.group())
                if not (in_example and digits == EXAMPLE_PHONE_DIGITS):
                    found.append(f"{path}:{line_no}: phone-shaped string `{m.group().strip()}`")
            if not in_example and DOB_RE.search(line):
                found.append(f"{path}:{line_no}: date of birth")
    return found


def _read_repo_file(path: str) -> str | None:
    try:
        return (REPO / path).read_text("utf-8")
    except (UnicodeDecodeError, OSError):
        return None


@pytest.mark.skipif(not (REPO / ".git").exists(), reason="not a git checkout")
def test_tracked_files_respect_the_boundary() -> None:
    violations = structural_violations(tracked_files(REPO), _read_repo_file)
    assert not violations, "\n".join(violations)


# --- the rules themselves, on synthetic input -------------------------------------------


def _rules(files: dict[str, str]) -> list[str]:
    return structural_violations(list(files), lambda p: files.get(p))


def test_user_data_outside_example_is_rejected() -> None:
    assert _rules({"users/someone/profile.yaml": "kind: profile\n"})


def test_example_user_must_be_allow_listed() -> None:
    assert not _rules({"example/users/robin/profile.yaml": "kind: profile\n"})
    assert _rules({"example/users/mallory/profile.yaml": "kind: profile\n"})


def test_office_documents_are_rejected_anywhere() -> None:
    assert _rules({"example/users/robin/masters/x/cv.pdf": ""})
    assert _rules({"docs/old-cv.docx": ""})


def test_private_directories_are_rejected_outside_example() -> None:
    assert _rules({"docs/interviews/01.md": "notes\n"})
    assert not _rules({"example/users/robin/interviews/01.md": "notes\n"})


def test_emails_outside_example_domains_are_rejected() -> None:
    assert not _rules({"README.md": "write to robin.ashcombe@example.com\n"})
    assert _rules({"README.md": "write to someone@gmail.com\n"})


def test_phone_numbers_are_rejected_except_the_reserved_example_one() -> None:
    assert _rules({"docs/x.md": "call +39 333 123 4567 now\n"})
    assert not _rules({"example/users/robin/profile.yaml": 'phone: "+44 1632 960123"\n'})
    assert _rules({"example/users/robin/profile.yaml": 'phone: "+44 1632 960999"\n'})
    assert _rules({"docs/x.md": 'phone: "+44 1632 960123"\n'})


def test_date_of_birth_is_rejected_outside_example() -> None:
    assert _rules({"tests/fixture.yaml": 'born: "1990-01-01"\n'})
    assert not _rules({"tests/fixture.yaml": "born: null\n"})
    assert not _rules({"example/users/robin/profile.yaml": 'born: "1990-01-01"\n'})


def test_binary_and_exempt_files_are_not_content_checked() -> None:
    assert not _rules({"src/cv_as_code/templates/fonts/Lato-Regular.ttf": "someone@gmail.com"})
    assert not _rules({"LICENSE": "someone@gmail.com"})
