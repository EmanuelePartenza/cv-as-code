"""The review area: each proposed fact with its passage, to verify, reject or reword."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..dataroot import DataRoot
from ..errors import CvacError
from ..facts import set_claim, set_status
from ..report import evidence_quote, profile_data
from . import views
from .i18n import t
from .state import current_root

bp = Blueprint("review", __name__)


def groups(root: DataRoot, user: str, only_draft: bool = True) -> list[dict[str, Any]]:
    """Facts grouped by the note that evidences them, each with its quote; drafts first."""
    user_dir = views.user_dir_of(root, user)
    data = profile_data(root, user)
    by_note: dict[str, dict[str, Any]] = {}
    for entry in data["entries"]:
        for fact in entry["facts"]:
            if only_draft and fact["status"] != "draft":
                continue
            key = fact["evidence"][0]["file"] if fact["evidence"] else ""
            group = by_note.setdefault(key, {"note": key or None, "facts": []})
            quotes = [
                evidence_quote(user_dir, ev["ref"]) if ev["exists"] else None
                for ev in fact["evidence"]
            ]
            group["facts"].append(
                {**fact, "parent": entry["id"], "role": entry["role"], "quotes": quotes}
            )
    return sorted(by_note.values(), key=lambda g: g["note"] or "", reverse=True)


@bp.get("/u/<user>/review")
def review(user: str) -> str:
    root = current_root()
    data = profile_data(root, user)
    return render_template(
        "review.html",
        user=user,
        groups=groups(root, user),
        counts=data["counts"],
        todo=data["todo"],
    )


@bp.post("/u/<user>/review/<action>")
def act(user: str, action: str):
    root = current_root()
    views.user_dir_of(root, user)
    if action not in ("verify", "reject"):
        raise views.NotFound(f"no action `{action}`")
    ids = [i for i in request.form.getlist("ids") if i]
    nxt = request.form.get("next") or ""
    back = redirect(
        nxt
        if nxt.startswith("/") and not nxt.startswith("//")
        else url_for("review.review", user=user)
    )
    if not ids:
        flash(t("select at least one fact"), "error")
        return back
    done: list[str] = []
    for fid in ids:
        try:
            change = set_status(
                root, user, [fid], "verified" if action == "verify" else "rejected"
            )[0]
            done.append(f"{change.fact_id}: {change.old_status} → {change.new_status}")
        except CvacError as e:
            flash(str(e), "error")
    if done:
        flash("; ".join(done), "ok")
    return back


@bp.post("/u/<user>/fact/<fact_id>/claim")
def claim(user: str, fact_id: str):
    root = current_root()
    views.user_dir_of(root, user)
    back = request.form.get("next") or url_for("review.review", user=user)
    if not back.startswith("/") or back.startswith("//"):
        back = url_for("review.review", user=user)
    try:
        change = set_claim(root, user, fact_id, request.form.get("claim", ""))
        if change.old_status != change.new_status:
            flash(t("{id} reworded and back to draft: verify it again", id=fact_id), "ok")
        else:
            flash(t("{id} reworded", id=fact_id), "ok")
    except CvacError as e:
        flash(str(e), "error")
    return redirect(back)
