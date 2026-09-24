"""Scaffolding a data root and a user: valid from the first file, never overwriting."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.scaffold import init_data_root, init_user, set_default_user
from cv_as_code.validate import discover_all, validate_files


def test_init_user_writes_a_valid_profile_and_search(tmp_path: Path) -> None:
    root = DataRoot.load(init_data_root(tmp_path / "dr"))
    udir = init_user(
        root,
        "ada",
        "Ada Example",
        "ada@example.org",
        "Testville",
        "XX",
        "en",
        target_roles=["engineer"],
    )
    assert udir == root.path / "users" / "ada"
    profile = yaml.safe_load(root.profile_path("ada").read_text("utf-8"))
    assert profile["identity"]["full_name"] == "Ada Example" and profile["experiences"] == []
    assert profile["languages"] == [{"code": "en", "level": "native"}]
    search = yaml.safe_load((udir / "search.yaml").read_text("utf-8"))
    assert search["markets"][0]["country"] == "XX" and search["confidential"] is False
    assert search["target_roles"] == ["engineer"] and "salary" not in search
    rep = validate_files(root, discover_all(root))
    assert rep.errors == []
    assert (udir / "inbox" / "README.md").is_file() and (udir / "masters").is_dir()
    assert root.default_user == "ada"
    assert "default_user: ada" in (root.path / "cvac.yaml").read_text("utf-8")


def test_init_user_refuses_bad_input_and_overwrites(tmp_path: Path) -> None:
    root = DataRoot.load(init_data_root(tmp_path / "dr", "ada"))
    with pytest.raises(CvacError, match="is not a slug"):
        init_user(root, "Ada!", "Ada", "a@example.org", "X")
    with pytest.raises(CvacError, match="the email is required"):
        init_user(root, "ada", "Ada", " ", "X")
    with pytest.raises(CvacError, match="not an ISO 639-1"):
        init_user(root, "ada", "Ada", "a@example.org", "X", pivot_language="english")
    with pytest.raises(CvacError, match="at least one target role"):
        init_user(root, "ada", "Ada", "a@example.org", "X", target_roles=[" "])
    init_user(root, "ada", "Ada", "a@example.org", "X", target_roles=["engineer"])
    with pytest.raises(CvacError, match="already exists"):
        init_user(root, "ada", "Ada", "a@example.org", "X", target_roles=["engineer"])


def test_default_user_is_set_once(tmp_path: Path) -> None:
    root = DataRoot.load(init_data_root(tmp_path / "dr"))
    set_default_user(root, "first")
    set_default_user(root, "second")
    assert root.default_user == "first"
    text = (root.path / "cvac.yaml").read_text("utf-8")
    assert text.count("default_user:") == 1 and "default_user: first" in text
    with pytest.raises(CvacError, match="already exists"):
        init_data_root(tmp_path / "dr")
