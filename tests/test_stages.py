"""Stage contracts: they validate, resolve against a data root, and pack for any engine."""

from __future__ import annotations

import pytest
from conftest import JOB_ID, write_job, write_spec

from cv_as_code.cli import main
from cv_as_code.dataroot import DataRoot, package_dir
from cv_as_code.errors import CvacError
from cv_as_code.stages import describe, fill, list_stages, load_stage, pack, resolve_stage


def test_the_six_stages_ship() -> None:
    assert list_stages() == [
        "03_extract",
        "05_interview",
        "10_normalize",
        "20_match",
        "30_tailor",
        "60_letter",
    ]


def test_every_contract_validates_and_points_to_a_shipped_schema() -> None:
    for name in list_stages():
        stage = load_stage(name)
        assert stage.contract["stage"] == name
        assert stage.instructions.startswith("# Stage ")
        assert (package_dir() / "schemas" / stage.contract["output"]["schema"]).is_file()


def test_gates_are_declared_where_a_person_must_approve() -> None:
    assert load_stage("30_tailor").gate == "human" and load_stage("60_letter").gate == "human"
    assert load_stage("10_normalize").gate == "none" and load_stage("20_match").gate == "none"


def test_unknown_stage_is_named() -> None:
    with pytest.raises(CvacError, match="unknown stage `99_nope`"):
        load_stage("99_nope")


def test_fill_names_the_missing_flag() -> None:
    with pytest.raises(CvacError, match="needs --job"):
        fill("jobs/{job_id}/x", {}, "w")
    assert fill("users/{user}/x", {"user": "u"}, "w") == "users/u/x"


def test_resolve_uses_the_default_user_and_finds_inputs(data_root: DataRoot) -> None:
    write_job(data_root)
    rs = resolve_stage(data_root, "20_match", {"job_id": JOB_ID})
    assert rs.params["user"] == "test"
    assert rs.output == data_root.path / "users" / "test" / "matches" / f"{JOB_ID}.yaml"
    assert all(path.is_file() for _, path, _ in rs.inputs)


def test_pack_holds_instructions_inputs_language_and_the_closing_rule(data_root: DataRoot) -> None:
    write_job(data_root)
    text = pack(data_root, resolve_stage(data_root, "20_match", {"job_id": JOB_ID}))
    assert text.startswith("# Stage 20_match")
    assert "# Stage 20 — match a posting against a profile" in text
    assert f"## Input jobs/{JOB_ID}/job.yaml" in text
    assert "## Input users/test/profile.yaml" in text
    assert "pivot language: `en`" in text
    assert f"`cvac validate users/test/matches/{JOB_ID}.yaml`" in text
    assert "Never set `status: approved`" in text


def test_pack_fails_on_a_missing_input(data_root: DataRoot) -> None:
    rs = resolve_stage(data_root, "20_match", {"job_id": "20260103-ghost-role"})
    with pytest.raises(CvacError, match="input jobs/20260103-ghost-role/job.yaml is missing"):
        pack(data_root, rs)


def test_describe_marks_missing_inputs(data_root: DataRoot) -> None:
    write_job(data_root)
    write_spec(data_root)
    rs = resolve_stage(data_root, "30_tailor", {"job_id": JOB_ID, "master": "base"})
    text = describe(data_root, rs)
    assert f"users/test/matches/{JOB_ID}.yaml  [MISSING]" in text
    assert "users/test/masters/base/cv-spec.yaml  [present]" in text
    assert "gate: human" in text


def test_cli_stage_commands(data_root: DataRoot, capsys: pytest.CaptureFixture[str]) -> None:
    write_job(data_root)
    assert main(["stage", "list"]) == 0
    assert "20_match" in capsys.readouterr().out
    assert (
        main(["stage", "pack", "20_match", "--job", JOB_ID, "--data-root", str(data_root.path)])
        == 0
    )
    assert capsys.readouterr().out.startswith("# Stage 20_match")
    assert main(["stage", "show", "20_match", "--data-root", str(data_root.path)]) == 1
    assert "needs --job" in capsys.readouterr().err


def test_interview_pack_carries_the_skeleton_and_tolerates_a_new_user(data_root: DataRoot) -> None:
    rs = resolve_stage(data_root, "05_interview", {"user": "newcomer", "name": "01-onboarding"})
    text = pack(data_root, rs)
    assert "# Attachment questionnaire.skeleton.md" in text
    assert "## A — Who you are" in text
    assert "_(absent; this input is optional)_" in text
    assert rs.output == data_root.path / "users" / "newcomer" / "interviews" / "01-onboarding.md"


def test_extract_pack_needs_document_and_name(data_root: DataRoot) -> None:
    with pytest.raises(CvacError, match="needs --document"):
        resolve_stage(data_root, "03_extract", {"name": "x"})
    doc = data_root.path / "users" / "test" / "inbox" / "old-cv.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("I built widgets.\n")
    rs = resolve_stage(data_root, "03_extract", {"document": "inbox/old-cv.md", "name": "old-cv"})
    text = pack(data_root, rs)
    assert "## Input users/test/inbox/old-cv.md" in text and "I built widgets." in text
    assert rs.output == data_root.path / "users" / "test" / "notes" / "old-cv.md"
