"""Data-root location (flag > env > discovery), display paths, and asset lookup order."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import write_root

from cv_as_code.dataroot import ENV_VAR, DataRoot, package_dir
from cv_as_code.errors import CvacError


def test_explicit_path_needs_no_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    plain = tmp_path / "plain"
    plain.mkdir()
    root = DataRoot.locate(str(plain))
    assert root.path == plain.resolve() and root.config == {} and root.default_user is None


def test_explicit_path_must_be_a_directory(tmp_path: Path) -> None:
    with pytest.raises(CvacError, match="not a directory"):
        DataRoot.locate(str(tmp_path / "missing"))


def test_environment_variable_is_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = write_root(tmp_path / "r")
    monkeypatch.setenv(ENV_VAR, str(root))
    assert DataRoot.locate().path == root.resolve()
    assert DataRoot.locate().default_user == "test"


def test_flag_wins_over_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a, b = write_root(tmp_path / "a"), write_root(tmp_path / "b")
    monkeypatch.setenv(ENV_VAR, str(a))
    assert DataRoot.locate(str(b)).path == b.resolve()


def test_discovery_walks_upward_from_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    root = write_root(tmp_path / "r")
    monkeypatch.chdir(root / "users" / "test" / "notes")
    assert DataRoot.locate().path == root.resolve()


def test_discovery_fails_clearly_without_a_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(CvacError, match="not inside a cv-as-code data root"):
        DataRoot.locate()


def test_load_requires_a_mapping_marker(tmp_path: Path) -> None:
    (tmp_path / "cvac.yaml").write_text("- not a mapping\n")
    with pytest.raises(CvacError, match="expected a mapping"):
        DataRoot.load(tmp_path)
    with pytest.raises(CvacError, match="has no cvac.yaml"):
        DataRoot.load(tmp_path / "nowhere")


def test_rel_display_paths(data_root: DataRoot, tmp_path: Path) -> None:
    assert data_root.rel(data_root.path / "users" / "test") == "users/test"
    assert (
        data_root.rel(package_dir() / "i18n" / "labels.en.yaml") == "<package>/i18n/labels.en.yaml"
    )
    outside = tmp_path / "elsewhere"
    assert data_root.rel(outside) == str(outside.resolve())


def test_resolve_dir_accepts_absolute_relative_and_root_relative(
    data_root: DataRoot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    d = data_root.path / "users" / "test" / "masters" / "base"
    d.mkdir(parents=True)
    (d / "cv-spec.yaml").write_text("kind: cv-spec\n")
    assert data_root.resolve_dir(d) == d
    assert data_root.resolve_dir(d / "cv-spec.yaml") == d
    monkeypatch.chdir(tmp_path)
    assert data_root.resolve_dir("users/test/masters/base") == d
    monkeypatch.chdir(data_root.path / "users")
    assert data_root.resolve_dir("test/masters/base") == d


def test_asset_lookup_prefers_the_data_root(data_root: DataRoot) -> None:
    assert data_root.labels_path("en") == package_dir() / "i18n" / "labels.en.yaml"
    assert data_root.labels_path("zz") is None
    override = data_root.path / "i18n" / "labels.en.yaml"
    override.parent.mkdir()
    override.write_text("kind: labels\n")
    assert data_root.labels_path("en") == override
    assert override in data_root.labels_files()

    assert data_root.template_dir("classic") == package_dir() / "templates" / "classic"
    assert data_root.template_dir("nope") is None
    local = data_root.path / "templates" / "classic"
    local.mkdir(parents=True)
    assert data_root.template_dir("classic") == local
    assert data_root.template_lib_dir() == package_dir() / "templates" / "lib"
    (data_root.path / "templates" / "lib").mkdir()
    assert data_root.template_lib_dir() == data_root.path / "templates" / "lib"


def test_schema_and_fonts_live_in_the_package(data_root: DataRoot) -> None:
    assert data_root.schema_path("profile").is_file()
    assert (data_root.fonts_dir() / "Lato-Regular.ttf").is_file()
    assert (data_root.fonts_dir() / "OFL.txt").is_file()
