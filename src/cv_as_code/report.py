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


def _facts_table(entries: list[dict[str, Any]], user_dir: Path) -> list[str]:
    lines = ["| id | status | claim | metrics | evidence | tags |", "|---|---|---|---|---|---|"]
    for fact in entries:
        paths = evidence_list(fact.get("evidence"))
        ok = bool(paths) and all((user_dir / p.split("#", 1)[0]).exists() for p in paths)
        mark = "✓" if ok else ("✗ missing" if paths else "✗ none")
        metrics = ", ".join(f"{k}={v}" for k, v in (fact.get("metrics") or {}).items())
        lines.append(
            f"| `{fact.get('id')}` | {fact.get('status')} | {_cell(fact.get('claim'))} "
            f"| {_cell(metrics, 40)} | {mark} | {_cell(', '.join(fact.get('tags') or []), 40)} |"
        )
    return lines


def _dates(entry: dict[str, Any]) -> str:
    start = entry.get("start") or "?"
    end = entry.get("end") or "ongoing"
    return f"{start} → {end}"


def build_report(root: DataRoot, user: str) -> str:
    profile_path = root.profile_path(user)
    if not profile_path.is_file():
        raise CvacError(f"profile not found: {root.rel(profile_path)}")
    profile = load_yaml(profile_path)
    user_dir = profile_path.parent
    ident = profile.get("identity") or {}
    entries = list(profile.get("experiences") or []) + list(profile.get("projects") or [])
    all_facts = [f for e in entries for f in (e.get("facts") or [])]
    counts = {
        s: sum(1 for f in all_facts if f.get("status") == s)
        for s in ("verified", "draft", "rejected")
    }

    out: list[str] = [
        f"# Profile report — {ident.get('full_name', user)} (`{user}`)",
        "",
        f"Generated {date.today().isoformat()} by `cvac profile report`; derived, never edited "
        f"by hand. Pivot language: `{profile.get('pivot_language')}`.",
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
    for e in entries:
        company = (e.get("company") or {}).get("name") or "—"
        out.append(
            f"| `{e.get('id')}` | {_cell(e.get('role'), 40)} | {_cell(company, 40)} "
            f"| {_dates(e)} | {len(e.get('facts') or [])} |"
        )

    out += ["", "## Facts", ""]
    for e in entries:
        out += [f"### `{e.get('id')}` — {e.get('role')}", ""]
        facts = e.get("facts") or []
        out += _facts_table(facts, user_dir) if facts else ["_(no facts)_"]
        out.append("")

    out += ["## Skills", "", "| skill | category | evidence facts |", "|---|---|---|"]
    for s in profile.get("skills") or []:
        ev = s.get("evidence_facts") or []
        out.append(
            f"| {_cell(s.get('name'), 40)} | {s.get('category')} | "
            f"{', '.join(f'`{x}`' for x in ev) if ev else '✗ none'} |"
        )

    out += ["", "## Education", "", "| degree | institution | dates |", "|---|---|---|"]
    for ed in profile.get("education") or []:
        out.append(
            f"| {_cell(ed.get('degree'), 50)} | {_cell(ed.get('institution'), 50)} | {_dates(ed)} |"
        )

    out += ["", "## Languages", ""]
    for lg in profile.get("languages") or []:
        note = f" — {lg['note']}" if lg.get("note") else ""
        out.append(f"- {lg.get('code')}: {lg.get('level')}{note}")

    # --- completeness: what a person or the update-mode interview can act on ---
    out += [
        "",
        "## Completeness",
        "",
        f"- facts: {counts['verified']} verified, {counts['draft']} draft, "
        f"{counts['rejected']} rejected",
    ]
    todo: list[str] = []
    for f in all_facts:
        paths = evidence_list(f.get("evidence"))
        if not paths:
            todo.append(f"fact `{f.get('id')}` has no evidence")
        for p in paths:
            if not (user_dir / p.split("#", 1)[0]).exists():
                todo.append(f"fact `{f.get('id')}` evidence `{p}` does not exist")
        if f.get("status") == "draft":
            todo.append(f"fact `{f.get('id')}` is draft: confirm or reject it")
        if not (f.get("metrics") or {}) and f.get("status") != "rejected":
            todo.append(f"fact `{f.get('id')}` carries no number")
    for e in entries:
        if not e.get("facts"):
            todo.append(f"`{e.get('id')}` has no facts")
        if not e.get("start"):
            todo.append(f"`{e.get('id')}` has no start date")
    for s in profile.get("skills") or []:
        if not s.get("evidence_facts"):
            todo.append(f"skill `{s.get('id')}` has no evidence facts")
    for key in ("email", "location"):
        if not ident.get(key):
            todo.append(f"identity.{key} is empty")
    for lg in profile.get("languages") or []:
        if not lg.get("level"):
            todo.append(f"language `{lg.get('code')}` has no level")
    out += (
        [f"- [ ] {t}" for t in todo] if todo else ["- nothing missing that the framework can see"]
    )
    out.append("")
    return "\n".join(out)


def write_report(root: DataRoot, user: str) -> Path:
    path = root.user_dir(user) / "profile.report.md"
    path.write_text(build_report(root, user), "utf-8")
    return path
