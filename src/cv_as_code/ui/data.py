"""The data area: documents in, questionnaires, a validating editor, new users."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from ..apply import archive_batch
from ..dataroot import DataRoot
from ..documents import load_document
from ..errors import CvacError
from ..scaffold import init_user
from ..validate import write_validated
from . import views
from .i18n import t
from .state import current_root, state

bp = Blueprint("data", __name__)

EDITABLE = (
    re.compile(r"^profile\.yaml$"),
    re.compile(r"^search\.yaml$"),
    re.compile(r"^(interviews|notes|growth)/[a-z0-9][a-z0-9-]*\.md$"),
)
UPLOAD_SUFFIXES = {".md", ".txt", ".pdf", ".docx", ".csv", ".yaml", ".json"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _status(path: Path, root: DataRoot) -> str | None:
    try:
        doc = load_document(path, root.rel(path))
    except CvacError:
        return "invalid"
    return str(doc.get("status")) if isinstance(doc, dict) and doc.get("status") else None


def listing(root: DataRoot, user: str) -> dict[str, Any]:
    udir = views.user_dir_of(root, user)

    def files(sub: str, suffixes: set[str] | None = None) -> list[dict[str, Any]]:
        base = udir / sub
        if not base.is_dir():
            return []
        out = []
        for p in sorted(base.iterdir()):
            if (
                not p.is_file()
                or p.name.startswith(".")
                or (p.name == "README.md" and sub == "inbox")
            ):
                continue
            if suffixes and p.suffix.lower() not in suffixes:
                continue
            out.append(
                {
                    "name": p.name,
                    "rel": f"{sub}/{p.name}",
                    "status": _status(p, root) if p.suffix == ".md" else None,
                }
            )
        return out

    notes = files("notes", {".md"})
    sources_of_notes = {_source_of(udir / "notes" / n["name"], root) for n in notes}
    index = sources_index(root, user)
    inbox, sources = files("inbox"), files("sources")
    for f in inbox + sources:
        entry = index.get(f["rel"]) or {}
        f["kind"] = entry.get("kind")
        f["about"] = entry.get("about")
        f["duplicate_of"] = entry.get("duplicate_of")
        f["extracted"] = f["rel"] in sources_of_notes or bool(entry.get("note"))
        f["pending"] = not f["extracted"] and f["kind"] in (None, "evidence")
    return {
        "inbox": inbox,
        "sources": sources,
        "interviews": files("interviews", {".md"}),
        "notes": notes,
        "growth": files("growth", {".md"}),
        "triaged": bool(index),
    }


def sources_index(root: DataRoot, user: str) -> dict[str, dict[str, Any]]:
    """The triage's verdict per document path, empty when there is no (valid) index yet."""
    path = root.user_dir(user) / "sources.yaml"
    if not path.is_file():
        return {}
    try:
        doc = load_document(path, root.rel(path))
    except CvacError:
        return {}
    if not isinstance(doc, dict):
        return {}
    return {str(d.get("path")): d for d in doc.get("documents") or [] if d.get("path")}


def _source_of(note: Path, root: DataRoot) -> str | None:
    try:
        doc = load_document(note, root.rel(note))
    except CvacError:
        return None
    return str(doc.get("source")) if isinstance(doc, dict) and doc.get("source") else None


def note_name_for(filename: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-")
    return stem or "document"


def extraction_steps(user: str, document: str, name: str) -> list[tuple[str, dict[str, str]]]:
    """Extract, then apply: facts land as draft in one run; nothing becomes verified."""
    return [
        ("03_extract", {"user": user, "document": document, "name": name}),
        ("04_apply", {"user": user, "name": name}),
    ]


def next_questionnaire_name(udir: Path) -> str:
    base = udir / "interviews"
    n = len(list(base.glob("*.md"))) + 1 if base.is_dir() else 1
    return f"{n:02d}-onboarding" if n == 1 else f"{n:02d}-update"


def editable(rel: str) -> bool:
    return any(rx.match(rel) for rx in EDITABLE)


@bp.get("/u/<user>/documents")
def documents(user: str) -> str:
    root = current_root()
    udir = views.user_dir_of(root, user)
    return render_template(
        "documents.html", user=user, d=listing(root, user), next_name=next_questionnaire_name(udir)
    )


@bp.post("/u/<user>/documents/upload")
def upload(user: str):
    root = current_root()
    udir = views.user_dir_of(root, user)
    back = url_for("data.documents", user=user)
    files = [f for f in request.files.getlist("file") if f and f.filename]
    if not files:
        flash(t("choose a file to upload"), "error")
        return redirect(back)
    saved: list[str] = []
    for file in files:
        name = secure_filename(file.filename or "")
        if not name or Path(name).suffix.lower() not in UPLOAD_SUFFIXES:
            flash(
                t(
                    "`{name}`: unsupported type (allowed: {types})",
                    name=name or file.filename,
                    types=", ".join(sorted(UPLOAD_SUFFIXES)),
                ),
                "error",
            )
            continue
        target = udir / "inbox" / name
        if target.exists():
            flash(t("inbox/{name} already exists; rename the file", name=name), "error")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        file.save(target)
        saved.append(name)
    if saved:
        flash(t("{n} document(s) uploaded to inbox/; extract them when ready", n=len(saved)), "ok")
    return redirect(back)


@bp.post("/u/<user>/documents/extract")
def extract(user: str):
    root = current_root()
    udir = views.user_dir_of(root, user)
    back = url_for("data.documents", user=user)
    document = request.form.get("document", "")
    name = request.form.get("name", "").strip() or Path(document).stem
    if (
        not re.match(r"^(inbox|sources|interviews)/[^/]+$", document)
        or not (udir / document).is_file()
    ):
        flash(
            t("`{name}` is not a document under inbox/, sources/ or interviews/", name=document),
            "error",
        )
        return redirect(back)
    if not NAME_RE.match(name):
        flash(
            t("`{name}` is not a note name (lowercase letters, digits and dashes)", name=name),
            "error",
        )
        return redirect(back)
    try:
        r = state().runs.start_steps(root, extraction_steps(user, document, name), back)
    except CvacError as e:
        flash(str(e), "error")
        return redirect(back)
    return redirect(url_for("runs.run", run_id=r.id))


def _free_note_name(root: DataRoot, user: str, filename: str, taken: set[str]) -> str:
    name = note_name_for(filename)
    while name in taken or (root.user_dir(user) / "notes" / f"{name}.md").exists():
        name = (
            name + "-2"
            if not re.search(r"-\d+$", name)
            else re.sub(r"-(\d+)$", lambda m: f"-{int(m.group(1)) + 1}", name)
        )
    taken.add(name)
    return name


def plan_extractions(user: str) -> Callable[[DataRoot], list[Any]]:
    """After the triage: extract and apply every evidence document of the inbox without a note."""

    def planner(root: DataRoot) -> list[Any]:
        steps: list[Any] = []
        taken: set[str] = set()
        for rel, entry in sources_index(root, user).items():
            if entry.get("kind") != "evidence" or entry.get("note") or not rel.startswith("inbox/"):
                continue
            if not (root.user_dir(user) / rel).is_file():
                continue
            steps += extraction_steps(user, rel, _free_note_name(root, user, rel, taken))
        return steps

    return planner


def _archive_step(user: str) -> tuple[str, str, Callable[[DataRoot], list[str]]]:
    return (
        "code",
        "archive",
        lambda root: archive_batch(root, user) or ["nothing left to archive"],
    )


@bp.post("/u/<user>/documents/triage")
def triage(user: str):
    """Sort the inbox with Claude (stage 02): what is evidence, context, duplicate, irrelevant."""
    root = current_root()
    views.user_dir_of(root, user)
    back = url_for("data.documents", user=user)
    if not [f for f in listing(root, user)["inbox"]]:
        flash(t("the inbox is empty"), "error")
        return redirect(back)
    try:
        r = state().runs.start(root, "02_triage", {"user": user}, back)
    except CvacError as e:
        flash(str(e), "error")
        return redirect(back)
    return redirect(url_for("runs.run", run_id=r.id))


@bp.post("/u/<user>/documents/extract-all")
def extract_all(user: str):
    """One run: sort the inbox (02), extract and apply every evidence document, archive the rest."""
    root = current_root()
    views.user_dir_of(root, user)
    back = url_for("data.documents", user=user)
    if not [f for f in listing(root, user)["inbox"] if f["pending"] or not f["extracted"]]:
        flash(t("nothing to extract: every document in the inbox has its note"), "error")
        return redirect(back)
    steps: list[Any] = [("02_triage", {"user": user}), plan_extractions(user), _archive_step(user)]
    try:
        r = state().runs.start_steps(root, steps, back)
    except CvacError as e:
        flash(str(e), "error")
        return redirect(back)
    return redirect(url_for("runs.run", run_id=r.id))


@bp.post("/u/<user>/documents/apply")
def apply_note(user: str):
    root = current_root()
    udir = views.user_dir_of(root, user)
    back = url_for("data.documents", user=user)
    name = request.form.get("name", "").strip()
    if not NAME_RE.match(name) or not (udir / "notes" / f"{name}.md").is_file():
        flash(t("`{name}` is not an evidence note under notes/", name=name), "error")
        return redirect(back)
    try:
        r = state().runs.start(root, "04_apply", {"user": user, "name": name}, back)
    except CvacError as e:
        flash(str(e), "error")
        return redirect(back)
    return redirect(url_for("runs.run", run_id=r.id))


@bp.post("/u/<user>/documents/questionnaire")
def questionnaire(user: str):
    root = current_root()
    views.user_dir_of(root, user)
    back = url_for("data.documents", user=user)
    name = request.form.get("name", "").strip()
    if not NAME_RE.match(name):
        flash(
            t(
                "`{name}` is not a questionnaire name (lowercase letters, digits and dashes)",
                name=name,
            ),
            "error",
        )
        return redirect(back)
    try:
        r = state().runs.start(root, "05_interview", {"user": user, "name": name}, back)
    except CvacError as e:
        flash(str(e), "error")
        return redirect(back)
    return redirect(url_for("runs.run", run_id=r.id))


@bp.route("/u/<user>/edit/<path:rel>", methods=["GET", "POST"])
def edit(user: str, rel: str):
    root = current_root()
    udir = views.user_dir_of(root, user)
    if not editable(rel):
        raise views.NotFound(f"`{rel}` is not an editable data file")
    path = udir / rel
    errors: list[str] = []
    text = path.read_text("utf-8") if path.is_file() else ""
    if request.method == "POST":
        text = request.form.get("text", "").replace("\r\n", "\n")
        rep = write_validated(root, path, text)
        errors = rep.errors
        for w in rep.warnings:
            flash(w, "warn")
        if not errors:
            flash(t("{name} saved and valid", name=rel), "ok")
            return redirect(url_for("data.edit", user=user, rel=rel))
    return render_template("edit.html", user=user, rel=rel, text=text, errors=errors)


@bp.route("/new-user", methods=["GET", "POST"])
def new_user():
    root = current_root()
    form = {
        k: request.form.get(k, "").strip()
        for k in ("slug", "full_name", "email", "city", "country", "pivot_language", "target_roles")
    }
    if request.method == "POST":
        try:
            init_user(
                root,
                form["slug"],
                form["full_name"],
                form["email"],
                form["city"],
                form["country"] or None,
                form["pivot_language"] or "en",
                target_roles=[r for r in form["target_roles"].split(",")],
            )
        except CvacError as e:
            flash(str(e), "error")
            return render_template("new_user.html", form=form)
        flash(
            t(
                "user `{slug}` created; next: a questionnaire, or documents to extract",
                slug=form["slug"],
            ),
            "ok",
        )
        return redirect(url_for("start.start", user=form["slug"]))
    return render_template("new_user.html", form=form)
