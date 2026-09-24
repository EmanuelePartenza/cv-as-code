"""Scaffolding: the files `cvac init` writes, and the first files of a new user (ADR-0006).

A data root is created once; a user is created once. Both refuse to overwrite: the
framework never rewrites a person's data on its own.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .dataroot import MARKER, DataRoot
from .errors import CvacError

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
USER_DIRS = ("notes", "sources", "interviews", "inbox", "masters", "applications")

INIT_GITIGNORE = """\
# Rendering products are regenerated: commit only what you deliberately deliver.
*-DRAFT.pdf
build/
*.report.md

# Raw document inbox: nothing enters git until it is archived in users/<slug>/sources/.
users/*/inbox/*
!users/*/inbox/README.md

# Agent-local configuration and session ephemera.
.claude/project.conf
.claude/settings.local.json
.claude/edit-log.jsonl
.claude/edit-log-archive/
"""

INIT_README = """\
# A cv-as-code data root

This directory holds *data only*: your profile, your search parameters, your
CVs and applications. The framework that reads it is the `cv-as-code` package
(https://github.com/EmanuelePartenza/cv-as-code); the `cvac.yaml` marker is
what tells it where the data root is.

```
cvac.yaml                 marker: schema_version, kind, default_user
users/<slug>/profile.yaml career facts, each with an id, a status and evidence
users/<slug>/search.yaml  target roles, markets, constraints
users/<slug>/masters/     generic CVs (cv-spec.yaml + rendered PDF)
users/<slug>/applications/<job_id>/   tailored CV, cover letter
users/<slug>/notes/       evidence notes cited by facts
users/<slug>/sources/     original documents (CVs, reviews), read-only
users/<slug>/inbox/       drop raw documents here for extraction (gitignored)
jobs/<job_id>/            postings: raw.txt verbatim + job.yaml normalised
i18n/, templates/         optional overrides of the package's labels and templates
```

Run `cvac validate --all` after every change; `cvac cv <spec-dir> --mode draft`
for a watermarked preview; `--mode final` only renders an approved spec that
cites verified facts.
"""

INBOX_README = """\
# Inbox

Drop raw documents here (old CVs, reviews, notes). They are extracted into
draft facts with an evidence note, then archived under `sources/`. Nothing in
this directory is tracked by git except this file.
"""


def check_slug(slug: str) -> str:
    if not SLUG_RE.match(slug or ""):
        raise CvacError(f"`{slug}` is not a slug (lowercase letters, digits and dashes)")
    return slug


def init_data_root(target: Path, user: str | None = None) -> Path:
    """Create a data root at target; refuses to overwrite an existing marker."""
    marker = target / MARKER
    if marker.exists():
        raise CvacError(f"{marker} already exists; refusing to overwrite a data root")
    if user:
        check_slug(user)
    target.mkdir(parents=True, exist_ok=True)
    lines = [
        "# cv-as-code data root - https://github.com/EmanuelePartenza/cv-as-code",
        "schema_version: 1",
        "kind: data-root",
        f"default_user: {user}" if user else "# default_user: <slug>",
    ]
    marker.write_text("\n".join(lines) + "\n", "utf-8")
    (target / "users").mkdir(exist_ok=True)
    (target / "jobs").mkdir(exist_ok=True)
    (target / "jobs" / ".gitkeep").touch()
    if not (target / ".gitignore").exists():
        (target / ".gitignore").write_text(INIT_GITIGNORE, "utf-8")
    if not (target / "README.md").exists():
        (target / "README.md").write_text(INIT_README, "utf-8")
    if user:
        user_dirs(target / "users" / user)
    else:
        (target / "users" / ".gitkeep").touch()
    return target


def user_dirs(udir: Path) -> Path:
    for sub in USER_DIRS:
        (udir / sub).mkdir(parents=True, exist_ok=True)
    readme = udir / "inbox" / "README.md"
    if not readme.exists():
        readme.write_text(INBOX_README, "utf-8")
    return udir


def set_default_user(root: DataRoot, slug: str) -> None:
    """Fill the marker's default_user when it has none; an existing value is kept."""
    marker = root.path / MARKER
    lines = marker.read_text("utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("default_user:"):
            return
        if line.startswith("# default_user:"):
            lines[i] = f"default_user: {slug}"
            break
    else:
        lines.append(f"default_user: {slug}")
    marker.write_text("\n".join(lines) + "\n", "utf-8")
    root.config["default_user"] = slug


def init_user(
    root: DataRoot,
    slug: str,
    full_name: str,
    email: str,
    city: str,
    country: str | None = None,
    pivot_language: str = "en",
    languages: list[tuple[str, str]] | None = None,
    target_roles: list[str] | None = None,
) -> Path:
    """A new user's directory with an empty but valid profile and search; refuses to overwrite."""
    check_slug(slug)
    if not re.match(r"^[a-z]{2}$", pivot_language or ""):
        raise CvacError(f"`{pivot_language}` is not an ISO 639-1 language code")
    for name, value in (("full name", full_name), ("email", email), ("city", city)):
        if not (value or "").strip():
            raise CvacError(f"the {name} is required")
    roles = [r.strip() for r in target_roles or [] if r and r.strip()]
    if not roles:
        raise CvacError("at least one target role is required (search.yaml needs one)")
    udir = root.user_dir(slug)
    if root.profile_path(slug).exists():
        raise CvacError(f"user `{slug}` already exists; refusing to overwrite the profile")
    user_dirs(udir)
    profile = {
        "schema_version": 1,
        "kind": "profile",
        "user": slug,
        "pivot_language": pivot_language,
        "identity": {
            "full_name": full_name.strip(),
            "born": None,
            "location": {
                "city": city.strip(),
                **({"country": country.strip()} if country and country.strip() else {}),
            },
            "email": email.strip(),
            "phone": None,
            "links": [],
        },
        "languages": [
            {"code": c, "level": lv} for c, lv in (languages or [(pivot_language, "native")])
        ],
        "experiences": [],
        "projects": [],
        "education": [],
        "skills": [],
    }
    search = {
        "schema_version": 1,
        "kind": "search",
        "user": slug,
        "target_roles": roles,
        "adjacent_roles": [],
        "markets": [
            {
                "area": city.strip(),
                **({"country": country.strip()} if country and country.strip() else {}),
                "modes": ["onsite", "hybrid", "remote"],
            }
        ],
        "cv_languages": [pivot_language],
        "red_flags": [],
        "confidential": False,
    }
    _write_yaml(
        root.profile_path(slug),
        profile,
        "# Career facts: the source of truth. Facts enter as draft and are verified by you.",
    )
    _write_yaml(
        udir / "search.yaml",
        search,
        "# What you are looking for: target roles, markets, constraints.",
    )
    if not root.default_user:
        set_default_user(root, slug)
    return udir


def _write_yaml(path: Path, doc: dict, comment: str) -> None:
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    path.write_text(f"{comment}\n{text}", "utf-8")
