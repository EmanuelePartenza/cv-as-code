"""The curriculum page: one place for everything about the person, to confirm and complete."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import curriculum as lib
from ..dataroot import DataRoot, load_yaml
from ..errors import CvacError
from ..report import evidence_quote, profile_data
from . import views
from .i18n import t
from .state import current_root

bp = Blueprint("curriculum", __name__)


def hints(entry: dict[str, Any]) -> list[str]:
    """The questionnaire's questions, asked where the entry lacks something."""
    out = []
    if not entry["facts"]:
        out.append(t("What did you actually do here? One line per thing, as concrete as you can."))
    elif not any(f["metrics"] for f in entry["facts"] if f["status"] != "rejected"):
        out.append(t("Numbers, where they are real: volumes, counts, money, people, frequency."))
    if not entry["start"]:
        out.append(t("When did it start? A year or a month is enough."))
    drafts = sum(1 for f in entry["facts"] if f["status"] == "draft")
    if drafts:
        out.append(
            t("{n} fact(s) await your decision: confirm, reword or reject each one.", n=drafts)
        )
    return out


def page_data(root: DataRoot, user: str) -> dict[str, Any]:
    user_dir = views.user_dir_of(root, user)
    data = profile_data(root, user)
    profile = load_yaml(root.profile_path(user))
    for entry in data["entries"]:
        raw = next(
            (
                e
                for k in ("experiences", "projects")
                for e in profile.get(k) or []
                if e.get("id") == entry["id"]
            ),
            {},
        )
        entry["company_name"] = (raw.get("company") or {}).get("name")
        entry["location"] = (raw.get("company") or {}).get("location")
        entry["industry"] = (raw.get("company") or {}).get("industry")
        entry["end"] = raw.get("end")
        entry["kind"] = "prj" if entry["id"].startswith("prj-") else "exp"
        entry["hints"] = hints(entry)
        for fact in entry["facts"]:
            for ev in fact["evidence"]:
                ev["quote"] = evidence_quote(user_dir, ev["ref"]) if ev["exists"] else None
    search_path = user_dir / "search.yaml"
    search = load_yaml(search_path) if search_path.is_file() else {}
    return {
        **data,
        "raw": profile,
        "search": search if isinstance(search, dict) else {},
        "experiences": [e for e in data["entries"] if e["kind"] == "exp"],
        "projects": [e for e in data["entries"] if e["kind"] == "prj"],
        "all_facts": [f for e in data["entries"] for f in e["facts"] if f["status"] != "rejected"],
    }


def _back(user: str, anchor: str | None = None) -> str:
    return url_for("curriculum.page", user=user) + (f"#{anchor}" if anchor else "")


def _do(user: str, anchor: str | None, message: str, action) -> Any:
    """Run one library call from a form; refusals come back as messages, never as tracebacks."""
    try:
        result = action()
        flash(message.format(id=result) if result else message, "ok")
    except CvacError as e:
        flash(str(e), "error")
    return redirect(_back(user, anchor))


@bp.get("/u/<user>/curriculum")
def page(user: str) -> str:
    return render_template("curriculum.html", p=page_data(current_root(), user))


@bp.post("/u/<user>/curriculum/identity")
def identity(user: str):
    root = current_root()
    f = request.form
    links = []
    for line in (f.get("links") or "").splitlines():
        if line.strip():
            label, _, url = line.partition("|")
            if not url.strip():
                label, url = "", label
            links.append((label.strip(), url.strip()))
    return _do(
        user,
        "identity",
        t("identity saved"),
        lambda: lib.set_identity(
            root,
            user,
            full_name=f.get("full_name", ""),
            email=f.get("email", ""),
            city=f.get("city", ""),
            country=f.get("country"),
            phone=f.get("phone"),
            born=f.get("born"),
            links=links,
        ),
    )


@bp.post("/u/<user>/curriculum/language")
def language(user: str):
    root = current_root()
    f = request.form
    return _do(
        user,
        "languages",
        t("language added"),
        lambda: lib.add_language(root, user, f.get("code", ""), f.get("level", ""), f.get("note")),
    )


@bp.post("/u/<user>/curriculum/entry")
def entry_new(user: str):
    root = current_root()
    f = request.form
    kind = f.get("kind", "exp")
    return _do(
        user,
        None,
        t("added: {id}. Now the facts: what you did there, one line each."),
        lambda: lib.add_entry(
            root,
            user,
            kind,
            role=f.get("role", ""),
            company=f.get("company"),
            location=f.get("location"),
            industry=f.get("industry"),
            start=f.get("start"),
            end=f.get("end"),
        ),
    )


@bp.post("/u/<user>/curriculum/entry/<entry_id>")
def entry_update(user: str, entry_id: str):
    root = current_root()
    f = request.form
    fields = {
        k: f.get(k) for k in ("role", "company", "location", "industry", "start", "end") if k in f
    }
    return _do(
        user,
        entry_id,
        t("{id} updated").format(id=entry_id),
        lambda: lib.update_entry(root, user, entry_id, **fields) or entry_id,
    )


@bp.post("/u/<user>/curriculum/entry/<entry_id>/fact")
def fact_new(user: str, entry_id: str):
    root = current_root()
    f = request.form
    confirm = f.get("action") == "confirm"

    def act() -> str:
        return lib.add_own_fact(
            root,
            user,
            entry_id,
            f.get("claim", ""),
            metrics=lib.parse_metrics(f.get("metrics", "")),
            tags=[x.strip() for x in (f.get("tags") or "").split(",") if x.strip()],
            confirm=confirm,
        )

    message = (
        t("{id} added and confirmed")
        if confirm
        else t("{id} added as draft; confirm it when you are sure")
    )
    return _do(user, entry_id, message, act)


@bp.post("/u/<user>/curriculum/education")
def education(user: str):
    root = current_root()
    f = request.form
    return _do(
        user,
        "education",
        t("education added: {id}"),
        lambda: lib.add_education(
            root,
            user,
            degree=f.get("degree", ""),
            institution=f.get("institution", ""),
            location=f.get("location"),
            start=f.get("start"),
            end=f.get("end"),
        ),
    )


@bp.post("/u/<user>/curriculum/skill")
def skill(user: str):
    root = current_root()
    f = request.form
    return _do(
        user,
        "skills",
        t("skill added: {id}"),
        lambda: lib.add_skill(
            root,
            user,
            name=f.get("name", ""),
            category=f.get("category", ""),
            evidence_facts=f.getlist("evidence_facts"),
        ),
    )


@bp.post("/u/<user>/curriculum/search")
def search(user: str):
    root = current_root()
    f = request.form

    def lines(key: str) -> list[str]:
        return [x.strip() for x in (f.get(key) or "").replace("\n", ",").split(",") if x.strip()]

    markets = []
    for line in (f.get("markets") or "").splitlines():
        if not line.strip():
            continue
        parts = [x.strip() for x in line.split("|")]
        area = parts[0] if parts else ""
        country = parts[1] if len(parts) > 1 else ""
        modes = [
            m.strip() for m in (parts[2] if len(parts) > 2 else "onsite, hybrid, remote").split(",")
        ]
        markets.append({"area": area, "country": country, "modes": modes})
    salary = {
        "min": f.get("salary_min") or None,
        "currency": f.get("currency"),
        "period": f.get("period"),
    }
    if salary["min"] not in (None, ""):
        try:
            salary["min"] = int(str(salary["min"]).replace(" ", ""))
        except ValueError:
            flash(t("the salary floor must be a number"), "error")
            return redirect(_back(user, "search"))
    return _do(
        user,
        "search",
        t("search parameters saved"),
        lambda: lib.set_search(
            root,
            user,
            target_roles=lines("target_roles"),
            adjacent_roles=lines("adjacent_roles"),
            cv_languages=lines("cv_languages"),
            confidential=f.get("confidential") == "on",
            salary=salary,
            red_flags=lines("red_flags"),
            markets=markets,
        ),
    )
