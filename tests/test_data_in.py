"""v0.2 data-in: the profile report and the fact verify/reject command."""

from __future__ import annotations

import pytest
import yaml
from conftest import write_spec

from cv_as_code.cli import main
from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.facts import set_status
from cv_as_code.report import build_report, write_report
from cv_as_code.validate import discover_all, validate_files


def test_report_has_every_section_and_a_completeness_checklist(data_root: DataRoot) -> None:
    text = build_report(data_root, "test")
    for heading in (
        "## Identity",
        "## Timeline",
        "## Facts",
        "## Skills",
        "## Education",
        "## Languages",
        "## Completeness",
    ):
        assert heading in text
    assert "- facts: 2 verified, 1 draft, 1 rejected" in text
    assert "- [ ] fact `exp-acme.f02` is draft: confirm or reject it" in text
    assert "- [ ] skill `skill-unproven` has no evidence facts" in text
    assert "| `exp-acme.f03` | rejected |" in text and "✗ none" in text
    assert "`prj-tool.f01`" in text


def test_report_is_written_where_data_roots_ignore_it(data_root: DataRoot) -> None:
    path = write_report(data_root, "test")
    assert path == data_root.path / "users" / "test" / "profile.report.md"
    assert main(["profile", "report", "--data-root", str(data_root.path)]) == 0
    with pytest.raises(CvacError, match="profile not found"):
        build_report(data_root, "ghost")


def test_verify_changes_only_the_status_lines(data_root: DataRoot) -> None:
    profile = data_root.profile_path("test")
    before = profile.read_text("utf-8")
    changes = set_status(data_root, "test", ["exp-acme.f02"], "verified", on="2026-02-02")
    assert [(c.fact_id, c.old_status, c.new_status) for c in changes] == [
        ("exp-acme.f02", "draft", "verified")
    ]
    after = profile.read_text("utf-8")
    import difflib

    changed = [
        ln[0] + ln[1:].strip()
        for ln in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0)
        if ln[:1] in "+-" and ln[:3] not in ("+++", "---")
    ]
    assert changed == [
        "-status: draft",
        "+status: verified",
        '+verified_on: "2026-02-02"',
    ]
    doc = yaml.safe_load(after)
    fact = doc["experiences"][0]["facts"][1]
    assert fact["status"] == "verified" and fact["verified_on"] == "2026-02-02"
    assert validate_files(data_root, discover_all(data_root)).errors == []


def test_verify_refuses_unknown_ids_and_facts_without_evidence(data_root: DataRoot) -> None:
    with pytest.raises(CvacError, match="fact `exp-acme.f99` does not exist"):
        set_status(data_root, "test", ["exp-acme.f99"], "verified")
    with pytest.raises(CvacError, match="is not a fact id"):
        set_status(data_root, "test", ["exp-acme"], "verified")
    with pytest.raises(CvacError, match="cannot be verified without evidence"):
        set_status(data_root, "test", ["exp-acme.f03"], "verified")  # rejected fact, evidence null


def test_reject_and_cli_exit_codes(data_root: DataRoot, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["fact", "reject", "exp-acme.f01", "--data-root", str(data_root.path)]) == 0
    assert "exp-acme.f01: verified -> rejected" in capsys.readouterr().out
    doc = yaml.safe_load(data_root.profile_path("test").read_text("utf-8"))
    assert doc["experiences"][0]["facts"][0]["status"] == "rejected"
    assert doc["experiences"][0]["facts"][0]["verified_on"] is None
    assert main(["fact", "verify", "exp-acme.f99", "--data-root", str(data_root.path)]) == 1
    assert "does not exist" in capsys.readouterr().err
    write_spec(data_root, status="approved")  # cites the now-rejected f01
    assert main(["validate", "--all", "--data-root", str(data_root.path)]) == 1
