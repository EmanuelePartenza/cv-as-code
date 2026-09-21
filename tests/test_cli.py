"""The cvac command: exit codes, messages, and the init scaffold."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import write_spec

from cv_as_code.cli import main
from cv_as_code.dataroot import DataRoot


def test_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0 and "cvac 0." in capsys.readouterr().out


def test_validate_all_reports_counts(
    data_root: DataRoot, capsys: pytest.CaptureFixture[str]
) -> None:
    write_spec(data_root)
    assert main(["validate", "--all", "--data-root", str(data_root.path)]) == 0
    out = capsys.readouterr().out
    assert "0 error(s), 1 warning(s)" in out and "WARN  users/test/profile.yaml" in out


def test_validate_without_arguments_is_a_usage_error(data_root: DataRoot) -> None:
    with pytest.raises(SystemExit) as e:
        main(["validate", "--data-root", str(data_root.path)])
    assert e.value.code == 2


def test_data_root_flag_works_before_and_after_the_subcommand(data_root: DataRoot) -> None:
    assert main(["--data-root", str(data_root.path), "validate", "--all"]) == 0
    assert main(["validate", "--all", "--data-root", str(data_root.path)]) == 0


def test_gate_failure_exits_one_with_a_named_error(
    data_root: DataRoot, capsys: pytest.CaptureFixture[str]
) -> None:
    write_spec(data_root)
    code = main(
        [
            "resolve",
            "users/test/masters/base",
            "--mode",
            "final",
            "--data-root",
            str(data_root.path),
        ]
    )
    assert code == 1
    assert "ERROR (resolve): --mode final requires status: approved" in capsys.readouterr().err


def test_cv_renders_a_pdf(data_root: DataRoot, capsys: pytest.CaptureFixture[str]) -> None:
    d = write_spec(data_root)
    assert main(["cv", str(d), "--data-root", str(data_root.path)]) == 0
    out = capsys.readouterr().out
    assert "rendered users/test/masters/base/Test_User_CV-DRAFT.pdf - 1 page(s)  [DRAFT]" in out
    assert (d / "Test_User_CV-DRAFT.pdf").is_file()


def test_init_scaffolds_a_data_root_and_refuses_to_overwrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "new"
    assert main(["init", str(target), "--user", "someone"]) == 0
    assert (target / "cvac.yaml").read_text().splitlines()[-1] == "default_user: someone"
    for rel in ("users/someone/inbox/README.md", "jobs/.gitkeep", ".gitignore", "README.md"):
        assert (target / rel).is_file(), rel
    assert main(["validate", "--all", "--data-root", str(target)]) == 0
    assert main(["init", str(target)]) == 1
    assert "already exists" in capsys.readouterr().err
