"""The resolver's join, its draft/final modes, and the anti-invention gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import dump, spec_doc, write_spec

from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.resolve import fmt_date, fmt_range, resolve


def resolved_json(root: DataRoot, spec_dir: Path, mode: str = "draft") -> dict:
    res = resolve(root, spec_dir, mode)
    return json.loads(res.out_json.read_text("utf-8"))


# --- pure formatting ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "fmt", "expected"),
    [
        ("2024-07", "MM/YYYY", "07/2024"),
        ("2024-07-15", "MM/YYYY", "07/2024"),
        ("2024", "MM/YYYY", "2024"),
        ("2024-07", "YYYY-MM", "2024-07"),
        ("2024-07", "MM.YYYY", "07.2024"),
        (None, "MM/YYYY", None),
        ("", "MM/YYYY", None),
    ],
)
def test_fmt_date(value: str | None, fmt: str, expected: str | None) -> None:
    assert fmt_date(value, fmt) == expected


def test_fmt_range_cases() -> None:
    assert fmt_range("2020-03", None, "Present", "MM/YYYY") == "03/2020 – Present"
    assert fmt_range("2024", "2024", "Present", "MM/YYYY") == "2024"
    assert fmt_range("2016", "2019", "Present", "MM/YYYY") == "2016 – 2019"
    assert fmt_range(None, "2016", "Present", "MM/YYYY") == "2016"
    assert fmt_range(None, None, "Present", "MM/YYYY") == ""


# --- the join ----------------------------------------------------------------------------


def test_draft_resolve_joins_profile_spec_and_labels(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    doc = resolved_json(data_root, d)
    assert doc["meta"] == {"draft": True, "language": "en", "source": "users/test/masters/base"}
    assert doc["labels"]["experience"] == "Professional experience"
    assert doc["identity"]["full_name"] == "Test User"
    assert doc["identity"]["location"] == "Testville, XX"
    assert doc["identity"]["headline"] == "Widget Engineer"
    assert doc["summary"] == "Widget engineer with a pipeline."
    exp = doc["experience"][0]
    assert exp["role"] == "Widget Engineer"
    assert exp["org"] == "Acme Widgets, Testville"
    assert exp["dates"] == "03/2020 – Present"
    assert exp["bullets"] == ["Built the widget pipeline end to end."]
    prj = doc["projects"][0]
    assert prj == {
        "role": "Counter",
        "org": "A widget counter",
        "dates": "2024",
        "bullets": ["Wrote a widget counter."],
    }
    edu = doc["education"][0]
    assert edu["degree"] == "BSc in Widgetry" and edu["institution"] == "Testville University"
    assert edu["dates"] == "2016 – 2019" and edu["notes"] == "With honours"
    assert doc["languages"] == [
        {"name": "English", "level": "Native"},
        {"name": "xx", "level": "B2"},
    ]
    assert doc["skills"] == {
        "groups": [{"label": "Domain", "items": ["Widgets"]}],
        "emphasis": ["Widgets"],
    }


def test_unknown_sections_are_dropped_in_order(data_root: DataRoot) -> None:
    d = write_spec(data_root, sections=["skills", "bogus", "summary"])
    assert resolved_json(data_root, d)["sections"] == ["skills", "summary"]


def test_org_falls_back_to_company_name_when_no_location(data_root: DataRoot) -> None:
    doc = spec_doc()
    d = data_root.path / "users" / "test" / "masters" / "x"
    dump(d / "cv-spec.yaml", doc)
    profile = data_root.profile_path("test")
    import yaml

    prof = yaml.safe_load(profile.read_text("utf-8"))
    prof["experiences"][0]["company"]["location"] = None
    dump(profile, prof)
    assert resolved_json(data_root, d)["experience"][0]["org"] == "Acme Widgets"


def test_data_root_labels_override_the_package(data_root: DataRoot) -> None:
    import yaml

    labels = yaml.safe_load(data_root.labels_path("en").read_text("utf-8"))
    labels["date_format"] = "YYYY-MM"
    labels["present"] = "now"
    dump(data_root.path / "i18n" / "labels.en.yaml", labels)
    d = write_spec(data_root)
    doc = resolved_json(data_root, d)
    assert doc["experience"][0]["dates"] == "2020-03 – now"
    assert doc["labels"]["present"] == "now"


def test_resolve_accepts_file_or_directory(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    assert resolve(data_root, d / "cv-spec.yaml", "draft").spec_dir == d


# --- gates -------------------------------------------------------------------------------


def test_final_requires_an_approved_spec(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    with pytest.raises(CvacError, match="requires status: approved"):
        resolve(data_root, d, "final")


def test_final_rejects_unverified_cited_facts(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved", facts=("exp-acme.f02",))
    with pytest.raises(CvacError, match=r"not verified:\n  - exp-acme.f02"):
        resolve(data_root, d, "final")


def test_final_on_verified_facts_is_not_a_draft(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved")
    res = resolve(data_root, d, "final")
    assert res.draft is False and res.unverified == []
    assert json.loads(res.out_json.read_text("utf-8"))["meta"]["draft"] is False


def test_draft_tolerates_unverified_facts_but_reports_them(data_root: DataRoot) -> None:
    d = write_spec(data_root, facts=("exp-acme.f02", "exp-acme.f03"))
    res = resolve(data_root, d, "draft")
    assert res.draft is True
    assert sorted(u.split(" ")[0] for u in res.unverified) == [
        "exp-acme.f02",
        "exp-acme.f02",
        "exp-acme.f03",
        "exp-acme.f03",
    ]


def test_broken_reference_fails_even_in_draft(data_root: DataRoot) -> None:
    d = write_spec(data_root, facts=("exp-acme.f99",))
    with pytest.raises(
        CvacError, match=r"broken references:\n  - summary cites unknown fact `exp-acme.f99`"
    ):
        resolve(data_root, d, "draft")


def test_unknown_entity_reference_fails(data_root: DataRoot) -> None:
    d = write_spec(data_root, education=[{"ref": "edu-ghost", "degree": "x"}])
    with pytest.raises(CvacError, match="education refs unknown `edu-ghost`"):
        resolve(data_root, d, "draft")


def test_not_a_cv_spec_document(data_root: DataRoot) -> None:
    d = data_root.path / "users" / "test" / "masters" / "x"
    dump(d / "cv-spec.yaml", {"kind": "profile"})
    with pytest.raises(CvacError, match="is not a cv-spec document"):
        resolve(data_root, d, "draft")


def test_missing_labels_language_fails(data_root: DataRoot) -> None:
    d = write_spec(data_root, language="zz")
    with pytest.raises(CvacError, match="no labels file for language `zz`"):
        resolve(data_root, d, "draft")
