"""Layout-preserving edits of profile.yaml: the curriculum grows in place, every line kept.

Shared by the deterministic apply (stage 04) and the curriculum form: blocks are appended
to their list, scalar fields are replaced on their own line, and nothing else moves. The
callers validate the result before it stands and restore the file otherwise.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from .errors import CvacError

TOP_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$")
ITEM_RE = re.compile(r"^(\s*)- id:\s*(\S+)\s*$")
FACT_ID_RE = re.compile(r"^(exp|prj)-[a-z0-9-]+\.f(\d{2})$")
LIST_OF = {"exp": "experiences", "prj": "projects"}


def scalar(value: Any) -> str:
    """One YAML scalar or flow collection, as safe_dump would quote it."""
    text = yaml.safe_dump(
        value, default_flow_style=True, allow_unicode=True, width=10**6, sort_keys=False
    )
    return text.split("\n...")[0].strip()


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def top_block(lines: list[str], key: str) -> tuple[int, int]:
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


def sub_block_end(lines: list[str], start: int, end: int, indent: int) -> int:
    """End of the block that starts at `start` (a line at `indent`): next line at <= indent."""
    stop = end
    for i in range(start + 1, end):
        if (
            lines[i].strip()
            and not lines[i].lstrip().startswith("#")
            and indent_of(lines[i]) <= indent
        ):
            stop = i
            break
    while stop > start + 1 and not lines[stop - 1].strip():
        stop -= 1
    return stop


def list_block_end(lines: list[str], at: int, end: int) -> int:
    """End of the list under the key at `at`: its items may sit at the key's own indent."""
    key_indent = indent_of(lines[at])
    stop = at + 1
    while stop < end:
        line = lines[stop]
        if not line.strip() or line.lstrip().startswith("#"):
            stop += 1
            continue
        ind = indent_of(line)
        if ind > key_indent or (ind == key_indent and line.lstrip().startswith("- ")):
            stop += 1
            continue
        break
    while stop > at + 1 and not lines[stop - 1].strip():
        stop -= 1
    return stop


def list_item_indent(lines: list[str], start: int, end: int, key_indent: int) -> int | None:
    for i in range(start + 1, end):
        if lines[i].lstrip().startswith("- ") and indent_of(lines[i]) >= key_indent:
            return indent_of(lines[i])
    return None


def file_list_offset(lines: list[str]) -> int:
    """How far this file indents list items under their key (0 safe_dump, 2 hand-written)."""
    for i, ln in enumerate(lines):
        m = TOP_KEY_RE.match(ln)
        if m and not m.group(2).strip():
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].lstrip().startswith("- "):
                    return indent_of(lines[j])
    return 0


def fact_lines(fact: dict[str, Any], fid: str, evidence: str, indent: int) -> list[str]:
    pad, inner = " " * indent, " " * (indent + 2)
    status = fact.get("status") or "draft"
    verified_on = scalar(fact["verified_on"]) if fact.get("verified_on") else "null"
    return [
        f"{pad}- id: {fid}",
        f"{inner}claim: {scalar(str(fact.get('claim', '')).strip())}",
        f"{inner}metrics: {scalar(dict(fact.get('metrics') or {}))}",
        f"{inner}tags: {scalar([str(t) for t in fact.get('tags') or []])}",
        f"{inner}status: {status}",
        f"{inner}verified_on: {verified_on}",
        f"{inner}evidence: {evidence}",
    ]


def parent_lines(parent: dict[str, Any], indent: int) -> list[str]:
    pad, inner = " " * indent, " " * (indent + 2)
    company = dict(parent.get("company") or {})
    return [
        f"{pad}- id: {parent['id']}",
        f"{inner}role: {scalar(str(parent.get('role') or ''))}",
        f"{inner}company: {scalar({k: company.get(k) for k in ('name', 'location', 'industry')})}",
        f"{inner}start: {scalar(parent.get('start'))}",
        f"{inner}end: {scalar(parent.get('end'))}",
        f"{inner}facts: []",
    ]


def mapping_lines(item: dict[str, Any], indent: int) -> list[str]:
    """A list item as a block mapping, `- key: value` then the rest indented."""
    keys = list(item)
    out = [" " * indent + f"- {keys[0]}: {scalar(item[keys[0]])}"]
    out += [" " * (indent + 2) + f"{k}: {scalar(item[k])}" for k in keys[1:]]
    return out


class ProfileEditor:
    """Line-level edits of the profile text; every original line survives untouched."""

    def __init__(self, text: str) -> None:
        self.lines = text.splitlines()
        self.offset = file_list_offset(self.lines)

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    # ---- lists --------------------------------------------------------------------
    def append_item(self, key: str, render: Any) -> None:
        """Append to a top-level list; `render(indent)` gives the item's lines; `[]` is opened."""
        start, end = top_block(self.lines, key)
        item_indent = list_item_indent(self.lines, start, end, 0)
        if item_indent is None:
            item_indent = self.offset
            if self.lines[start].split(":", 1)[1].strip() in ("[]", ""):
                self.lines[start] = f"{key}:"
                end = start + 1
        self.lines[end:end] = render(item_indent)

    def add_parent(self, parent: dict[str, Any]) -> None:
        key = LIST_OF[str(parent["id"])[:3]]
        self.append_item(key, lambda indent: parent_lines(parent, indent))

    def find_item(self, key: str, item_id: str) -> tuple[int, int]:
        start, end = top_block(self.lines, key)
        for i in range(start + 1, end):
            m = ITEM_RE.match(self.lines[i])
            if m and m.group(2) == item_id:
                return i, sub_block_end(self.lines, i, end, indent_of(self.lines[i]))
        raise CvacError(f"`{item_id}` not found under `{key}` in the profile")

    def add_fact(self, parent_id: str, fact: dict[str, Any], fid: str, evidence: str) -> None:
        for key in ("experiences", "projects"):
            try:
                p_start, p_end = self.find_item(key, parent_id)
            except CvacError:
                continue
            self._add_fact_in(p_start, p_end, fact, fid, evidence)
            return
        raise CvacError(f"parent `{parent_id}` not found in the profile")

    def _add_fact_in(
        self, p_start: int, p_end: int, fact: dict[str, Any], fid: str, evidence: str
    ) -> None:
        parent_indent = indent_of(self.lines[p_start])
        facts_at = None
        for i in range(p_start + 1, p_end):
            stripped = self.lines[i].lstrip()
            if stripped.startswith("facts:") and indent_of(self.lines[i]) == parent_indent + 2:
                facts_at = i
                break
        if facts_at is None:
            self.lines[p_end:p_end] = [" " * (parent_indent + 2) + "facts:"]
            facts_at, f_end = p_end, p_end + 1
        else:
            f_end = list_block_end(self.lines, facts_at, p_end)
        key_indent = indent_of(self.lines[facts_at])
        item_indent = list_item_indent(self.lines, facts_at, f_end, key_indent)
        if item_indent is None:
            item_indent = key_indent + self.offset
            self.lines[facts_at] = " " * key_indent + "facts:"
            f_end = facts_at + 1
        self.lines[f_end:f_end] = fact_lines(fact, fid, evidence, item_indent)

    # ---- scalar fields ----------------------------------------------------------------
    def set_field(self, start: int, end: int, field: str, value: Any, at_indent: int) -> None:
        """Replace `field:` at exactly `at_indent` within [start, end); add it if absent."""
        rendered = scalar(value)
        for i in range(start + 1, end):
            if indent_of(self.lines[i]) == at_indent and re.match(rf"^\s*{field}:", self.lines[i]):
                stop = sub_block_end(self.lines, i, end, at_indent)
                self.lines[i:stop] = [" " * at_indent + f"{field}: {rendered}"]
                return
        self.lines.insert(start + 1, " " * at_indent + f"{field}: {rendered}")

    def set_item_field(self, key: str, item_id: str, field: str, value: Any) -> None:
        start, end = self.find_item(key, item_id)
        self.set_field(start, end, field, value, indent_of(self.lines[start]) + 2)

    def set_mapping_field(self, start: int, end: int, name: str, field: str, value: Any) -> None:
        """`name.field` inside [start, end): a flow `{…}` line is rewritten, a block edited."""
        at = next((i for i in range(start, end) if re.match(rf"^\s*{name}:", self.lines[i])), None)
        if at is None:
            base = indent_of(self.lines[start]) + (
                2 if self.lines[start].lstrip().startswith("- ") else 0
            )
            self.lines.insert(start + 1, " " * base + f"{name}:")
            self.lines.insert(start + 2, " " * (base + 2) + f"{field}: {scalar(value)}")
            return
        head, _, rest = self.lines[at].partition(":")
        rest = rest.strip()
        if rest.startswith("{"):
            mapping = yaml.safe_load(rest) or {}
            mapping[field] = value
            self.lines[at] = f"{head}: {scalar(mapping)}"
            return
        stop = sub_block_end(self.lines, at, end, indent_of(self.lines[at]))
        self.set_field(at, stop, field, value, indent_of(self.lines[at]) + 2)

    def set_item_mapping_field(
        self, key: str, item_id: str, name: str, field: str, value: Any
    ) -> None:
        start, end = self.find_item(key, item_id)
        self.set_mapping_field(start, end, name, field, value)

    def set_identity_field(self, field: str, value: Any) -> None:
        start, end = top_block(self.lines, "identity")
        self.set_field(start, end, field, value, indent_of(self.lines[start]) + 2)

    def set_identity_location(self, city: str, country: str | None) -> None:
        start, end = top_block(self.lines, "identity")
        self.set_mapping_field(start, end, "location", "city", city)
        start, end = top_block(self.lines, "identity")
        if country:
            self.set_mapping_field(start, end, "location", "country", country)
        else:
            self._drop_mapping_field(start, end, "location", "country")

    def _drop_mapping_field(self, start: int, end: int, name: str, field: str) -> None:
        at = next((i for i in range(start, end) if re.match(rf"^\s*{name}:", self.lines[i])), None)
        if at is None:
            return
        rest = self.lines[at].partition(":")[2].strip()
        if rest.startswith("{"):
            mapping = yaml.safe_load(rest) or {}
            mapping.pop(field, None)
            self.lines[at] = f"{self.lines[at].partition(':')[0]}: {scalar(mapping)}"
            return
        stop = sub_block_end(self.lines, at, end, indent_of(self.lines[at]))
        for i in range(at + 1, stop):
            if re.match(rf"^\s*{field}:", self.lines[i]):
                del self.lines[i]
                return

    def set_identity_links(self, links: list[dict[str, str]]) -> None:
        start, end = top_block(self.lines, "identity")
        base = indent_of(self.lines[start]) + 2
        at = next(
            (i for i in range(start + 1, end) if re.match(r"^\s*links:", self.lines[i])), None
        )
        rendered = [" " * base + ("links: []" if not links else "links:")] + [
            " " * (base + self.offset) + f"- {scalar(link)}" for link in links
        ]
        if at is None:
            self.lines[end:end] = rendered
            return
        stop = list_block_end(self.lines, at, end)
        self.lines[at:stop] = rendered
