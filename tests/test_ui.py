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


def post(c: flask.testing.FlaskClient, url: str, **data: str) -> str:
    r = c.post(url, data=data, follow_redirects=True)
    assert r.status_code == 200, (url, r.status_code)
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
    assert "cannot approve" in post(
        c, "/u/test/applications/20260101-acme-widget/letter/approve"
    ) or "no YAML frontmatter" in post(
        c, "/u/test/applications/20260101-acme-widget/letter/approve"
    )


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
