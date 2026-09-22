"""The profile report: a generated Markdown view of a user's profile, and what it lacks.

The storage shape (nested facts under experiences) is right for an agent and hostile
to a person; the human view is derived, never stored (ADR-0013). Written to
users/<slug>/profile.report.md, which data roots gitignore.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .dataroot import DataRoot, load_yaml
from .errors import CvacError
from .validate import evidence_list


def _cell(value: Any, width: int = 90) -> str:
    text = " ".join(str(value or "").split())
    text = text.replace("|", "\\|")
    return text if len(text) <= width else text[: width - 1] + "…"


def _dates(entry: dict[str, Any]) -> str:
    start = entry.get("start") or "?"
    end = entry.get("end") or "ongoing"
    return f"{start} → {end}"


def _fact_view(fact: dict[str, Any], user_dir: Path) -> dict[str, Any]:
    evidence = []
    for ref in evidence_list(fact.get("evidence")):
        file, _, anchor = ref.partition("#")
        evidence.append(
            {
                "ref": ref,
                "file": file,
                "anchor": anchor or None,
                "exists": (user_dir / file).exists(),
            }
        )
    return {
        "id": fact.get("id"),
        "status": fact.get("status"),
        "verified_on": fact.get("verified_on"),
        "claim": fact.get("claim"),
        "metrics": dict(fact.get("metrics") or {}),
        "tags": list(fact.get("tags") or []),
        "evidence": evidence,
        "evidence_ok": bool(evidence) and all(e["exists"] for e in evidence),
    }


def profile_data(root: DataRoot, user: str) -> dict[str, Any]:
    """The profile as a person reads it: entries with their facts, evidence resolution, gaps."""
    profile_path = root.profile_path(user)
    if not profile_path.is_file():
        raise CvacError(f"profile not found: {root.rel(profile_path)}")
    profile = load_yaml(profile_path)
    user_dir = profile_path.parent
    ident = dict(profile.get("identity") or {})
    entries = []
    for e in list(profile.get("experiences") or []) + list(profile.get("projects") or []):
        entries.append(
            {
                "id": e.get("id"),
                "role": e.get("role"),
                "company": (e.get("company") or {}).get("name"),
                "dates": _dates(e),
                "start": e.get("start"),
                "facts": [_fact_view(f, user_dir) for f in e.get("facts") or []],
            }
        )
    all_facts = [f for e in entries for f in e["facts"]]
    counts = {
        s: sum(1 for f in all_facts if f["status"] == s) for s in ("verified", "draft", "rejected")
    }
    skills = [
        {
            "id": s.get("id"),
            "name": s.get("name"),
            "category": s.get("category"),
            "evidence_facts": list(s.get("evidence_facts") or []),
        }
        for s in profile.get("skills") or []
    ]
    education = [
        {"degree": ed.get("degree"), "institution": ed.get("institution"), "dates": _dates(ed)}
        for ed in profile.get("education") or []
    ]
    languages = [
        {"code": lg.get("code"), "level": lg.get("level"), "note": lg.get("note")}
        for lg in profile.get("languages") or []
    ]

    # --- completeness: what a person or the update-mode interview can act on ---
    todo: list[str] = []
    for f in all_facts:
        if not f["evidence"]:
            todo.append(f"fact `{f['id']}` has no evidence")
        for ev in f["evidence"]:
            if not ev["exists"]:
                todo.append(f"fact `{f['id']}` evidence `{ev['ref']}` does not exist")
        if f["status"] == "draft":
            todo.append(f"fact `{f['id']}` is draft: confirm or reject it")
        if not f["metrics"] and f["status"] != "rejected":
            todo.append(f"fact `{f['id']}` carries no number")
    for e in entries:
        if not e["facts"]:
            todo.append(f"`{e['id']}` has no facts")
        if not e["start"]:
            todo.append(f"`{e['id']}` has no start date")
    for s in skills:
        if not s["evidence_facts"]:
            todo.append(f"skill `{s['id']}` has no evidence facts")
    for key in ("email", "location"):
        if not ident.get(key):
            todo.append(f"identity.{key} is empty")
    for lg in languages:
        if not lg["level"]:
            todo.append(f"language `{lg['code']}` has no level")

    return {
        "user": user,
        "full_name": ident.get("full_name") or user,
        "pivot_language": profile.get("pivot_language"),
        "identity": ident,
        "entries": entries,
        "skills": skills,
        "education": education,
        "languages": languages,
        "counts": counts,
        "todo": todo,
    }


def evidence_quote(user_dir: Path, ref: str) -> str | None:
    """The passage under `## <anchor>` in an evidence note; None without an anchor or a match."""
    file, _, anchor = ref.partition("#")
    path = user_dir / file
    if not anchor or not path.is_file():
        return None
    out: list[str] = []
    inside = False
    for line in path.read_text("utf-8").splitlines():
        if line.startswith("#"):
            if inside:
                break
            inside = line.strip("# ").strip() == anchor
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip() or None


def _facts_table(facts: list[dict[str, Any]]) -> list[str]:
    lines = ["| id | status | claim | metrics | evidence | tags |", "|---|---|---|---|---|---|"]
    for f in facts:
        mark = "✓" if f["evidence_ok"] else ("✗ missing" if f["evidence"] else "✗ none")
        metrics = ", ".join(f"{k}={v}" for k, v in f["metrics"].items())
        lines.append(
            f"| `{f['id']}` | {f['status']} | {_cell(f['claim'])} "
            f"| {_cell(metrics, 40)} | {mark} | {_cell(', '.join(f['tags']), 40)} |"
        )
    return lines


def build_report(root: DataRoot, user: str) -> str:
    data = profile_data(root, user)
    ident = data["identity"]
    out: list[str] = [
        f"# Profile report — {data['full_name']} (`{user}`)",
        "",
        f"Generated {date.today().isoformat()} by `cvac profile report`; derived, never edited "
        f"by hand. Pivot language: `{data['pivot_language']}`.",
        "",
        "## Identity",
        "",
        "| field | value |",
        "|---|---|",
    ]
    for key in ("full_name", "location", "email", "phone", "born"):
        value = ident.get(key)
        if isinstance(value, dict):
            value = ", ".join(str(v) for v in value.values() if v)
        out.append(f"| {key} | {_cell(value) or '_(empty)_'} |")
    links = ", ".join(lk.get("url", "") for lk in ident.get("links") or [])
    out.append(f"| links | {_cell(links) or '_(none)_'} |")

    out += [
        "",
        "## Timeline",
        "",
        "| id | role | organisation | dates | facts |",
        "|---|---|---|---|---|",
    ]
    for e in data["entries"]:
        out.append(
            f"| `{e['id']}` | {_cell(e['role'], 40)} | {_cell(e['company'] or '—', 40)} "
            f"| {e['dates']} | {len(e['facts'])} |"
        )

    out += ["", "## Facts", ""]
    for e in data["entries"]:
        out += [f"### `{e['id']}` — {e['role']}", ""]
        out += _facts_table(e["facts"]) if e["facts"] else ["_(no facts)_"]
        out.append("")

    out += ["## Skills", "", "| skill | category | evidence facts |", "|---|---|---|"]
    for s in data["skills"]:
        ev = s["evidence_facts"]
        out.append(
            f"| {_cell(s['name'], 40)} | {s['category']} | "
            f"{', '.join(f'`{x}`' for x in ev) if ev else '✗ none'} |"
        )

    out += ["", "## Education", "", "| degree | institution | dates |", "|---|---|---|"]
    for ed in data["education"]:
        out.append(
            f"| {_cell(ed['degree'], 50)} | {_cell(ed['institution'], 50)} | {ed['dates']} |"
        )

    out += ["", "## Languages", ""]
    for lg in data["languages"]:
        note = f" — {lg['note']}" if lg["note"] else ""
        out.append(f"- {lg['code']}: {lg['level']}{note}")

    counts = data["counts"]
    out += [
        "",
        "## Completeness",
        "",
        f"- facts: {counts['verified']} verified, {counts['draft']} draft, "
        f"{counts['rejected']} rejected",
    ]
    todo = data["todo"]
    out += (
        [f"- [ ] {t}" for t in todo] if todo else ["- nothing missing that the framework can see"]
    )
    out.append("")
    return "\n".join(out)


def write_report(root: DataRoot, user: str) -> Path:
    path = root.user_dir(user) / "profile.report.md"
    path.write_text(build_report(root, user), "utf-8")
    return path
