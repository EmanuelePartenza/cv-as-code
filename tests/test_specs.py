"""The approval gate as a library call: layout-preserving, refused through the validator."""

from __future__ import annotations

import pytest
import yaml
from conftest import JOB_ID, write_job, write_letter_md, write_spec

from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.specs import approve, approved_text


def test_approve_changes_only_status_and_approved_on(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    path = d / "cv-spec.yaml"
    text = path.read_text("utf-8").replace("status: draft", "status: draft   # from the interview")
    path.write_text(text, "utf-8")
    before = path.read_text("utf-8").splitlines()
    assert approve(data_root, path, on="2026-03-01") == "2026-03-01"
    after = path.read_text("utf-8").splitlines()
    changed = [(a, b) for a, b in zip(before, after, strict=True) if a != b]
    assert changed == [
        ("status: draft   # from the interview", "status: approved   # from the interview"),
        ("approved_on: null", 'approved_on: "2026-03-01"'),
    ]
    doc = yaml.safe_load(path.read_text("utf-8"))
    assert doc["status"] == "approved" and doc["approved_on"] == "2026-03-01"


def test_approved_on_is_inserted_after_status_when_absent() -> None:
    from pathlib import Path

    text = "kind: cv-spec\nstatus: draft\nheadline: x\n"
    out = approved_text(text, Path("cv-spec.yaml"), "2026-03-01")
    assert out == 'kind: cv-spec\nstatus: approved\napproved_on: "2026-03-01"\nheadline: x\n'
    with pytest.raises(CvacError, match="no top-level `status:` line"):
        approved_text("kind: cv-spec\n  status: draft\n", Path("cv-spec.yaml"), "2026-03-01")


def test_approve_refuses_a_spec_citing_a_draft_fact_and_leaves_it_untouched(
    data_root: DataRoot,
) -> None:
    d = write_spec(data_root, facts=("exp-acme.f02",))
    path = d / "cv-spec.yaml"
    before = path.read_text("utf-8")
    with pytest.raises(
        CvacError,
        match=r"cannot approve .*cv-spec.yaml:\n  - status is `approved` but cites non-verified "
        r"fact\(s\): exp-acme.f02",
    ):
        approve(data_root, path)
    assert path.read_text("utf-8") == before


def test_approve_refuses_twice_and_non_approvable_documents(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    approve(data_root, d / "cv-spec.yaml", on="2026-03-01")
    with pytest.raises(CvacError, match="already approved \\(approved_on: 2026-03-01\\)"):
        approve(data_root, d / "cv-spec.yaml")
    with pytest.raises(CvacError, match="not a cv-spec or a cover letter"):
        approve(data_root, data_root.profile_path("test"))
    with pytest.raises(CvacError, match="missing users/test/masters/ghost/cv-spec.yaml"):
        approve(data_root, data_root.path / "users" / "test" / "masters" / "ghost" / "cv-spec.yaml")


def test_approve_a_letter_edits_its_frontmatter_only(data_root: DataRoot) -> None:
    write_job(data_root)
    path = write_letter_md(data_root)
    body_before = path.read_text("utf-8").split("---\n", 2)[2]
    approve(data_root, path, on="2026-03-02")
    text = path.read_text("utf-8")
    assert text.startswith("---\n") and 'approved_on: "2026-03-02"' in text
    assert "status: approved" in text and text.split("---\n", 2)[2] == body_before
    path.write_text("no frontmatter here\n", "utf-8")
    with pytest.raises(CvacError, match="has no YAML frontmatter"):
        approve(data_root, path)


def test_approve_a_letter_citing_a_draft_fact_is_refused(data_root: DataRoot) -> None:
    write_job(data_root)
    path = write_letter_md(data_root, source_facts=["exp-acme.f02"])
    with pytest.raises(CvacError, match="non-verified fact\\(s\\): exp-acme.f02"):
        approve(data_root, path)
    assert f"applications/{JOB_ID}" in str(path)
