"""The guided home of a user: four independent doors and where each stands."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, render_template

from ..dataroot import DataRoot
from ..report import profile_data
from . import data as data_area
from . import jobs as jobs_area
from . import views
from .state import current_root

bp = Blueprint("start", __name__)


def overview(root: DataRoot, user: str) -> dict[str, Any]:
    docs = data_area.listing(root, user)
    profile = profile_data(root, user)
    interviews = docs["interviews"]
    filled = [f for f in interviews if f["status"] == "filled"]
    return {
        "user": user,
        "full_name": profile["full_name"],
        "documents": {
            "pending": [f for f in docs["inbox"] if not f.get("extracted")],
            "extracted": [f for f in docs["inbox"] if f.get("extracted")] + docs["sources"],
            "notes_proposed": [n for n in docs["notes"] if n["status"] == "proposed"],
        },
        "questionnaire": {
            "any": bool(interviews),
            "to_fill": [f for f in interviews if f["status"] == "to-fill"],
            "filled": filled,
            "next_name": data_area.next_questionnaire_name(root.user_dir(user)),
        },
        "facts": profile["counts"],
        "todo": profile["todo"],
        "jobs": len(jobs_area.jobs(root, user)),
        "masters": jobs_area.masters(root, user),
    }


@bp.get("/u/<user>/start")
def start(user: str) -> str:
    root = current_root()
    views.user_dir_of(root, user)
    return render_template("start.html", o=overview(root, user))
