"""What the screens show, assembled from the library. No rule lives here (ADR-0014)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from ..dataroot import DataRoot, load_yaml
from ..documents import load_document
from ..errors import CvacError
from ..render import draft_name
from ..validate import citable_ids, validate_files

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
KINDS = ("masters", "applications")


class NotFound(Exception):
    """A user, kind or spec name that does not exist, or is not even well-formed."""


def users(root: DataRoot) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not root.users_dir.is_dir():
        return out
    for d in sorted(root.users_dir.iterdir()):
        profile = d / "profile.yaml"
        if not profile.is_file():
            continue
        try:
            name = (load_yaml(profile).get("identity") or {}).get("full_name")
        except (CvacError, AttributeError):
            name = None
        out.append({"slug": d.name, "full_name": name or d.name})
    return out


def git_status(root: DataRoot) -> dict[str, Any]:
    """The data root's git status, or `available: False` when it is not a repository."""
    try:
        run = subprocess.run(
            ["git", "-C", str(root.path), "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "lines": []}
    if run.returncode != 0:
        return {"available": False, "lines": []}
    return {"available": True, "lines": run.stdout.splitlines()}


def user_dir_of(root: DataRoot, user: str) -> Path:
    if not SLUG_RE.match(user) or not root.profile_path(user).is_file():
        raise NotFound(f"no user `{user}`")
    return root.user_dir(user)


def spec_dir_of(root: DataRoot, user: str, kind: str, name: str) -> Path:
    udir = user_dir_of(root, user)
    if kind not in KINDS or not SLUG_RE.match(name):
        raise NotFound(f"no {kind} `{name}`")
    d = udir / kind / name
    if not (d / "cv-spec.yaml").is_file():
        raise NotFound(f"no {kind} `{name}` for `{user}`")
    return d


def _pdfs(d: Path, output_name: str) -> dict[str, Path | None]:
    draft = d / draft_name(output_name, True)
    final = d / output_name
    return {
        "draft": draft if draft.is_file() else None,
        "final": final if final.is_file() else None,
    }


def _cited(doc: dict[str, Any]) -> list[str]:
    """Every fact id a spec or a letter cites, in order of first appearance."""
    refs: list[str] = []
    if isinstance(doc.get("summary"), dict):
        refs += doc["summary"].get("source_facts") or []
    for item in doc.get("experience") or []:
        for b in item.get("bullets") or []:
            refs += b.get("source_facts") or []
    refs += doc.get("source_facts") or []
    return list(dict.fromkeys(refs))


def spec_summary(root: DataRoot, user: str, kind: str, d: Path) -> dict[str, Any]:
    spec = load_yaml(d / "cv-spec.yaml")
    if not isinstance(spec, dict):
        raise CvacError(f"{root.rel(d / 'cv-spec.yaml')} is not a mapping")
    out: dict[str, Any] = {
        "user": user,
        "kind": kind,
        "name": d.name,
        "rel": root.rel(d),
        "language": spec.get("language"),
        "template": spec.get("template"),
        "status": spec.get("status"),
        "approved_on": spec.get("approved_on"),
        "headline": spec.get("headline"),
        "job_id": spec.get("job_id"),
        "max_pages": spec.get("max_pages"),
        "output_name": spec.get("output_name") or "",
        "pdf": _pdfs(d, spec.get("output_name") or "cv.pdf"),
        "letter": None,
    }
    letter = d / "letter.md"
    if kind == "applications" and letter.is_file():
        out["letter"] = _letter_summary(root, d, letter)
    return out


def _letter_summary(root: DataRoot, d: Path, letter: Path) -> dict[str, Any]:
    """A letter's state; a letter that does not even parse is shown as invalid, not hidden."""
    try:
        fm = load_document(letter, root.rel(letter))
    except CvacError as e:
        return {
            "status": "invalid",
            "error": str(e),
            "approved_on": None,
            "language": None,
            "pdf": _pdfs(d, "cover-letter.pdf"),
            "cited": [],
        }
    fm = fm if isinstance(fm, dict) else {}
    return {
        "status": fm.get("status"),
        "error": None,
        "approved_on": fm.get("approved_on"),
        "language": fm.get("language"),
        "pdf": _pdfs(d, fm.get("output_name") or "cover-letter.pdf"),
        "cited": _cited(fm),
    }


def specs(root: DataRoot, user: str) -> list[dict[str, Any]]:
    udir = user_dir_of(root, user)
    out = []
    for kind in KINDS:
        base = udir / kind
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if (d / "cv-spec.yaml").is_file():
                out.append(spec_summary(root, user, kind, d))
    return out


def spec_detail(root: DataRoot, user: str, kind: str, name: str) -> dict[str, Any]:
    d = spec_dir_of(root, user, kind, name)
    out = spec_summary(root, user, kind, d)
    spec = load_yaml(d / "cv-spec.yaml")
    _, fact_status = citable_ids(load_yaml(root.profile_path(user)))
    out["facts"] = [{"id": f, "status": fact_status.get(f, "unknown")} for f in _cited(spec)]
    files = [d / "cv-spec.yaml"]
    if out["letter"] is not None:
        files.append(d / "letter.md")
        out["letter"]["facts"] = [
            {"id": f, "status": fact_status.get(f, "unknown")} for f in out["letter"]["cited"]
        ]
    rep = validate_files(root, files)
    out["errors"], out["warnings"] = rep.errors, rep.warnings
    return out
