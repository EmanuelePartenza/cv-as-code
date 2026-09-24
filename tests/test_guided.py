"""The guided path: many documents in, extraction chained to apply, review with quotes, the
questionnaire as a form, the start page."""

from __future__ import annotations

import io
import shutil
import stat
from pathlib import Path

import pytest
import yaml
from conftest import write_job

flask = pytest.importorskip("flask")

from cv_as_code.apply import apply_note, archive_source  # noqa: E402
from cv_as_code.dataroot import DataRoot  # noqa: E402
from cv_as_code.errors import CvacError  # noqa: E402
from cv_as_code.facts import set_claim  # noqa: E402
from cv_as_code.ui import create_app  # noqa: E402
from cv_as_code.ui.questionnaire import (  # noqa: E402
    add_block,
    parse,
    render,
    skeleton_text,
    split_front,
)
from cv_as_code.validate import discover_all, validate_files  # noqa: E402

EXAMPLE = Path(__file__).resolve().parents[1] / "example"
SKELETON = (
    Path(__file__).resolve().parents[1]
    / "src/cv_as_code/pipeline/05_interview/questionnaire.skeleton.md"
)


@pytest.fixture
def ui_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from test_runner import FAKE

    fake = tmp_path / "fake-claude"
    fake.write_text(FAKE, "utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(fake))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FAKE_OUTPUT", raising=False)
    return tmp_path


def client(root: DataRoot):
    app = create_app(root)
    app.config["TESTING"] = True
    return app.test_client()


def page(c, url: str, status: int = 200) -> str:
    r = c.get(url)
    assert r.status_code == status, (url, r.status_code)
    return r.get_data(as_text=True)


def post(c, url: str, **data) -> str:
    r = c.post(url, data=data, follow_redirects=True)
    assert r.status_code == 200, (url, r.status_code)
    return r.get_data(as_text=True)


# --- library: reword, archive ------------------------------------------------------------


def test_set_claim_rewords_in_place_and_resets_a_verified_fact(data_root: DataRoot) -> None:
    profile = data_root.profile_path("test")
    before = profile.read_text("utf-8")
    change = set_claim(data_root, "test", "exp-acme.f01", "Built the  whole widget pipeline ")
    assert change.old_status == "verified" and change.new_status == "draft"
    prof = yaml.safe_load(profile.read_text("utf-8"))
    fact = prof["experiences"][0]["facts"][0]
    assert fact["claim"] == "Built the whole widget pipeline" and fact["status"] == "draft"
    assert fact["verified_on"] is None
    change = set_claim(data_root, "test", "exp-acme.f02", "Reduced defects: a lot")
    assert change.old_status == "draft" and change.new_status == "draft"
    assert (
        "Reduced defects: a lot"
        in yaml.safe_load(profile.read_text("utf-8"))["experiences"][0]["facts"][1]["claim"]
    )
    assert profile.read_text("utf-8").count("\n") == before.count("\n")
    with pytest.raises(CvacError, match="cannot be empty"):
        set_claim(data_root, "test", "exp-acme.f01", "  ")
    with pytest.raises(CvacError, match="does not exist"):
        set_claim(data_root, "test", "exp-acme.f09", "x")
    assert validate_files(data_root, discover_all(data_root)).errors == []


def test_set_claim_handles_a_folded_claim(tmp_path: Path) -> None:
    root = DataRoot.load(shutil.copytree(EXAMPLE, tmp_path / "ex"))
    change = set_claim(root, "robin", "exp-skerra.f01", "Sole keeper of the light")
    assert change.new_status == "draft"
    prof = yaml.safe_load(root.profile_path("robin").read_text("utf-8"))
    assert prof["experiences"][0]["facts"][0]["claim"] == "Sole keeper of the light"
    # the approved CVs cite that fact: until it is verified again they no longer validate
    errors = validate_files(root, discover_all(root)).errors
    assert errors and all("cites non-verified fact(s): exp-skerra.f01" in e for e in errors)
    from cv_as_code.facts import set_status

    set_status(root, "robin", ["exp-skerra.f01"], "verified")
    assert validate_files(root, discover_all(root)).errors == []


def test_apply_archives_the_inbox_document_and_repoints_the_note(data_root: DataRoot) -> None:
    from test_apply import fact, write_note

    note = write_note(data_root, fact("exp-acme", "Shipped releases", "r"))
    apply_note(data_root, "test", "old-cv")
    udir = data_root.path / "users" / "test"
    assert (
        not (udir / "inbox" / "old-cv.md").exists() and (udir / "sources" / "old-cv.md").is_file()
    )
    assert "source: sources/old-cv.md" in note.read_text("utf-8")
    assert validate_files(data_root, discover_all(data_root)).errors == []
    assert archive_source(data_root, "test", note) is None


# --- documents: many at once, chained extraction --------------------------------------------


def test_many_documents_upload_at_once_and_bad_ones_are_named(
    data_root: DataRoot, ui_env: Path
) -> None:
    c = client(data_root)
    r = c.post(
        "/u/test/documents/upload",
        data={
            "file": [
                (io.BytesIO(b"cv"), "old cv.txt"),
                (io.BytesIO(b"rev"), "review 2024.md"),
                (io.BytesIO(b"x"), "bad.exe"),
            ]
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    body = r.get_data(as_text=True)
    assert "2 document(s) uploaded" in body and "unsupported type" in body
    inbox = data_root.path / "users" / "test" / "inbox"
    assert (inbox / "old_cv.txt").is_file() and (inbox / "review_2024.md").is_file()
    assert "Extract all with Claude (2 documents)" in page(c, "/u/test/documents")


def test_extract_chains_to_apply_and_archives(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inbox = data_root.path / "users" / "test" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "old-cv.md").write_text("I shipped releases.\n", "utf-8")
    note = ui_env / "note.md"
    note.write_text(
        "---\nschema_version: 1\nkind: evidence\nuser: test\nsource: inbox/old-cv.md\n"
        'extracted_on: "2026-01-05"\nstatus: proposed\nfacts:\n  - parent: exp-acme\n'
        "    claim: Shipped releases\n    metrics: {}\n    tags: []\n    quote: q\n"
        "    anchor: r\n---\n\n## r\nq\n",
        "utf-8",
    )
    monkeypatch.setenv("FAKE_OUTPUT", str(note))
    c = client(data_root)
    r = c.post("/u/test/documents/extract", data={"document": "inbox/old-cv.md", "name": "old-cv"})
    run = c.application.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "ok" and run.stage == "03_extract → 04_apply"
    body = page(c, f"/runs/{run.id}")
    assert (
        "── 04_apply" in body
        and "added exp-acme.f04 (draft)" in body
        and "archived as sources/old-cv.md" in body
    )
    assert not (inbox / "old-cv.md").exists()
    assert "exp-acme.f04" in page(c, "/u/test/review")
    assert "nothing to extract" in post(c, "/u/test/documents/extract-all")


def test_extract_all_queues_every_pending_document(data_root: DataRoot, ui_env: Path) -> None:
    inbox = data_root.path / "users" / "test" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "a.md").write_text("a\n")
    (inbox / "b.md").write_text("b\n")
    c = client(data_root)
    r = c.post("/u/test/documents/extract-all")
    run = c.application.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.stage == "03_extract → 04_apply → 03_extract → 04_apply"
    assert run.status == "failed" and "was not written" in run.summary


# --- review ---------------------------------------------------------------------------------


def test_review_shows_drafts_with_quotes_and_confirms_selected(
    data_root: DataRoot, ui_env: Path
) -> None:
    (data_root.path / "users" / "test" / "notes" / "evidence.md").write_text(
        "# Evidence\n\n## defects\n\nCut defects by half.\n", "utf-8"
    )
    c = client(data_root)
    body = page(c, "/u/test/review")
    assert "exp-acme.f02" in body and "Cut defects by half." in body and "exp-acme.f01" not in body
    assert "1 to review" in body
    body = post(c, "/u/test/review/verify", ids="exp-acme.f02")
    assert "exp-acme.f02: draft → verified" in body and "Nothing to review" in body
    body = post(c, "/u/test/review/reject", ids="exp-acme.f02")
    assert "exp-acme.f02: verified → rejected" in body
    assert "select at least one fact" in post(c, "/u/test/review/verify")
    assert c.post("/u/test/review/bless", data={"ids": "x"}).status_code == 404
    body = post(
        c,
        "/u/test/fact/exp-acme.f01/claim",
        claim="Built it all",
        next="/u/test/review#exp-acme.f01",
    )
    assert "exp-acme.f01 reworded and back to draft" in body and "exp-acme.f01" in body
    assert "cannot be empty" in post(c, "/u/test/fact/exp-acme.f01/claim", claim=" ")


# --- questionnaire ---------------------------------------------------------------------------


def test_questionnaire_round_trips_the_example_and_the_skeleton() -> None:
    for path in (EXAMPLE / "users/robin/interviews/01-onboarding.md", SKELETON):
        text = path.read_text("utf-8")
        q = parse(text, path.name)
        assert render(q, split_front(text)) == text
    q = parse(SKELETON.read_text("utf-8"), "s")
    assert q.answered == (0, 30) and [s.letter for s in q.sections] == list("ABCDEFGH")
    add_block(q, "C")
    assert (
        q.sections[2].blocks[-1].title == "Position 2"
        and len(q.sections[2].blocks[-1].questions) == 7
    )
    with pytest.raises(CvacError, match="not repeatable"):
        add_block(q, "A")


def test_questionnaire_form_saves_in_sittings_and_marks_filled(
    data_root: DataRoot, ui_env: Path
) -> None:
    c = client(data_root)
    body = post(c, "/u/test/questionnaire/new", name="01-onboarding", language="en")
    assert "created from the standard skeleton" in body and "0 of 30 questions answered" in body
    path = data_root.path / "users" / "test" / "interviews" / "01-onboarding.md"
    assert path.is_file() and "user: test" in path.read_text("utf-8")
    body = post(
        c,
        "/u/test/questionnaire/01-onboarding",
        **{"a:A:0:A1": "Test User", "a:A:0:A3": "test.user@example.com", "action": "save"},
    )
    assert "2 of 30 questions answered" in body
    text = path.read_text("utf-8")
    assert "- A1. Full name as it should appear on a CV.\n  > Test User\n- A2." in text
    body = post(c, "/u/test/questionnaire/01-onboarding", **{"action": "add:C"})
    assert "Position 2" in body and "### Position 2" in path.read_text("utf-8")
    body = post(
        c,
        "/u/test/questionnaire/01-onboarding",
        **{"a:C:1:C3": "Kept the light\nevery night", "action": "filled"},
    )
    assert "status: filled" in path.read_text("utf-8") and "Extract my answers (03)" in body
    assert "  > Kept the light\n  > every night\n" in path.read_text("utf-8")
    assert validate_files(data_root, [path]).errors == []
    assert "already exists" in post(c, "/u/test/questionnaire/new", name="01-onboarding")
    page(c, "/u/test/questionnaire/ghost", 404)
    page(c, "/u/test/questionnaire/../x", 404)
    assert "user: test" in skeleton_text("test", "it") and "language: it" in skeleton_text(
        "test", "it"
    )


# --- start -----------------------------------------------------------------------------------


def test_start_page_shows_the_four_doors_and_their_state(data_root: DataRoot, ui_env: Path) -> None:
    inbox = data_root.path / "users" / "test" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "a.md").write_text("a\n")
    write_job(data_root)
    c = client(data_root)
    body = page(c, "/u/test/start")
    assert "1 to extract" in body and "1 to review" in body and "2 confirmed" in body
    assert "1 posting(s)" in body and "Start a questionnaire" in body
    assert "skill `skill-unproven` has no evidence facts" in body
    post(c, "/u/test/questionnaire/new", name="01-onboarding")
    assert "Continue the questionnaire" in page(c, "/u/test/start")
    assert ">Start<" in page(c, "/") and ">Review<" in page(c, "/")
