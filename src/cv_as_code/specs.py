"""The human gate on a cv-spec or a cover letter as a library call (ADR-0001, ADR-0014).

Approval edits only the top-level `status:` and `approved_on:` lines, so the file
keeps its comments and layout. It is refused when the approved document would not
validate: the validator, not this module, holds the rule (approved => every cited
fact verified), so the CLI, the skills and the UI cannot drift from each other.
"""

from __future__ import annotations

import re
import tempfile
from datetime import date
from pathlib import Path

from .dataroot import DataRoot
from .documents import load_document
from .errors import CvacError
from .validate import validate_files

STATUS_RE = re.compile(r"^status:\s*[\w-]+(?P<tail>\s+#.*)?\s*$")
APPROVED_ON_RE = re.compile(r"^approved_on:.*$")
APPROVABLE = ("cv-spec", "cover-letter")


def _region(lines: list[str], path: Path) -> tuple[int, int]:
    """Line range [start, end) holding the top-level keys: the whole file, or the frontmatter."""
    if path.suffix != ".md":
        return 0, len(lines)
    if not lines or lines[0].strip() != "---":
        raise CvacError(f"{path.name} has no YAML frontmatter")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return 1, i
    raise CvacError(f"{path.name}: unterminated frontmatter")


def approved_text(text: str, path: Path, stamp: str) -> str:
    """The document with status: approved and approved_on set; nothing else touched."""
    lines = text.splitlines()
    start, end = _region(lines, path)
    status_at = None
    for i in range(start, end):
        m = STATUS_RE.match(lines[i])
        if m:
            lines[i] = f"status: approved{m.group('tail') or ''}"
            status_at = i
            break
    if status_at is None:
        raise CvacError(f"{path.name} has no top-level `status:` line")
    for i in range(start, end):
        if APPROVED_ON_RE.match(lines[i]):
            lines[i] = f'approved_on: "{stamp}"'
            break
    else:
        lines.insert(status_at + 1, f'approved_on: "{stamp}"')
    return "\n".join(lines) + "\n"


def approve(root: DataRoot, path: Path, on: str | None = None) -> str:
    """Approve a cv-spec.yaml or a letter.md on the person's say-so; returns the date stamped."""
    where = root.rel(path)
    if not path.is_file():
        raise CvacError(f"missing {where}")
    doc = load_document(path, where)
    if not isinstance(doc, dict) or doc.get("kind") not in APPROVABLE:
        raise CvacError(f"{where} is not a cv-spec or a cover letter")
    if doc.get("status") == "approved":
        raise CvacError(f"{where} is already approved (approved_on: {doc.get('approved_on')})")
    stamp = on or date.today().isoformat()
    candidate = approved_text(path.read_text("utf-8"), path, stamp)
    # Validate the would-be document before touching the real file: the temporary copy keeps
    # the file and directory names (a letter's directory is its job_id), and every other check
    # resolves against the data root, not the file's location.
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / path.parent.name / path.name
        probe.parent.mkdir()
        probe.write_text(candidate, "utf-8")
        rep = validate_files(root, [probe])
        prefix = f"{root.rel(probe)}: "
    if rep.errors:
        msgs = [e[len(prefix) :] if e.startswith(prefix) else e for e in rep.errors]
        raise CvacError(f"cannot approve {where}:\n  - " + "\n  - ".join(msgs))
    path.write_text(candidate, "utf-8")
    return stamp
