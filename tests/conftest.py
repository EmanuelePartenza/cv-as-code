"""Shared fixtures: a minimal synthetic data root.

Nothing here describes a real person (ADR-0008): the profile is invented for the
tests and deliberately small - one experience, one project, three facts at the
three statuses, one evidenced skill and one without evidence.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from cv_as_code.dataroot import DataRoot

PROFILE: dict[str, Any] = {
    "schema_version": 1,
    "kind": "profile",
    "user": "test",
    "pivot_language": "en",
    "identity": {
        "full_name": "Test User",
        "born": None,
        "location": {"city": "Testville", "country": "XX"},
        "email": "test.user@example.com",
        "phone": None,
        "links": [{"label": "Site", "url": "https://example.com"}],
    },
    "languages": [{"code": "en", "level": "native"}, {"code": "xx", "level": "B2"}],
    "experiences": [
        {
            "id": "exp-acme",
            "role": "Widget Engineer",
            "company": {"name": "Acme Widgets", "location": "Testville", "industry": "Widgets"},
            "start": "2020-03",
            "end": None,
            "stack": ["Widgets"],
            "facts": [
                {
                    "id": "exp-acme.f01",
                    "claim": "Built the widget pipeline",
                    "metrics": {"widgets": 42},
                    "tags": ["pipeline"],
                    "status": "verified",
                    "verified_on": "2026-01-01",
                    "evidence": "notes/evidence.md",
                },
                {
                    "id": "exp-acme.f02",
                    "claim": "Reduced widget defects",
                    "status": "draft",
                    "evidence": ["notes/evidence.md#defects"],
                },
                {
                    "id": "exp-acme.f03",
                    "claim": "Invented the widget",
                    "status": "rejected",
                    "evidence": None,
                },
            ],
        }
    ],
    "projects": [
        {
            "id": "prj-tool",
            "role": "Author",
            "company": {"name": None},
            "start": "2024",
            "end": "2024",
            "facts": [
                {
                    "id": "prj-tool.f01",
                    "claim": "Wrote a widget counter",
                    "status": "verified",
                    "verified_on": "2026-01-01",
                    "evidence": "notes/evidence.md",
                }
            ],
        }
    ],
    "education": [
        {
            "id": "edu-uni",
            "degree": "BSc Widgetry",
            "institution": "Testville University",
            "location": "Testville",
            "start": "2016",
            "end": "2019",
            "notes": None,
        }
    ],
    "skills": [
        {
            "id": "skill-widgets",
            "name": "Widgets",
            "category": "domain",
            "evidence_facts": ["exp-acme.f01"],
        },
        {"id": "skill-unproven", "name": "Gadgets", "category": "domain", "evidence_facts": []},
    ],
}

SEARCH: dict[str, Any] = {
    "schema_version": 1,
    "kind": "search",
    "user": "test",
    "target_roles": ["widget-engineer"],
    "markets": [{"area": "Testville", "country": "XX", "modes": ["remote"]}],
    "cv_languages": ["en"],
    "confidential": False,
}


def spec_doc(
    status: str = "draft", facts: tuple[str, ...] = ("exp-acme.f01",), **overrides: Any
) -> dict[str, Any]:
    """A cv-spec citing `facts` in its summary and first bullet."""
    doc: dict[str, Any] = {
        "schema_version": 1,
        "kind": "cv-spec",
        "user": "test",
        "job_id": None,
        "based_on": None,
        "language": "en",
        "template": "classic",
        "max_pages": 2,
        "output_name": "Test_User_CV.pdf",
        "status": status,
        "approved_on": "2026-01-02" if status == "approved" else None,
        "headline": "Widget Engineer",
        "summary": {"text": "Widget engineer with a pipeline.", "source_facts": list(facts)},
        "sections": ["summary", "experience", "projects", "skills", "education", "languages"],
        "experience": [
            {
                "ref": "exp-acme",
                "bullets": [
                    {"text": "Built the widget pipeline end to end.", "source_facts": list(facts)}
                ],
            },
            {
                "ref": "prj-tool",
                "title": "Counter",
                "subtitle": "A widget counter",
                "bullets": [{"text": "Wrote a widget counter.", "source_facts": ["prj-tool.f01"]}],
            },
        ],
        "skills_layout": {
            "groups": [{"label": "Domain", "items": ["Widgets"]}],
            "emphasis": ["Widgets"],
        },
        "education": [{"ref": "edu-uni", "degree": "BSc in Widgetry", "notes": "With honours"}],
        "omitted": [],
    }
    doc.update(overrides)
    return doc


def dump(path: Path, doc: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), "utf-8")
    return path


def write_root(root: Path, profile: dict[str, Any] | None = None) -> Path:
    """Create a complete minimal data root at `root` and return it."""
    (root / "users" / "test" / "notes").mkdir(parents=True, exist_ok=True)
    (root / "jobs").mkdir(exist_ok=True)
    (root / "cvac.yaml").write_text("schema_version: 1\nkind: data-root\ndefault_user: test\n")
    dump(root / "users" / "test" / "profile.yaml", copy.deepcopy(profile or PROFILE))
    dump(root / "users" / "test" / "search.yaml", copy.deepcopy(SEARCH))
    (root / "users" / "test" / "notes" / "evidence.md").write_text("# Evidence\n\n## defects\n")
    return root


def write_spec(root: DataRoot, name: str = "base", **kw: Any) -> Path:
    """Write users/test/masters/<name>/cv-spec.yaml and return its directory."""
    d = root.path / "users" / "test" / "masters" / name
    dump(d / "cv-spec.yaml", spec_doc(**kw))
    return d


@pytest.fixture
def data_root(tmp_path: Path) -> DataRoot:
    return DataRoot.load(write_root(tmp_path / "root"))


@pytest.fixture
def profile() -> dict[str, Any]:
    return copy.deepcopy(PROFILE)
