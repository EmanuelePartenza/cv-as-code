"""The jobs area: a posting enters verbatim, then the stages run on it from buttons."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..dataroot import DataRoot
from ..documents import load_document
from ..errors import CvacError
from . import views
from .state import current_root, state

bp = Blueprint("jobs", __name__)

JOB_ID_RE = re.compile(r"^\d{8}-[a-z0-9]+(-[a-z0-9]+)*$")
JOB_STAGES = (
    "10_normalize",
    "20_match",
    "30_tailor",
    "60_letter",
    "70_interview_prep",
    "40_gap_plan",
)


def slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (text or "").lower())).strip("-")


def job_id_for(day: str, company: str, title: str) -> str:
    try:
        stamp = date.fromisoformat(day).strftime("%Y%m%d")
    except ValueError as e:
        raise CvacError(f"`{day}` is not a date (YYYY-MM-DD)") from e
    job_id = f"{stamp}-{slug(company)}-{slug(title)}"
    if not JOB_ID_RE.match(job_id):
        raise CvacError("company and role must each contain at least one letter or digit")
    return job_id


def raw_text(channel: str, company: str, title: str, url: str, day: str, text: str) -> str:
    head = [
        f"SOURCE: {channel.strip() or 'unknown'}",
        f"COMPANY: {company.strip()}",
        f"TITLE: {title.strip()}",
    ]
    if url.strip():
        head.append(f"URL: {url.strip()}")
    head.append(f"NOTE: pasted on {day} through cvac ui; the text below is verbatim.")
    return "\n".join(head) + "\n---\n" + text.strip() + "\n"


def create_job(
    root: DataRoot, day: str, channel: str, company: str, title: str, url: str, text: str
) -> str:
    if not text.strip():
        raise CvacError("paste the posting's text")
    job_id = job_id_for(day, company, title)
    d = root.job_dir(job_id)
    if d.exists():
        raise CvacError(f"jobs/{job_id}/ already exists; postings are never overwritten")
    d.mkdir(parents=True)
    (d / "raw.txt").write_text(raw_text(channel, company, title, url, day, text), "utf-8")
    return job_id


def _doc(path: Path, root: DataRoot) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        doc = load_document(path, root.rel(path))
    except CvacError:
        return {"invalid": True}
    return doc if isinstance(doc, dict) else {"invalid": True}


def job_state(root: DataRoot, user: str, job_id: str) -> dict[str, Any]:
    d = root.job_dir(job_id)
    udir = root.user_dir(user)
    app = udir / "applications" / job_id
    job = _doc(d / "job.yaml", root)
    match = _doc(udir / "matches" / f"{job_id}.yaml", root)
    spec = _doc(app / "cv-spec.yaml", root)
    letter = _doc(app / "letter.md", root)
    prep = _doc(app / "interview-prep.md", root)
    growth = _doc(udir / "growth" / f"{job_id}.md", root)
    raw = d / "raw.txt"
    return {
        "id": job_id,
        "user": user,
        "raw": raw.read_text("utf-8") if raw.is_file() else None,
        "job": job,
        "title": (job or {}).get("title") or _raw_field(raw, "TITLE"),
        "company": ((job or {}).get("company") or {}).get("name") or _raw_field(raw, "COMPANY"),
        "match": match,
        "verdict": (match or {}).get("verdict"),
        "spec": spec,
        "spec_status": (spec or {}).get("status"),
        "letter": letter,
        "letter_status": (letter or {}).get("status"),
        "prep": prep,
        "growth": growth,
        "texts": {
            "match": _text(udir / "matches" / f"{job_id}.yaml"),
            "growth": _text(udir / "growth" / f"{job_id}.md"),
            "prep": _text(app / "interview-prep.md"),
        },
    }


def _raw_field(raw: Path, key: str) -> str | None:
    if not raw.is_file():
        return None
    for line in raw.read_text("utf-8").splitlines()[:8]:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def _text(path: Path) -> str | None:
    return path.read_text("utf-8") if path.is_file() else None


def jobs(root: DataRoot, user: str) -> list[dict[str, Any]]:
    if not root.jobs_dir.is_dir():
        return []
    return [
        job_state(root, user, d.name)
        for d in sorted(root.jobs_dir.iterdir(), reverse=True)
        if d.is_dir() and JOB_ID_RE.match(d.name)
    ]


def masters(root: DataRoot, user: str) -> list[str]:
    base = root.user_dir(user) / "masters"
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if (d / "cv-spec.yaml").is_file())


def _job_id(root: DataRoot, job_id: str) -> str:
    if not JOB_ID_RE.match(job_id) or not root.job_dir(job_id).is_dir():
        raise views.NotFound(f"no job `{job_id}`")
    return job_id


@bp.get("/u/<user>/jobs")
def listing(user: str) -> str:
    root = current_root()
    views.user_dir_of(root, user)
    return render_template(
        "jobs.html", user=user, jobs=jobs(root, user), today=date.today().isoformat()
    )


@bp.post("/u/<user>/jobs/new")
def new(user: str):
    root = current_root()
    views.user_dir_of(root, user)
    f = request.form
    try:
        job_id = create_job(
            root,
            f.get("date", ""),
            f.get("channel", ""),
            f.get("company", ""),
            f.get("title", ""),
            f.get("url", ""),
            f.get("text", ""),
        )
    except CvacError as e:
        flash(str(e), "error")
        return redirect(url_for("jobs.listing", user=user))
    flash(f"jobs/{job_id}/raw.txt written; next: normalise it (stage 10)", "ok")
    return redirect(url_for("jobs.job", user=user, job_id=job_id))


@bp.get("/u/<user>/jobs/<job_id>")
def job(user: str, job_id: str) -> str:
    root = current_root()
    views.user_dir_of(root, user)
    _job_id(root, job_id)
    return render_template("job.html", j=job_state(root, user, job_id), masters=masters(root, user))


@bp.post("/u/<user>/jobs/<job_id>/run/<stage>")
def run(user: str, job_id: str, stage: str):
    root = current_root()
    views.user_dir_of(root, user)
    _job_id(root, job_id)
    if stage not in JOB_STAGES:
        raise views.NotFound(f"stage `{stage}` does not run on a job")
    params = {"user": user, "job_id": job_id}
    if request.form.get("master"):
        params["master"] = request.form["master"]
    back = url_for("jobs.job", user=user, job_id=job_id)
    try:
        r = state().runs.start(root, stage, params, back)
    except CvacError as e:
        flash(str(e), "error")
        return redirect(back)
    return redirect(url_for("runs.run", run_id=r.id))
