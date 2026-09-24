"""The data area: documents in, questionnaires, a validating editor, new users."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from ..dataroot import DataRoot
from ..documents import load_document
from ..errors import CvacError
from ..scaffold import init_user
from ..validate import validate_files
from . import views
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
            if not p.is_file() or p.name == "README.md" and sub == "inbox":
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

    return {
        "inbox": files("inbox"),
        "sources": files("sources"),
        "interviews": files("interviews", {".md"}),
        "notes": files("notes", {".md"}),
        "growth": files("growth", {".md"}),
    }


def next_questionnaire_name(udir: Path) -> str:
    base = udir / "interviews"
    n = len(list(base.glob("*.md"))) + 1 if base.is_dir() else 1
    return f"{n:02d}-onboarding" if n == 1 else f"{n:02d}-update"


def editable(rel: str) -> bool:
    return any(rx.match(rel) for rx in EDITABLE)


def save_validated(root: DataRoot, path: Path, text: str) -> list[str]:
    """Write text, validate the file; on errors restore the previous content and return them."""
    before = path.read_text("utf-8") if path.is_file() else None
    path.write_text(text, "utf-8")
    rep = validate_files(root, [path])
    if rep.errors:
        if before is None:
            path.unlink()
        else:
            path.write_text(before, "utf-8")
        return rep.errors
    for w in rep.warnings:
        flash(w, "warn")
    return []


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
    file = request.files.get("file")
    name = secure_filename(file.filename or "") if file else ""
    if not file or not name:
        flash("choose a file to upload", "error")
        return redirect(back)
    if Path(name).suffix.lower() not in UPLOAD_SUFFIXES:
        flash(
            f"`{name}`: unsupported type (allowed: {', '.join(sorted(UPLOAD_SUFFIXES))})", "error"
        )
        return redirect(back)
    target = udir / "inbox" / name
    if target.exists():
        flash(f"inbox/{name} already exists; rename the file", "error")
        return redirect(back)
    target.parent.mkdir(parents=True, exist_ok=True)
    file.save(target)
    flash(f"inbox/{name} uploaded; extract it when ready (stage 03)", "ok")
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
        flash(f"`{document}` is not a document under inbox/, sources/ or interviews/", "error")
        return redirect(back)
    if not NAME_RE.match(name):
        flash(f"`{name}` is not a note name (lowercase letters, digits and dashes)", "error")
        return redirect(back)
    try:
        r = state().runs.start(
            root, "03_extract", {"user": user, "document": document, "name": name}, back
        )
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
        flash(f"`{name}` is not an evidence note under notes/", "error")
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
            f"`{name}` is not a questionnaire name (lowercase letters, digits and dashes)", "error"
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
        errors = save_validated(root, path, text)
        if not errors:
            flash(f"{rel} saved and valid", "ok")
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
            f"user `{form['slug']}` created; next: a questionnaire, or documents to extract", "ok"
        )
        return redirect(url_for("data.documents", user=form["slug"]))
    return render_template("new_user.html", form=form)
