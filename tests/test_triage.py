"""Documents read together: directory inputs, the sources index, the triage run, archiving."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest
import yaml
from conftest import write_job

flask = pytest.importorskip("flask")

from cv_as_code.apply import apply_note, archive_batch  # noqa: E402
from cv_as_code.dataroot import DataRoot  # noqa: E402
from cv_as_code.errors import CvacError  # noqa: E402
from cv_as_code.stages import describe, files_in, pack, resolve_stage  # noqa: E402
from cv_as_code.ui import create_app  # noqa: E402
from cv_as_code.validate import discover_all, validate_files  # noqa: E402

INDEX = """schema_version: 1
kind: sources
user: test
updated: "2026-01-06"
documents:
  - path: inbox/cv-en.md
    kind: evidence
    language: en
    about: The person's CV, English, the fullest version
  - path: inbox/cv-fr.md
    kind: duplicate
    language: fr
    about: The same CV in French
    duplicate_of: inbox/cv-en.md
  - path: inbox/role.md
    kind: context
    about: The company's description of the role; not about the person
    context_for: [inbox/cv-en.md, exp-acme]
  - path: inbox/timetable.md
    kind: irrelevant
    about: A ferry timetable
"""

NOTE = """---
schema_version: 1
kind: evidence
user: test
source: inbox/cv-en.md
extracted_on: "2026-01-06"
status: proposed
duplicates: [inbox/cv-fr.md]
facts:
  - parent: exp-acme
    claim: Ran the widget line
    metrics: {}
    tags: []
    quote: ran the line
    anchor: line
---

## line
ran the line
"""


def fill_inbox(root: DataRoot) -> Path:
    inbox = root.path / "users" / "test" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    for name in ("cv-en.md", "cv-fr.md", "role.md", "timetable.md"):
        (inbox / name).write_text(f"{name}\n", "utf-8")
    (inbox / ".hidden.md").write_text("x\n")
    (inbox / "README.md").write_text("inbox\n")
    return inbox


@pytest.fixture
def ui_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from test_runner import FAKE

    fake = tmp_path / "fake-claude"
    fake.write_text(FAKE, "utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(fake))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FAKE_OUTPUT", raising=False)
    monkeypatch.delenv("FAKE_OUTPUTS", raising=False)
    return tmp_path


def client(root: DataRoot):
    app = create_app(root)
    app.config["TESTING"] = True
    return app.test_client()


# --- directory inputs --------------------------------------------------------------------------


def test_a_directory_input_lists_and_packs_every_document(data_root: DataRoot) -> None:
    inbox = fill_inbox(data_root)
    assert [p.name for p in files_in(inbox)] == ["cv-en.md", "cv-fr.md", "role.md", "timetable.md"]
    rs = resolve_stage(data_root, "02_triage", {})
    text = describe(data_root, rs)
    assert (
        "users/test/inbox  [4 file(s)]" in text and "users/test/sources  [absent, optional]" in text
    )
    bundle = pack(data_root, rs)
    assert "## Input users/test/inbox (4 document(s))" in bundle
    assert "## Input users/test/inbox/role.md" in bundle and ".hidden" not in bundle
    assert bundle.count("## Input users/test/inbox/") == 4
    assert "## Input users/test/sources.yaml\n\n_(absent; this input is optional)_" in bundle
    assert rs.output == data_root.path / "users" / "test" / "sources.yaml"


# --- the index and its rules --------------------------------------------------------------------


def test_sources_index_validates_and_its_rules_bite(data_root: DataRoot) -> None:
    fill_inbox(data_root)
    path = data_root.path / "users" / "test" / "sources.yaml"
    path.write_text(INDEX, "utf-8")
    assert validate_files(data_root, [path]).errors == [] and path in discover_all(data_root)
    doc = yaml.safe_load(INDEX)
    doc["documents"][1]["duplicate_of"] = None
    path.write_text(yaml.safe_dump(doc, sort_keys=False), "utf-8")
    assert any(
        "duplicate without duplicate_of" in e for e in validate_files(data_root, [path]).errors
    )
    doc = yaml.safe_load(INDEX)
    doc["documents"][1]["duplicate_of"] = "inbox/ghost.md"
    doc["documents"][2]["duplicate_of"] = "inbox/cv-en.md"
    doc["documents"].append({"path": "inbox/missing.md", "kind": "evidence", "about": "x"})
    doc["documents"].append({"path": "inbox/cv-en.md", "kind": "evidence", "about": "again"})
    path.write_text(yaml.safe_dump(doc, sort_keys=False), "utf-8")
    errors = validate_files(data_root, [path]).errors
    for needle in (
        "is not in the index",
        "has duplicate_of but is `context`",
        "does not exist under",
        "is listed twice",
    ):
        assert any(needle in e for e in errors), needle
    doc = yaml.safe_load(INDEX)
    doc["documents"][0]["note"] = "ghost"
    doc["documents"][1]["duplicate_of"] = "inbox/cv-fr.md"
    doc["documents"][1]["kind"] = "duplicate"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), "utf-8")
    errors = validate_files(data_root, [path]).errors
    assert any("note `ghost` does not exist" in e for e in errors)
    assert any("is itself a duplicate" in e for e in errors)


# --- archiving a batch ----------------------------------------------------------------------------


def test_apply_and_archive_batch_keep_the_index_true(data_root: DataRoot) -> None:
    fill_inbox(data_root)
    udir = data_root.path / "users" / "test"
    (udir / "sources.yaml").write_text(INDEX, "utf-8")
    (udir / "notes").mkdir(exist_ok=True)
    (udir / "notes" / "cv-en.md").write_text(NOTE, "utf-8")
    result = apply_note(data_root, "test", "cv-en")
    assert "document archived as sources/cv-en.md" in result.notes
    index = yaml.safe_load((udir / "sources.yaml").read_text("utf-8"))
    by_path = {d["path"]: d for d in index["documents"]}
    assert by_path["sources/cv-en.md"]["note"] == "cv-en"
    assert by_path["inbox/cv-fr.md"]["duplicate_of"] == "sources/cv-en.md"
    assert by_path["inbox/role.md"]["context_for"] == ["sources/cv-en.md", "exp-acme"]
    moved = archive_batch(data_root, "test")
    assert sorted(moved) == [
        "inbox/cv-fr.md → sources/cv-fr.md",
        "inbox/role.md → sources/role.md",
        "inbox/timetable.md → sources/timetable.md",
    ]
    index = yaml.safe_load((udir / "sources.yaml").read_text("utf-8"))
    assert {d["path"] for d in index["documents"]} == {
        "sources/cv-en.md",
        "sources/cv-fr.md",
        "sources/role.md",
        "sources/timetable.md",
    }
    assert not any(
        p.name != "README.md" and not p.name.startswith(".") for p in (udir / "inbox").iterdir()
    )
    assert validate_files(data_root, discover_all(data_root)).errors == []
    assert archive_batch(data_root, "test") == []


# --- the run: sort, extract, apply, archive ----------------------------------------------------


def test_extract_all_sorts_then_extracts_only_the_evidence_and_archives(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fill_inbox(data_root)
    (ui_env / "index.yaml").write_text(INDEX, "utf-8")
    (ui_env / "note.md").write_text(NOTE, "utf-8")
    monkeypatch.setenv(
        "FAKE_OUTPUTS", f"02_triage={ui_env / 'index.yaml'},03_extract={ui_env / 'note.md'}"
    )
    c = client(data_root)
    body = c.get("/u/test/documents").get_data(as_text=True)
    assert (
        "Sort, extract and apply everything with Claude (4 documents)" in body
        and "Only sort them (02)" in body
    )
    r = c.post("/u/test/documents/extract-all")
    run = c.application.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "ok", run.summary
    assert run.stage == "02_triage → 03_extract → 04_apply → archive"
    body = c.get(f"/runs/{run.id}").get_data(as_text=True)
    assert (
        "── 02_triage" in body
        and "── 03_extract" in body
        and "── 04_apply" in body
        and "── archive" in body
    )
    assert "inbox/role.md → sources/role.md" in body and body.count("── 03_extract") == 1
    udir = data_root.path / "users" / "test"
    assert (udir / "sources" / "cv-fr.md").is_file() and (
        udir / "sources" / "timetable.md"
    ).is_file()
    prof = yaml.safe_load(data_root.profile_path("test").read_text("utf-8"))
    assert any(f["claim"] == "Ran the widget line" for f in prof["experiences"][0]["facts"])
    body = c.get("/u/test/documents").get_data(as_text=True)
    assert (
        ">duplicate<" in body
        and ">context<" in body
        and ">irrelevant<" in body
        and "The same CV in French" in body
    )
    assert "nothing to extract" in c.post(
        "/u/test/documents/extract-all", follow_redirects=True
    ).get_data(as_text=True)
    assert validate_files(data_root, discover_all(data_root)).errors == []


def test_only_sort_runs_the_triage_alone(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fill_inbox(data_root)
    (ui_env / "index.yaml").write_text(INDEX, "utf-8")
    monkeypatch.setenv("FAKE_OUTPUT", str(ui_env / "index.yaml"))
    c = client(data_root)
    r = c.post("/u/test/documents/triage")
    run = c.application.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "ok" and run.stage == "02_triage"
    body = c.get("/u/test/documents").get_data(as_text=True)
    assert ">evidence<" in body and "Extract with Claude (03)" in body
    assert body.count("Extract with Claude (03)") == 1  # only the evidence document offers it
    (data_root.path / "users" / "test" / "inbox" / "cv-en.md").unlink()
    (data_root.path / "users" / "test" / "inbox" / "cv-fr.md").unlink()
    (data_root.path / "users" / "test" / "inbox" / "role.md").unlink()
    (data_root.path / "users" / "test" / "inbox" / "timetable.md").unlink()
    assert "the inbox is empty" in c.post(
        "/u/test/documents/triage", follow_redirects=True
    ).get_data(as_text=True)


def test_a_run_may_not_start_with_a_code_step(data_root: DataRoot, ui_env: Path) -> None:
    write_job(data_root)
    manager = create_app(data_root).extensions["cvac"].runs
    with pytest.raises(CvacError, match="starts with a stage"):
        manager.start_steps(data_root, [("code", "x", lambda root: [])], "/")
