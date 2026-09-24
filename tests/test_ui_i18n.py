"""The UI in four languages (ADR-0016) and the folder browser of the chooser."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from conftest import write_spec

flask = pytest.importorskip("flask")

from cv_as_code.dataroot import DataRoot  # noqa: E402
from cv_as_code.errors import CvacError  # noqa: E402
from cv_as_code.resolve import resolve  # noqa: E402
from cv_as_code.ui import create_app  # noqa: E402
from cv_as_code.ui.i18n import LANGUAGES, catalog, translate, used_keys  # noqa: E402
from cv_as_code.ui.state import browse, new_folder  # noqa: E402

STATUS_WORDS = {
    "verified", "draft", "rejected", "approved", "proposed", "applied", "filled", "to-fill",
    "invalid", "running", "ok", "failed", "apply", "stretch", "skip", "masters", "applications",
    "final",
    "Position",
    "Project",
    "evidence",
    "context",
    "duplicate",
    "irrelevant",
}  # fmt: skip


@pytest.fixture
def ui_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    return tmp_path


def client(root: DataRoot | None):
    app = create_app(root)
    app.config["TESTING"] = True
    return app.test_client()


def test_every_catalog_covers_every_chrome_string_and_nothing_else() -> None:
    keys = used_keys() | STATUS_WORDS
    assert len(keys) > 100
    for lang in ("fr", "de", "it"):
        cat = catalog(lang)
        missing = sorted(keys - set(cat))
        unused = sorted(set(cat) - keys)
        assert not missing, f"{lang}: missing {missing}"
        assert not unused, f"{lang}: unused {unused}"
        for key, value in cat.items():
            assert value.strip(), f"{lang}: empty translation for {key!r}"
            assert set(re.findall(r"\{(\w+)\}", key)) == set(re.findall(r"\{(\w+)\}", value)), (
                f"{lang}: placeholders differ for {key!r}"
            )
    assert translate("it", "Profile") == "Profilo"
    assert translate("de", "{n} error(s)", n=2) == "2 Fehler"
    assert translate("fr", "not a key") == "not a key"


def test_language_is_negotiated_then_chosen_and_remembered(
    data_root: DataRoot, ui_env: Path
) -> None:
    c = client(data_root)
    assert ">Profile<" in c.get("/").get_data(as_text=True)
    body = c.get("/", headers={"Accept-Language": "de-DE,de;q=0.9"}).get_data(as_text=True)
    assert ">Profil<" in body and 'lang="de"' in body
    r = c.post("/language", data={"lang": "it", "next": "/u/test"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/u/test")
    body = c.get("/", headers={"Accept-Language": "de"}).get_data(as_text=True)
    assert ">Profilo<" in body and 'lang="it"' in body
    assert (
        yaml.safe_load((ui_env / "cfg" / "cvac" / "ui.yaml").read_text("utf-8"))["language"] == "it"
    )
    c.post("/language", data={"lang": "xx", "next": "//evil"})
    assert ">Profilo<" in c.get("/").get_data(as_text=True)
    assert (
        c.post("/language", data={"lang": "fr", "next": "//evil"}).headers["Location"].endswith("/")
    )


def test_library_messages_stay_english_inside_a_translated_page(
    data_root: DataRoot, ui_env: Path
) -> None:
    c = client(data_root)
    c.post("/language", data={"lang": "fr"})
    body = c.post("/u/test/fact/exp-acme.f03/verify", follow_redirects=True).get_data(as_text=True)
    assert "cannot be verified without evidence" in body and ">Vérifier<" in body


def test_the_chooser_browses_folders_and_creates_a_new_one(ui_env: Path) -> None:
    home = ui_env / "home"
    (home / "work" / "cv-data").mkdir(parents=True)
    (home / "work" / "cv-data" / "cvac.yaml").write_text("kind: data-root\nschema_version: 1\n")
    (home / ".hidden").mkdir()
    (home / "empty").mkdir()
    (home / "notes.txt").write_text("x")
    listing = browse(str(home))
    assert [f["name"] for f in listing["folders"]] == ["empty", "work"]
    assert listing["parent"] == str(ui_env) and not listing["is_root"] and not listing["empty"]
    assert browse(str(home / "work"))["folders"][0]["is_root"]
    assert browse(str(home / "empty"))["empty"]
    with pytest.raises(CvacError, match="is not a folder"):
        browse(str(home / "notes.txt"))
    with pytest.raises(CvacError, match="absolute path"):
        browse("relative")
    c = client(None)
    body = c.get(f"/open?dir={home}").get_data(as_text=True)
    assert (
        "work/" in body
        and "empty/" in body
        and ".hidden" not in body
        and "Create the data root here" not in body
    )
    body = c.get(f"/open?dir={home / 'empty'}").get_data(as_text=True)
    assert "Create the data root here" in body
    body = c.get(f"/open?dir={home / 'work' / 'cv-data'}").get_data(as_text=True)
    assert "Open this data root" in body
    body = c.get(f"/open?dir={home / 'nope'}", follow_redirects=True).get_data(as_text=True)
    assert "is not a folder" in body
    r = c.post(
        "/open",
        data={"action": "new-folder", "dir": str(home), "name": "my-cv"},
        follow_redirects=True,
    )
    body = r.get_data(as_text=True)
    assert (home / "my-cv" / "cvac.yaml").is_file() and "Data root" in body
    assert "already exists" in c.post(
        "/open",
        data={"action": "new-folder", "dir": str(home), "name": "my-cv"},
        follow_redirects=True,
    ).get_data(as_text=True)
    for bad in ("../x", "a/b", ".dot", "  "):
        with pytest.raises(CvacError, match="not a folder name"):
            new_folder(str(home), bad)
    r = c.post(
        "/open", data={"action": "create", "path": str(home / "empty")}, follow_redirects=True
    )
    assert (home / "empty" / "cvac.yaml").is_file()


def test_german_labels_render_a_cv(data_root: DataRoot) -> None:
    import json

    d = write_spec(data_root, language="de")
    res = resolve(data_root, d, "draft")
    doc = json.loads(res.out_json.read_text("utf-8"))
    assert doc["labels"]["experience"] == "Berufserfahrung" and doc["labels"]["present"] == "heute"
    assert doc["experience"][0]["dates"] == "03.2020 – heute"
    assert doc["languages"][0]["name"] == "Englisch"
    assert set(LANGUAGES) == {"en", "fr", "de", "it"}


def test_new_user_form_offers_the_four_languages(data_root: DataRoot, ui_env: Path) -> None:
    c = client(data_root)
    body = c.get("/new-user").get_data(as_text=True)
    for name in ("English", "Français", "Deutsch", "Italiano"):
        assert f">{name}<" in body
    c.post(
        "/new-user",
        data={
            "slug": "ada",
            "full_name": "Ada",
            "email": "a@example.org",
            "city": "X",
            "pivot_language": "de",
            "target_roles": "x",
        },
    )
    assert (
        yaml.safe_load(data_root.profile_path("ada").read_text("utf-8"))["pivot_language"] == "de"
    )
