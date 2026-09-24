"""Stage 04 as code: an evidence note applied to the profile, layout-preserving (ADR-0013).

The profile is a person's file, so the edit is textual and additive: fact blocks are
appended under their parent's `facts:` list, new parents at the end of their list,
every existing line stays byte for byte. The result is validated before it stands;
the note is then marked `applied`. Nothing here sets a fact to `verified`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .dataroot import DataRoot, load_yaml
from .documents import load_document
from .errors import CvacError
from .validate import validate_files, write_validated

TOP_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")
ITEM_RE = re.compile(r"^(\s*)- id:\s*(\S+)\s*$")
FACT_ID_RE = re.compile(r"^(exp|prj)-[a-z0-9-]+\.f(\d{2})$")
LIST_OF = {"exp": "experiences", "prj": "projects"}


@dataclass
class ApplyResult:
    added: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    new_parents: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def lines(self) -> list[str]:
        out = [f"added {fid} (draft)" for fid in self.added]
        out += [f"skipped {s}" for s in self.skipped]
        out += [f"new parent {p}" for p in self.new_parents]
        return out + self.notes


def _scalar(value: Any) -> str:
    """One YAML scalar or flow collection, as safe_dump would quote it."""
    text = yaml.safe_dump(
        value, default_flow_style=True, allow_unicode=True, width=10**6, sort_keys=False
    )
    return text.split("\n...")[0].strip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _top_block(lines: list[str], key: str) -> tuple[int, int]:
    """[start, end) of a top-level key's block, end excluding trailing blank or comment lines."""
    start = next((i for i, ln in enumerate(lines) if ln.startswith(f"{key}:")), None)
    if start is None:
        raise CvacError(f"profile has no top-level `{key}:` key")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if TOP_KEY_RE.match(lines[i]):
            end = i
            break
    while end > start + 1 and (
        not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")
    ):
        end -= 1
    return start, end


def _sub_block_end(lines: list[str], start: int, end: int, indent: int) -> int:
    """End of the block that starts at `start` (a line at `indent`): next line at <= indent."""
    stop = end
    for i in range(start + 1, end):
        if (
            lines[i].strip()
            and not lines[i].lstrip().startswith("#")
            and _indent(lines[i]) <= indent
        ):
            stop = i
            break
    while stop > start + 1 and not lines[stop - 1].strip():
        stop -= 1
    return stop


def _list_item_indent(lines: list[str], start: int, end: int, key_indent: int) -> int | None:
    for i in range(start + 1, end):
        if ITEM_RE.match(lines[i]) and _indent(lines[i]) >= key_indent:
            return _indent(lines[i])
    return None


def _file_list_offset(lines: list[str]) -> int:
    """How far this file indents list items under their key (0 safe_dump, 2 hand-written)."""
    for i, ln in enumerate(lines):
        m = TOP_KEY_RE.match(ln)
        if m and not m.group(2).strip():
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].lstrip().startswith("- "):
                    return _indent(lines[j])
    return 0


def _fact_lines(fact: dict[str, Any], fid: str, evidence: str, indent: int) -> list[str]:
    pad, inner = " " * indent, " " * (indent + 2)
    return [
        f"{pad}- id: {fid}",
        f"{inner}claim: {_scalar(str(fact.get('claim', '')).strip())}",
        f"{inner}metrics: {_scalar(dict(fact.get('metrics') or {}))}",
        f"{inner}tags: {_scalar([str(t) for t in fact.get('tags') or []])}",
        f"{inner}status: draft",
        f"{inner}verified_on: null",
        f"{inner}evidence: {evidence}",
    ]


def _parent_lines(parent: dict[str, Any], indent: int) -> list[str]:
    pad, inner = " " * indent, " " * (indent + 2)
    company = dict(parent.get("company") or {})
    return [
        f"{pad}- id: {parent['id']}",
        f"{inner}role: {_scalar(str(parent.get('role') or ''))}",
        f"{inner}company: {_scalar({k: company.get(k) for k in ('name', 'location', 'industry')})}",
        f"{inner}start: {_scalar(parent.get('start'))}",
        f"{inner}end: {_scalar(parent.get('end'))}",
        f"{inner}facts:",
    ]


def _existing_facts(profile: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for section in ("experiences", "projects"):
        for entry in profile.get(section) or []:
            out[str(entry.get("id"))] = list(entry.get("facts") or [])
    return out


def _is_duplicate(existing: list[dict[str, Any]], fact: dict[str, Any], evidence: str) -> bool:
    claim = " ".join(str(fact.get("claim", "")).split()).casefold()
    for old in existing:
        refs = old.get("evidence")
        refs = [refs] if isinstance(refs, str) else list(refs or [])
        if evidence in refs or " ".join(str(old.get("claim", "")).split()).casefold() == claim:
            return True
    return False


class _Editor:
    """Line-level insertions into the profile text; every original line survives untouched."""

    def __init__(self, text: str) -> None:
        self.lines = text.splitlines()
        self.offset = _file_list_offset(self.lines)

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    def add_parent(self, parent: dict[str, Any]) -> None:
        key = LIST_OF[str(parent["id"])[:3]]
        start, end = _top_block(self.lines, key)
        head = self.lines[start]
        item_indent = _list_item_indent(self.lines, start, end, 0)
        if item_indent is None:
            item_indent = self.offset
            if head.split(":", 1)[1].strip() in ("[]", ""):
                self.lines[start] = f"{key}:"
                end = start + 1
        self.lines[end:end] = _parent_lines(parent, item_indent)

    def add_fact(self, parent_id: str, fact: dict[str, Any], fid: str, evidence: str) -> None:
        for key in ("experiences", "projects"):
            start, end = _top_block(self.lines, key)
            for i in range(start + 1, end):
                m = ITEM_RE.match(self.lines[i])
                if m and m.group(2) == parent_id:
                    self._add_fact_in(
                        i,
                        _sub_block_end(self.lines, i, end, _indent(self.lines[i])),
                        fact,
                        fid,
                        evidence,
                    )
                    return
        raise CvacError(f"parent `{parent_id}` not found in the profile")

    def _add_fact_in(
        self, p_start: int, p_end: int, fact: dict[str, Any], fid: str, evidence: str
    ) -> None:
        parent_indent = _indent(self.lines[p_start])
        facts_at = None
        for i in range(p_start + 1, p_end):
            stripped = self.lines[i].lstrip()
            if stripped.startswith("facts:") and _indent(self.lines[i]) == parent_indent + 2:
                facts_at = i
                break
        if facts_at is None:
            self.lines[p_end:p_end] = [" " * (parent_indent + 2) + "facts:"]
            facts_at, f_end = p_end, p_end + 1
        else:
            f_end = _sub_block_end(self.lines, facts_at, p_end, _indent(self.lines[facts_at]))
        key_indent = _indent(self.lines[facts_at])
        item_indent = _list_item_indent(self.lines, facts_at, f_end, key_indent)
        if item_indent is None:
            item_indent = key_indent + self.offset
            self.lines[facts_at] = " " * key_indent + "facts:"
            f_end = facts_at + 1
        self.lines[f_end:f_end] = _fact_lines(fact, fid, evidence, item_indent)


def _search_parameters_note(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("#") and "search parameters" in line.casefold():
            return (
                f"the note lists search parameters under '{line.strip('# ').strip()}': "
                "carry them into search.yaml by hand; they are not facts"
            )
    return None


def _set_note_applied(path: Path) -> None:
    lines = path.read_text("utf-8").splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        if re.match(r"^status:\s*proposed\s*$", lines[i]):
            lines[i] = "status: applied"
            path.write_text("\n".join(lines) + "\n", "utf-8")
            return
    raise CvacError(f"{path.name}: no `status: proposed` line in the frontmatter")


def apply_note(root: DataRoot, user: str, name: str) -> ApplyResult:
    """Apply notes/<name>.md to the user's profile; refuses what would not validate."""
    note_path = root.user_dir(user) / "notes" / f"{name}.md"
    profile_path = root.profile_path(user)
    for p in (note_path, profile_path):
        if not p.is_file():
            raise CvacError(f"missing {root.rel(p)}")
    rep = validate_files(root, [note_path])
    if rep.errors:
        raise CvacError("the note does not validate:\n  - " + "\n  - ".join(rep.errors))
    note = load_document(note_path, root.rel(note_path))
    if note.get("kind") != "evidence":
        raise CvacError(f"{root.rel(note_path)} is not an evidence note")
    if note.get("status") == "applied":
        raise CvacError(f"{root.rel(note_path)} is already applied")
    profile = load_yaml(profile_path)
    existing = _existing_facts(profile)
    editor = _Editor(profile_path.read_text("utf-8"))
    result = ApplyResult()

    for parent in note.get("new_parents") or []:
        pid = str(parent.get("id"))
        if pid in existing:
            raise CvacError(f"new parent `{pid}` already exists in the profile")
        editor.add_parent(parent)
        existing[pid] = []
        result.new_parents.append(pid)

    counters: dict[str, int] = {}
    for pid, facts in existing.items():
        numbers = [int(m.group(2)) for f in facts if (m := FACT_ID_RE.match(str(f.get("id", ""))))]
        counters[pid] = max(numbers, default=0)
    rel_note = f"notes/{name}.md"
    for fact in note.get("facts") or []:
        pid = str(fact.get("parent"))
        evidence = f"{rel_note}#{fact.get('anchor')}"
        if pid not in existing:
            raise CvacError(f"fact parent `{pid}` is neither in the profile nor in new_parents")
        if _is_duplicate(existing[pid], fact, evidence):
            result.skipped.append(
                f"{pid}: `{str(fact.get('claim', ''))[:60]}` (already in the profile)"
            )
            continue
        counters[pid] += 1
        fid = f"{pid}.f{counters[pid]:02d}"
        editor.add_fact(pid, fact, fid, evidence)
        existing[pid].append({"id": fid, "claim": fact.get("claim"), "evidence": evidence})
        result.added.append(fid)

    if not result.added and not result.new_parents:
        raise CvacError("nothing to apply: every fact of the note is already in the profile")
    rep = write_validated(root, profile_path, editor.text())
    if rep.errors:
        raise CvacError(
            "the profile would not validate; nothing written:\n  - " + "\n  - ".join(rep.errors)
        )
    _set_note_applied(note_path)
    body = note_path.read_text("utf-8").split("\n---\n", 1)[-1]
    if hint := _search_parameters_note(body):
        result.notes.append(hint)
    result.notes.append("every added fact is draft until you verify it")
    return result
