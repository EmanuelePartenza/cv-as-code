"""The local UI: pages render from the library, gates are buttons with the CLI's refusals."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import yaml
from conftest import dump, write_job, write_letter_md, write_spec

flask = pytest.importorskip("flask")

from cv_as_code.cli import main  # noqa: E402
from cv_as_code.dataroot import DataRoot  # noqa: E402
from cv_as_code.ui import create_app  # noqa: E402

EXAMPLE = Path(__file__).resolve().parents[1] / "example"
APP = "20260915-saltmere-port-operations-officer"


def client(root: DataRoot) -> flask.testing.FlaskClient:
    app = create_app(root)
    app.config["TESTING"] = True
    return app.test_client()


def page(c: flask.testing.FlaskClient, url: str, status: int = 200) -> str:
    r = c.get(url)
    assert r.status_code == status, (url, r.status_code)
    return r.get_data(as_text=True)


def post(c: flask.testing.FlaskClient, _url: str, **data: str) -> str:
    r = c.post(_url, data=data, follow_redirects=True)
    assert r.status_code == 200, (_url, r.status_code)
    return r.get_data(as_text=True)


# --- pages on the synthetic fixture -------------------------------------------------------


def test_index_lists_users_and_git_state(data_root: DataRoot) -> None:
    body = page(client(data_root), "/")
    assert "Test User" in body and "/u/test" in body
    assert "Not a git repository" in body


def test_profile_shows_facts_statuses_evidence_and_completeness(data_root: DataRoot) -> None:
    body = page(client(data_root), "/u/test")
    assert 'id="exp-acme.f02"' in body and "exp-acme.f03" in body
    assert "2 verified" in body and "1 draft" in body and "1 rejected" in body
    assert "fact `exp-acme.f02` is draft: confirm or reject it" in body
    assert "skill `skill-unproven` has no evidence facts" in body
    assert "/u/test/fact/exp-acme.f02/verify" in body


def test_profile_shows_the_evidence_quote_under_its_anchor(data_root: DataRoot) -> None:
    note = data_root.path / "users" / "test" / "notes" / "quoted.md"
    note.write_text("# Note\n\n## built\n\nI built the widget pipeline, alone.\n\n## other\n\nx\n")
    profile = data_root.profile_path("test")
    prof = yaml.safe_load(profile.read_text("utf-8"))
    prof["experiences"][0]["facts"][0]["evidence"] = "notes/quoted.md#built"
    dump(profile, prof)
    body = page(client(data_root), "/u/test")
    assert "I built the widget pipeline, alone." in body and ">x<" not in body


def test_validate_page_mirrors_the_command(data_root: DataRoot) -> None:
    write_spec(data_root)
    body = page(client(data_root), "/validate")
    assert "0 error(s)" in body and "1 warning(s)" in body


def test_unknown_users_kinds_names_and_traversal_are_404(data_root: DataRoot) -> None:
    c = client(data_root)
    for url in ("/u/nobody", "/u/test/things/x", "/u/test/masters/ghost", "/u/test/masters/../x"):
        page(c, url, 404)
    assert c.post("/u/test/fact/exp-acme.f01/bless").status_code == 404
    assert c.post("/u/test/masters/base/render", data={"mode": "sneaky"}).status_code == 404


def test_posts_from_another_origin_are_refused(data_root: DataRoot) -> None:
    c = client(data_root)
    r = c.post("/u/test/fact/exp-acme.f02/verify", headers={"Origin": "http://evil.example"})
    assert r.status_code == 403
    r = c.post("/u/test/fact/exp-acme.f02/verify", headers={"Referer": "http://evil.example/x"})
    assert r.status_code == 403
    prof = yaml.safe_load(data_root.profile_path("test").read_text("utf-8"))
    assert prof["experiences"][0]["facts"][1]["status"] == "draft"
    r = c.post("/u/test/fact/exp-acme.f02/verify", headers={"Origin": "http://localhost"})
    assert r.status_code == 302


# --- the gate on facts -------------------------------------------------------------------


def test_verify_and_reject_buttons_change_the_profile_like_the_command(
    data_root: DataRoot,
) -> None:
    c = client(data_root)
    body = post(c, "/u/test/fact/exp-acme.f02/verify")
    assert "exp-acme.f02: draft → verified" in body
    prof = yaml.safe_load(data_root.profile_path("test").read_text("utf-8"))
    facts = {f["id"]: f for f in prof["experiences"][0]["facts"]}
    assert facts["exp-acme.f02"]["status"] == "verified" and facts["exp-acme.f02"]["verified_on"]
    body = post(c, "/u/test/fact/exp-acme.f01/reject")
    assert "exp-acme.f01: verified → rejected" in body


def test_verify_refusals_come_back_as_messages(data_root: DataRoot) -> None:
    c = client(data_root)
    assert "cannot be verified without evidence" in post(c, "/u/test/fact/exp-acme.f03/verify")
    assert "is not a fact id" in post(c, "/u/test/fact/nope/verify")


# --- CVs, rendering and the gate on specs ---------------------------------------------------


def test_cv_list_and_spec_page(data_root: DataRoot) -> None:
    write_spec(data_root)
    c = client(data_root)
    body = page(c, "/u/test/cvs")
    assert "/u/test/masters/base" in body and "Widget Engineer" in body
    body = page(c, "/u/test/masters/base")
    assert "exp-acme.f01" in body and "No PDF yet" in body and "Approve" in body


def test_render_draft_then_preview_the_pdf(data_root: DataRoot) -> None:
    write_spec(data_root)
    c = client(data_root)
    body = post(c, "/u/test/masters/base/render", mode="draft")
    assert "rendered Test_User_CV-DRAFT.pdf: 1 page(s)" in body
    assert "/u/test/masters/base/pdf/draft" in body
    r = c.get("/u/test/masters/base/pdf/draft")
    assert r.status_code == 200 and r.mimetype == "application/pdf"
    assert c.get("/u/test/masters/base/pdf/final").status_code == 404


def test_final_render_is_refused_before_approval_and_works_after(data_root: DataRoot) -> None:
    write_spec(data_root)
    c = client(data_root)
    assert "requires status: approved" in post(c, "/u/test/masters/base/render", mode="final")
    body = post(c, "/u/test/masters/base/approve")
    assert "approved on" in body and "Render final" in body
    body = post(c, "/u/test/masters/base/render", mode="final")
    assert "rendered Test_User_CV.pdf: 1 page(s)" in body
    assert (
        yaml.safe_load((data_root.path / "users/test/masters/base/cv-spec.yaml").read_text())[
            "status"
        ]
        == "approved"
    )


def test_approve_is_refused_when_a_cited_fact_is_draft(data_root: DataRoot) -> None:
    write_spec(data_root, facts=("exp-acme.f02",))
    body = post(client(data_root), "/u/test/masters/base/approve")
    assert "cannot approve" in body and "non-verified fact(s): exp-acme.f02" in body


def test_application_page_renders_and_approves_the_letter(data_root: DataRoot) -> None:
    write_job(data_root)
    write_letter_md(data_root)
    d = data_root.path / "users" / "test" / "applications" / "20260101-acme-widget"
    dump(
        d / "cv-spec.yaml",
        {
            **yaml.safe_load((write_spec(data_root) / "cv-spec.yaml").read_text()),
            "job_id": "20260101-acme-widget",
        },
    )
    c = client(data_root)
    url = "/u/test/applications/20260101-acme-widget"
    body = page(c, url)
    assert "Cover letter" in body and "Approve letter" in body
    body = post(c, url + "/letter/render", mode="draft")
    assert "rendered Test_User_Letter-DRAFT.pdf" in body
    assert c.get(url + "/pdf/letter-draft").mimetype == "application/pdf"
    body = post(c, url + "/letter/approve")
    assert "letter approved on" in body
    body = post(c, url + "/letter/render", mode="final")
    assert "rendered Test_User_Letter.pdf" in body


def test_a_letter_without_frontmatter_is_shown_as_invalid_not_hidden(data_root: DataRoot) -> None:
    write_job(data_root)
    path = write_letter_md(data_root)
    path.write_text("Dear team, no frontmatter.\n", "utf-8")
    d = path.parent
    dump(
        d / "cv-spec.yaml",
        {
            **yaml.safe_load((write_spec(data_root) / "cv-spec.yaml").read_text()),
            "job_id": "20260101-acme-widget",
        },
    )
    c = client(data_root)
    assert "invalid" in page(c, "/u/test/cvs")
    body = page(c, "/u/test/applications/20260101-acme-widget")
    assert "has no YAML frontmatter" in body
    body = post(c, "/u/test/applications/20260101-acme-widget/letter/approve")
    assert "has no YAML frontmatter" in body


# --- on the example user -------------------------------------------------------------------


@pytest.fixture
def example(tmp_path: Path) -> DataRoot:
    root = tmp_path / "example"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns("*.pdf", "build"))
    return DataRoot.load(root)


def test_robin_end_to_end_in_the_browser(example: DataRoot) -> None:
    c = client(example)
    assert "Robin Ashcombe" in page(c, "/")
    body = page(c, "/u/robin")
    assert "exp-skerra.f09" in body and "Six years without an unplanned outage" in body
    assert "port-operations-fr" in page(c, "/u/robin/cvs")
    body = post(c, "/u/robin/masters/port-operations-en/render", mode="final")
    assert (
        "1 page(s)" in body
        and c.get("/u/robin/masters/port-operations-en/pdf/final").status_code == 200
    )
    assert "already approved" in post(c, "/u/robin/masters/port-operations-en/approve")
    body = page(c, f"/u/robin/applications/{APP}")
    assert "Cover letter" in body and "approved" in body
    assert "exp-skerra.f10: draft → verified" in post(c, "/u/robin/fact/exp-skerra.f10/verify")


# --- the command -----------------------------------------------------------------------------


def test_cvac_ui_names_the_missing_extra(
    data_root: DataRoot, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in list(sys.modules):
        if name == "flask" or name.startswith("flask.") or name.startswith("cv_as_code.ui"):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "flask", None)
    assert main(["ui", "--no-browser", "--data-root", str(data_root.path)]) == 1
    assert "needs the `ui` extra" in capsys.readouterr().err


# --- slice 2: the chooser, jobs, documents, the editor, runs -----------------------------------


@pytest.fixture
def ui_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    return tmp_path


def test_without_a_root_every_page_leads_to_the_chooser(data_root: DataRoot, ui_env: Path) -> None:
    app = create_app(None)
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.get("/")
    assert r.status_code == 302 and r.headers["Location"].endswith("/open")
    assert "Where is your data" in page(c, "/open")
    body = post(c, "/open", path=str(data_root.path))
    assert "Test User" in body and f"data root: {data_root.path}" in body
    assert str(data_root.path) in (ui_env / "cfg" / "cvac" / "ui.yaml").read_text("utf-8")
    assert str(data_root.path) in page(c, "/open")


def test_chooser_creates_a_root_only_when_asked_and_refuses_other_directories(
    ui_env: Path,
) -> None:
    app = create_app(None)
    app.config["TESTING"] = True
    c = app.test_client()
    fresh = ui_env / "fresh"
    assert "to scaffold a data root there" in post(c, "/open", path=str(fresh))
    body = post(c, "/open", path=str(fresh), create="on")
    assert (fresh / "cvac.yaml").is_file() and "No user yet" in body
    other = ui_env / "other"
    other.mkdir()
    (other / "x.txt").write_text("x")
    assert "is not a data root" in post(c, "/open", path=str(other), create="on")
    assert "absolute path" in post(c, "/open", path="relative/dir")


def test_new_user_form_scaffolds_a_valid_user(data_root: DataRoot, ui_env: Path) -> None:
    c = client(data_root)
    body = post(
        c,
        "/new-user",
        slug="ada",
        full_name="Ada Example",
        email="ada@example.org",
        city="Testville",
        country="XX",
        pivot_language="en",
        target_roles="engineer, analyst",
    )
    assert "user `ada` created" in body and "Questionnaire" in body
    assert data_root.profile_path("ada").is_file()
    assert "0 error(s)" in page(c, "/validate")
    assert "at least one target role" in post(
        c, "/new-user", slug="bob", full_name="B", email="b@example.org", city="X", target_roles=""
    )


def test_jobs_area_saves_a_posting_verbatim_and_refuses_duplicates(
    data_root: DataRoot, ui_env: Path
) -> None:
    c = client(data_root)
    assert "No posting yet" in page(c, "/u/test/jobs")
    form = {
        "company": "Acme Widgets",
        "title": "Widget Engineer",
        "date": "2026-09-24",
        "channel": "careers page",
        "url": "https://example.com/jobs/1",
        "text": "Widget Engineer wanted.\n\n3+ years of widgets.",
    }
    body = post(c, "/u/test/jobs/new", **form)
    assert "jobs/20260924-acme-widgets-widget-engineer/raw.txt written" in body
    raw = (
        data_root.path / "jobs" / "20260924-acme-widgets-widget-engineer" / "raw.txt"
    ).read_text()
    assert raw.startswith(
        "SOURCE: careers page\nCOMPANY: Acme Widgets\nTITLE: Widget Engineer\nURL: https://example.com/jobs/1\n"
    )
    assert raw.endswith("---\nWidget Engineer wanted.\n\n3+ years of widgets.\n")
    assert "already exists" in post(c, "/u/test/jobs/new", **form)
    assert "is not a date" in post(c, "/u/test/jobs/new", **{**form, "date": "yesterday"})
    assert "paste the posting" in post(c, "/u/test/jobs/new", **{**form, "text": " "})
    body = page(c, "/u/test/jobs/20260924-acme-widgets-widget-engineer")
    assert "Normalise (10)" in body and "Widget Engineer wanted." in body
    page(c, "/u/test/jobs/20260924-ghost", 404)


def test_job_page_runs_a_stage_and_shows_its_log(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import stat

    from test_runner import FAKE

    write_job(data_root)
    fake = ui_env / "fake-claude"
    fake.write_text(FAKE, "utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(fake))
    app = create_app(data_root)
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/u/test/jobs/20260101-acme-widget/run/20_match")
    assert r.status_code == 302 and "/runs/" in r.headers["Location"]
    run_id = r.headers["Location"].rsplit("/", 1)[1]
    run = app.extensions["cvac"].runs.wait(run_id)
    assert run.status == "failed"
    body = page(c, f"/runs/{run_id}")
    assert "was not written" in body and "[Write]" in body and "Back to where" in body
    assert "20_match" in page(c, "/runs")
    assert c.post("/u/test/jobs/20260101-acme-widget/run/99_nope").status_code == 404
    assert "is missing" in post(c, "/u/test/jobs/20260101-acme-widget/run/30_tailor", master="base")
    page(c, "/runs/nope", 404)


def test_documents_area_uploads_extracts_and_edits(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import io
    import stat

    from test_runner import FAKE

    fake = ui_env / "fake-claude"
    fake.write_text(FAKE, "utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(fake))
    app = create_app(data_root)
    app.config["TESTING"] = True
    c = app.test_client()
    body = page(c, "/u/test/documents")
    assert "01-onboarding" in body and "profile.yaml" in body
    r = c.post(
        "/u/test/documents/upload",
        data={"file": (io.BytesIO(b"I built widgets for years."), "Old CV.txt")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "inbox/Old_CV.txt uploaded" in r.get_data(as_text=True)
    assert (data_root.path / "users" / "test" / "inbox" / "Old_CV.txt").is_file()
    r = c.post(
        "/u/test/documents/upload",
        data={"file": (io.BytesIO(b"x"), "evil.exe")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "unsupported type" in r.get_data(as_text=True)
    r = c.post("/u/test/documents/extract", data={"document": "inbox/Old_CV.txt", "name": "old-cv"})
    assert r.status_code == 302 and "/runs/" in r.headers["Location"]
    assert "is not a document" in post(c, "/u/test/documents/extract", document="../x", name="x")
    assert "is not a note name" in post(
        c, "/u/test/documents/extract", document="inbox/Old_CV.txt", name="Bad Name"
    )
    app.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    r = c.post("/u/test/documents/questionnaire", data={"name": "01-onboarding"})
    assert r.status_code == 302 and "/runs/" in r.headers["Location"]
    app.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])


def test_editor_saves_only_what_validates(data_root: DataRoot, ui_env: Path) -> None:
    c = client(data_root)
    search = data_root.path / "users" / "test" / "search.yaml"
    before = search.read_text("utf-8")
    assert "target_roles" in page(c, "/u/test/edit/search.yaml")
    body = post(c, "/u/test/edit/search.yaml", text="kind: search\nuser: test\n")
    assert "Not saved" in body and "required property" in body
    assert search.read_text("utf-8") == before
    body = post(
        c,
        "/u/test/edit/search.yaml",
        text=before.replace("confidential: false", "confidential: true"),
    )
    assert "saved and valid" in body and "confidential: true" in search.read_text("utf-8")
    note = data_root.path / "users" / "test" / "notes" / "fresh.md"
    body = post(c, "/u/test/edit/notes/fresh.md", text="---\nkind: evidence\n---\n")
    assert "Not saved" in body and not note.exists()
    page(c, "/u/test/edit/../cvac.yaml", 404)
    page(c, "/u/test/edit/masters/base/cv-spec.yaml", 404)


def test_binary_inputs_do_not_break_the_pack(data_root: DataRoot) -> None:
    from cv_as_code.stages import pack, resolve_stage

    doc = data_root.path / "users" / "test" / "inbox" / "scan.pdf"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_bytes(b"%PDF-1.4\n\xff\xfe\x00binary")
    text = pack(
        data_root,
        resolve_stage(data_root, "03_extract", {"document": "inbox/scan.pdf", "name": "scan"}),
    )
    assert "binary document at `users/test/inbox/scan.pdf`" in text


def test_a_successful_run_and_an_engine_failure_are_both_reported(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import stat

    import yaml
    from conftest import MATCH
    from test_runner import FAKE

    write_job(data_root)
    fake = ui_env / "fake-claude"
    fake.write_text(FAKE, "utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(fake))
    out = ui_env / "match.yaml"
    out.write_text(yaml.safe_dump(MATCH, sort_keys=False), "utf-8")
    monkeypatch.setenv("FAKE_OUTPUT", str(out))
    app = create_app(data_root)
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/u/test/jobs/20260101-acme-widget/run/20_match")
    run = app.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "ok" and run.result is not None and run.result.ok
    body = page(c, f"/runs/{run.id}")
    assert "ok: users/test/matches" in body and "cost 0.0123" in body
    assert "stretch" in page(c, "/u/test/jobs/20260101-acme-widget")
    monkeypatch.setenv("FAKE_EXIT", "2")
    r = c.post("/u/test/jobs/20260101-acme-widget/run/40_gap_plan")
    run = app.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "failed"
    assert "engine: engine exited with code 2" in page(c, f"/runs/{run.id}")


def test_a_missing_engine_is_an_immediate_message_not_a_thread(
    data_root: DataRoot, ui_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_job(data_root)
    monkeypatch.setenv("CVAC_CLAUDE_BIN", str(ui_env / "no-such-claude"))
    c = client(data_root)
    body = post(c, "/u/test/jobs/20260101-acme-widget/run/20_match")
    assert "is not a file" in body
    assert c.application.extensions["cvac"].runs.listing() == []


def test_apply_button_runs_stage_04_on_a_proposed_note_only(
    data_root: DataRoot, ui_env: Path
) -> None:
    from test_apply import fact, write_note

    write_note(data_root, fact("exp-acme", "Shipped releases", "r"), name="fresh")
    write_note(data_root, fact("exp-acme", "Older", "o"), name="done")
    done = data_root.path / "users" / "test" / "notes" / "done.md"
    done.write_text(done.read_text("utf-8").replace("status: proposed", "status: applied"), "utf-8")
    app = create_app(data_root)
    app.config["TESTING"] = True
    c = app.test_client()
    body = page(c, "/u/test/documents")
    assert body.count("Apply to the profile (04)") == 1
    r = c.post("/u/test/documents/apply", data={"name": "fresh"})
    assert r.status_code == 302 and "/runs/" in r.headers["Location"]
    run = app.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "ok" and run.stage == "04_apply"
    assert "added exp-acme.f04 (draft)" in page(c, f"/runs/{run.id}")
    assert "exp-acme.f04" in page(c, "/u/test")
    assert "is not an evidence note" in post(c, "/u/test/documents/apply", name="ghost")
    assert "is not an evidence note" in post(c, "/u/test/documents/apply", name="../profile")
    r = c.post("/u/test/documents/apply", data={"name": "done"})
    run = app.extensions["cvac"].runs.wait(r.headers["Location"].rsplit("/", 1)[1])
    assert run.status == "failed" and "already applied" in page(c, f"/runs/{run.id}")
