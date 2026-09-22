"""The human gate as a command: `cvac fact verify|reject <id>...` (ADR-0013).

Edits profile.yaml textually — only the `status:` and `verified_on:` lines of the
named facts — so the file keeps its comments and layout; a YAML round trip would
rewrite it. Verification refuses a fact without evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .dataroot import DataRoot, load_yaml
from .errors import CvacError
from .validate import evidence_list

FACT_ID_RE = re.compile(r"^(exp|prj)-[a-z0-9-]+\.f\d{2}$")


@dataclass
class FactChange:
    fact_id: str
    old_status: str
    new_status: str


def _fact_index(profile: dict) -> dict[str, dict]:
    facts: dict[str, dict] = {}
    for section in ("experiences", "projects"):
        for entry in profile.get(section) or []:
            for fact in entry.get("facts") or []:
                facts[str(fact.get("id"))] = fact
    return facts


def _block_bounds(lines: list[str], fact_id: str) -> tuple[int, int]:
    """Line range [start, end) of the fact whose `id:` line names fact_id."""
    id_re = re.compile(rf"^(\s*)-\s+id:\s*{re.escape(fact_id)}\s*$")
    for i, line in enumerate(lines):
        m = id_re.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        end = i + 1
        while end < len(lines):
            stripped = lines[end].lstrip()
            current = len(lines[end]) - len(stripped)
            if stripped and current <= indent:
                break
            end += 1
        return i, end
    raise CvacError(f"fact `{fact_id}` not found as a `- id:` line in the profile")


def _set_field(lines: list[str], start: int, end: int, key: str, value: str) -> None:
    field_re = re.compile(rf"^(\s*){key}:\s*.*$")
    for i in range(start + 1, end):
        m = field_re.match(lines[i])
        if m:
            lines[i] = f"{m.group(1)}{key}: {value}"
            return
    # the field is absent: add it after the status line, aligned with it
    for i in range(start + 1, end):
        m = re.match(r"^(\s*)status:", lines[i])
        if m:
            lines.insert(i + 1, f"{m.group(1)}{key}: {value}")
            return
    raise CvacError(f"fact block has no `status:` line to anchor `{key}` on")


def set_status(
    root: DataRoot, user: str, fact_ids: list[str], status: str, on: str | None = None
) -> list[FactChange]:
    if status not in ("verified", "rejected"):
        raise CvacError(f"status must be verified or rejected, not {status!r}")
    profile_path = root.profile_path(user)
    profile = load_yaml(profile_path)
    index = _fact_index(profile)
    stamp = on or date.today().isoformat()
    changes: list[FactChange] = []
    for fid in fact_ids:
        if not FACT_ID_RE.match(fid):
            raise CvacError(f"`{fid}` is not a fact id (expected <parent>.fNN)")
        if fid not in index:
            raise CvacError(f"fact `{fid}` does not exist in {root.rel(profile_path)}")
        fact = index[fid]
        if status == "verified":
            paths = evidence_list(fact.get("evidence"))
            missing = [p for p in paths if not (profile_path.parent / p.split("#", 1)[0]).exists()]
            if not paths or missing:
                raise CvacError(
                    f"fact `{fid}` cannot be verified without evidence that exists "
                    f"(evidence: {paths or 'none'})"
                )
        changes.append(FactChange(fid, str(fact.get("status")), status))

    lines = profile_path.read_text("utf-8").splitlines()
    for change in changes:
        start, end = _block_bounds(lines, change.fact_id)
        _set_field(lines, start, end, "status", status)
        _set_field(
            lines, start, end, "verified_on", f'"{stamp}"' if status == "verified" else "null"
        )
    profile_path.write_text("\n".join(lines) + "\n", "utf-8")
    return changes


def profile_of(root: DataRoot, user: str | None) -> tuple[str, Path]:
    slug = user or root.default_user
    if not slug:
        raise CvacError("no user: pass --user or set default_user in cvac.yaml")
    return slug, root.profile_path(slug)
