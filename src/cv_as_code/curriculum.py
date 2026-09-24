"""The curriculum grows from the form: entries, education, skills, languages, identity, search,
and the person's own facts — evidenced as their own words, in a note (ADR-0017).

Every write is a layout-preserving edit validated before it stands; a fact the person adds
is draft unless they confirm it in the same act, and nothing else ever sets `verified`.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .dataroot import DataRoot, load_yaml
from .documents import load_document
from .errors import CvacError
from .profile_edit import FACT_ID_RE, LIST_OF, ProfileEditor, mapping_lines, scalar, top_block
from .validate import write_validated

OWN_NOTE = "own-words"
DATE_RE = re.compile(r"^\d{4}(-\d{2})?(-\d{2})?$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MODES = ("onsite", "hybrid", "remote")


def slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (text or "").lower())).strip("-")


def _date(value: str | None, what: str) -> str | None:
    value = (value or "").strip()
    if not value or value.lower() in ("ongoing", "present", "now"):
        return None
    if not DATE_RE.match(value):
        raise CvacError(f"{what}: `{value}` is not a date (YYYY, YYYY-MM or YYYY-MM-DD)")
    return value


def _required(value: str | None, what: str) -> str:
    value = " ".join((value or "").split())
    if not value:
        raise CvacError(f"{what} is required")
    return value


def _save(root: DataRoot, path: Path, text: str) -> None:
    rep = write_validated(root, path, text)
    if rep.errors:
        raise CvacError("not saved, the file would not validate:\n  - " + "\n  - ".join(rep.errors))


def _editor(root: DataRoot, user: str) -> tuple[Path, ProfileEditor]:
    path = root.profile_path(user)
    if not path.is_file():
        raise CvacError(f"missing {root.rel(path)}")
    return path, ProfileEditor(path.read_text("utf-8"))


def _ids(profile: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("experiences", "projects", "education", "skills"):
        for item in profile.get(key) or []:
            ids.add(str(item.get("id")))
            for fact in item.get("facts") or []:
                ids.add(str(fact.get("id")))
    return ids


def _fresh_id(prefix: str, base: str, taken: set[str], explicit: str | None) -> str:
    if explicit:
        if not SLUG_RE.match(explicit) or not explicit.startswith(prefix + "-"):
            raise CvacError(f"`{explicit}` is not an id of the form {prefix}-<slug>")
        if explicit in taken:
            raise CvacError(f"`{explicit}` already exists in the profile")
        return explicit
    stem = slugify(base) or "item"
    candidate, n = f"{prefix}-{stem}", 2
    while candidate in taken:
        candidate, n = f"{prefix}-{stem}-{n}", n + 1
    return candidate


# ---- identity, languages ------------------------------------------------------------------


def set_identity(
    root: DataRoot,
    user: str,
    *,
    full_name: str,
    email: str,
    city: str,
    country: str | None = None,
    phone: str | None = None,
    born: str | None = None,
    links: list[tuple[str, str]] | None = None,
) -> None:
    path, ed = _editor(root, user)
    ed.set_identity_field("full_name", _required(full_name, "the full name"))
    ed.set_identity_field("email", _required(email, "the e-mail"))
    ed.set_identity_field("phone", (phone or "").strip() or None)
    born_value = (born or "").strip() or None
    if born_value and not re.match(r"^\d{4}-\d{2}-\d{2}$", born_value):
        raise CvacError(f"the date of birth `{born_value}` is not YYYY-MM-DD")
    ed.set_identity_field("born", born_value)
    ed.set_identity_location(_required(city, "the city"), (country or "").strip() or None)
    if links is not None:
        clean = []
        for label, url in links:
            label, url = label.strip(), url.strip()
            if not url:
                continue
            clean.append({"label": label or url, "url": url})
        ed.set_identity_links(clean)
    _save(root, path, ed.text())


def add_language(root: DataRoot, user: str, code: str, level: str, note: str | None = None) -> None:
    code, level = (code or "").strip().lower(), _required(level, "the level")
    if not re.match(r"^[a-z]{2}$", code):
        raise CvacError(f"`{code}` is not an ISO 639-1 language code")
    path, ed = _editor(root, user)
    if any(lg.get("code") == code for lg in load_yaml(path).get("languages") or []):
        raise CvacError(f"language `{code}` is already listed")
    item: dict[str, Any] = {"code": code, "level": level}
    if note and note.strip():
        item["note"] = note.strip()
    ed.append_item("languages", lambda indent: mapping_lines(item, indent))
    _save(root, path, ed.text())


# ---- experiences and projects ---------------------------------------------------------------


def add_entry(
    root: DataRoot,
    user: str,
    kind: str,
    *,
    role: str,
    company: str | None = None,
    location: str | None = None,
    industry: str | None = None,
    start: str | None = None,
    end: str | None = None,
    entry_id: str | None = None,
) -> str:
    """A new experience (`exp`) or project (`prj`), with no facts yet; returns its id."""
    if kind not in LIST_OF:
        raise CvacError(f"kind must be exp or prj, not {kind!r}")
    path, ed = _editor(root, user)
    role = _required(role, "the role")
    eid = _fresh_id(kind, company or role, _ids(load_yaml(path)), entry_id)
    ed.add_parent(
        {
            "id": eid,
            "role": role,
            "company": {
                "name": (company or "").strip() or None,
                "location": (location or "").strip() or None,
                "industry": (industry or "").strip() or None,
            },
            "start": _date(start, "start"),
            "end": _date(end, "end"),
        }
    )
    _save(root, path, ed.text())
    return eid


def update_entry(root: DataRoot, user: str, entry_id: str, **fields: str | None) -> None:
    """Change role, start, end, company, location or industry of an entry, in place."""
    key = LIST_OF.get(entry_id[:3])
    if key is None:
        raise CvacError(f"`{entry_id}` is not an experience or project id")
    path, ed = _editor(root, user)
    for name, value in fields.items():
        if name == "role":
            ed.set_item_field(key, entry_id, "role", _required(value, "the role"))
        elif name in ("start", "end"):
            ed.set_item_field(key, entry_id, name, _date(value, name))
        elif name in ("company", "location", "industry"):
            sub = "name" if name == "company" else name
            ed.set_item_mapping_field(key, entry_id, "company", sub, (value or "").strip() or None)
        else:
            raise CvacError(f"`{name}` is not an editable field of an entry")
    _save(root, path, ed.text())


# ---- education, skills ------------------------------------------------------------------------


def add_education(
    root: DataRoot,
    user: str,
    *,
    degree: str,
    institution: str,
    location: str | None = None,
    start: str | None = None,
    end: str | None = None,
    edu_id: str | None = None,
) -> str:
    path, ed = _editor(root, user)
    degree, institution = _required(degree, "the degree"), _required(institution, "the institution")
    eid = _fresh_id("edu", institution, _ids(load_yaml(path)), edu_id)
    item = {
        "id": eid,
        "degree": degree,
        "institution": institution,
        "location": (location or "").strip() or None,
        "start": _date(start, "start"),
        "end": _date(end, "end"),
    }
    ed.append_item("education", lambda indent: mapping_lines(item, indent))
    _save(root, path, ed.text())
    return eid


def add_skill(
    root: DataRoot,
    user: str,
    *,
    name: str,
    category: str,
    evidence_facts: list[str] | None = None,
    skill_id: str | None = None,
) -> str:
    path, ed = _editor(root, user)
    profile = load_yaml(path)
    name, category = _required(name, "the skill"), _required(category, "the category")
    facts = [f.strip() for f in evidence_facts or [] if f.strip()]
    known = _ids(profile)
    unknown = [f for f in facts if f not in known or not FACT_ID_RE.match(f)]
    if unknown:
        raise CvacError(f"unknown fact(s) for the skill: {', '.join(unknown)}")
    sid = _fresh_id("skill", name, known, skill_id)
    item = {"id": sid, "name": name, "category": category, "evidence_facts": facts}
    ed.append_item("skills", lambda indent: mapping_lines(item, indent))
    _save(root, path, ed.text())
    return sid


# ---- the person's own facts ---------------------------------------------------------------------


def _own_note(root: DataRoot, user: str, pivot: str) -> Path:
    path = root.user_dir(user) / "notes" / f"{OWN_NOTE}.md"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        front = {
            "schema_version": 1,
            "kind": "evidence",
            "user": user,
            "source": "the person's own words, entered in the curriculum form",
            "extracted_on": date.today().isoformat(),
            "language": pivot,
            "status": "applied",
            "facts": [],
        }
        text = "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True) + "---\n\n"
        text += (
            "# Own words\n\nFacts the person added directly, each dated; verified only by them.\n"
        )
        path.write_text(text, "utf-8")
    return path


def _append_own_quote(text: str, fact: dict[str, Any], anchor: str, stamp: str) -> str:
    """The note with one more proposed fact in its frontmatter and its passage in the body."""
    lines = text.splitlines()
    close = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    facts_at = next(i for i in range(1, close) if re.match(r"^facts:", lines[i]))
    item = [
        f"  - parent: {fact['parent']}",
        f"    claim: {scalar(fact['claim'])}",
        f"    metrics: {scalar(fact['metrics'])}",
        f"    tags: {scalar(fact['tags'])}",
        f"    quote: {scalar(fact['claim'])}",
        f"    anchor: {anchor}",
    ]
    if lines[facts_at].strip() == "facts: []":
        lines[facts_at] = "facts:"
        lines[facts_at + 1 : facts_at + 1] = item
    else:
        lines[close:close] = item
    return (
        "\n".join(lines).rstrip("\n")
        + f"\n\n## {anchor}\n\n{fact['claim']}\n\n_stated on {stamp}_\n"
    )


def add_own_fact(
    root: DataRoot,
    user: str,
    parent_id: str,
    claim: str,
    *,
    metrics: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    confirm: bool = False,
) -> str:
    """A fact in the person's own words under an entry; its evidence is the own-words note."""
    claim = _required(claim, "the fact")
    path, ed = _editor(root, user)
    profile = load_yaml(path)
    entries = {e["id"]: e for k in LIST_OF.values() for e in profile.get(k) or []}
    if parent_id not in entries:
        raise CvacError(f"`{parent_id}` is not an experience or project of the profile")
    numbers = [
        int(m.group(2))
        for f in entries[parent_id].get("facts") or []
        if (m := FACT_ID_RE.match(str(f.get("id", ""))))
    ]
    fid = f"{parent_id}.f{max(numbers, default=0) + 1:02d}"
    note_path = _own_note(root, user, str(profile.get("pivot_language") or "en"))
    note_before = note_path.read_text("utf-8")
    anchor = f"own-{len(re.findall(r'^## own-', note_before, re.M)) + 1:03d}"
    stamp = date.today().isoformat()
    fact = {
        "parent": parent_id,
        "claim": claim,
        "metrics": dict(metrics or {}),
        "tags": list(tags or []),
    }
    _save(root, note_path, _append_own_quote(note_before, fact, anchor, stamp))
    profile_fact = {
        **fact,
        "status": "verified" if confirm else "draft",
        "verified_on": stamp if confirm else None,
    }
    try:
        ed.add_fact(parent_id, profile_fact, fid, f"notes/{OWN_NOTE}.md#{anchor}")
        _save(root, path, ed.text())
    except CvacError:
        note_path.write_text(note_before, "utf-8")
        raise
    return fid


def parse_metrics(text: str) -> dict[str, Any]:
    """`key=value` pairs, comma- or newline-separated; numbers become numbers."""
    out: dict[str, Any] = {}
    for pair in re.split(r"[,\n]", text or ""):
        if "=" not in pair:
            if pair.strip():
                raise CvacError(f"`{pair.strip()}` is not key=value")
            continue
        key, value = (s.strip() for s in pair.split("=", 1))
        if not re.match(r"^[a-z0-9_]+$", key):
            raise CvacError(f"`{key}` is not a metric name (lowercase letters, digits, _)")
        out[key] = yaml.safe_load(value) if value else None
    return out


# ---- what the person is looking for -----------------------------------------------------


def set_search(root: DataRoot, user: str, **fields: Any) -> None:
    """Replace top-level keys of search.yaml with the given values; other lines stay."""
    path = root.user_dir(user) / "search.yaml"
    if not path.is_file():
        raise CvacError(f"missing {root.rel(path)}")
    lines = path.read_text("utf-8").splitlines()
    for key, value in fields.items():
        rendered = _search_lines(key, value)
        try:
            start, end = top_block(lines, key)
        except CvacError:
            lines[len(lines) :] = rendered
            continue
        while end < len(lines) and not lines[end].strip() and not rendered:
            end += 1  # a removed key takes its blank line with it
        lines[start:end] = rendered
    _save(root, path, "\n".join(lines) + "\n")


def _search_lines(key: str, value: Any) -> list[str]:
    if key == "markets":
        items = []
        for m in value or []:
            modes = [x for x in m.get("modes") or [] if x in MODES]
            if not (m.get("area") or "").strip() or not modes:
                raise CvacError(
                    "each market needs an area and at least one mode (onsite, hybrid, remote)"
                )
            item = {"area": m["area"].strip(), "modes": modes}
            if (m.get("country") or "").strip():
                item["country"] = m["country"].strip()
            if (m.get("note") or "").strip():
                item["note"] = m["note"].strip()
            items.append(f"  - {scalar(item)}")
        if not items:
            raise CvacError("at least one market is required")
        return ["markets:"] + items
    if key == "salary":
        if not value or value.get("min") in (None, ""):
            return []  # the schema has no null salary: the key goes away
        salary = {
            "min": value["min"],
            "currency": value.get("currency") or "EUR",
            "period": value.get("period") or "year",
        }
        return [f"salary: {scalar(salary)}"]
    if key in ("target_roles", "adjacent_roles", "cv_languages", "red_flags"):
        items = [x.strip() for x in value or [] if x and x.strip()]
        if key == "target_roles" and not items:
            raise CvacError("at least one target role is required")
        if key == "cv_languages" and any(not re.match(r"^[a-z]{2}$", x) for x in items):
            raise CvacError("cv_languages are ISO 639-1 codes")
        return [f"{key}: {scalar(items)}"]
    if key == "confidential":
        return [f"confidential: {scalar(bool(value))}"]
    raise CvacError(f"`{key}` is not a field of search.yaml the form edits")


def own_note_quotes(root: DataRoot, user: str) -> dict[str, str]:
    """anchor -> the person's words, for the curriculum page."""
    path = root.user_dir(user) / "notes" / f"{OWN_NOTE}.md"
    if not path.is_file():
        return {}
    doc = load_document(path, root.rel(path))
    return {str(f.get("anchor")): str(f.get("quote")) for f in doc.get("facts") or []}
