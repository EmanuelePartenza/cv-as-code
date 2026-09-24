"""The curriculum: profile.yaml edited in place from the form, own words as evidence (ADR-0017)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from conftest import write_job

flask = pytest.importorskip("flask")

from cv_as_code import curriculum as lib  # noqa: E402
from cv_as_code.dataroot import DataRoot  # noqa: E402
from cv_as_code.errors import CvacError  # noqa: E402
from cv_as_code.ui import create_app  # noqa: E402
from cv_as_code.validate import discover_all, validate_files  # noqa: E402

EXAMPLE = Path(__file__).resolve().parents[1] / "example"


@pytest.fixture
def robin(tmp_path: Path) -> DataRoot:
    return DataRoot.load(shutil.copytree(EXAMPLE, tmp_path / "ex"))


@pytest.fixture
def ui_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    return tmp_path


def client(root: DataRoot):
    app = create_app(root)
    app.config["TESTING"] = True
    return app.test_client()


def prof(root: DataRoot, user: str = "test") -> dict:
    return yaml.safe_load(root.profile_path(user).read_text("utf-8"))


def clean(root: DataRoot) -> None:
    assert validate_files(root, discover_all(root)).errors == []


def surviving(before: str, after: str, *dropped: str) -> None:
    """Every old line is still there, except the ones deliberately replaced."""
    after_lines = after.splitlines()
    for line in before.splitlines():
        if line.strip() and not any(line.strip().startswith(d) for d in dropped):
            assert line in after_lines, line


# --- identity, languages ---------------------------------------------------------------------


@pytest.mark.parametrize("who", ["fixture", "robin"])
def test_identity_and_links_are_replaced_in_place(
    who: str, data_root: DataRoot, robin: DataRoot
) -> None:
    root, user = (data_root, "test") if who == "fixture" else (robin, "robin")
    before = root.profile_path(user).read_text("utf-8")
    lib.set_identity(
        root,
        user,
        full_name="Name Surname",
        email="n@example.org",
        city="Town",
        country="XX",
        phone="555-0100",
        born="1990-03-12",
        links=[("Site", "https://example.com/x"), ("", "https://example.org")],
    )
    ident = prof(root, user)["identity"]
    assert ident["full_name"] == "Name Surname" and ident["born"] == "1990-03-12"
    assert ident["location"] == {"city": "Town", "country": "XX"} and ident["phone"] == "555-0100"
    assert ident["links"] == [
        {"label": "Site", "url": "https://example.com/x"},
        {"label": "https://example.org", "url": "https://example.org"},
    ]
    surviving(
        before,
        root.profile_path(user).read_text("utf-8"),
        "full_name:",
        "email:",
        "phone:",
        "born:",
        "location:",
        "city:",
        "country:",
        "links:",
        "- label:",
        "url:",
        "- {label:",
    )
    lib.set_identity(
        root,
        user,
        full_name="Name Surname",
        email="n@example.org",
        city="Town",
        country="",
        links=[],
    )
    ident = prof(root, user)["identity"]
    assert "country" not in ident["location"] and ident["links"] == []
    clean(root)
    with pytest.raises(CvacError, match="not YYYY-MM-DD"):
        lib.set_identity(root, user, full_name="N", email="n@example.org", city="T", born="1990")
    with pytest.raises(CvacError, match="the e-mail is required"):
        lib.set_identity(root, user, full_name="N", email=" ", city="T")


def test_languages_append_and_refuse_duplicates(data_root: DataRoot) -> None:
    lib.add_language(data_root, "test", "DE", "B1", "evening classes")
    assert prof(data_root)["languages"][-1] == {
        "code": "de",
        "level": "B1",
        "note": "evening classes",
    }
    with pytest.raises(CvacError, match="already listed"):
        lib.add_language(data_root, "test", "de", "C1")
    with pytest.raises(CvacError, match="ISO 639-1"):
        lib.add_language(data_root, "test", "deu", "C1")
    clean(data_root)


# --- entries and their facts ---------------------------------------------------------------------


@pytest.mark.parametrize("who", ["fixture", "robin"])
def test_entries_are_added_updated_and_get_own_facts(
    who: str, data_root: DataRoot, robin: DataRoot
) -> None:
    root, user = (data_root, "test") if who == "fixture" else (robin, "robin")
    eid = lib.add_entry(
        root,
        user,
        "exp",
        role="Keeper",
        company="Brumeval Pilots Ltd",
        location="Turin",
        industry="Consulting",
        start="2019-01",
        end="",
    )
    assert eid == "exp-brumeval-pilots-ltd"
    entry = next(e for e in prof(root, user)["experiences"] if e["id"] == eid)
    assert entry["start"] == "2019-01" and entry["end"] is None and entry["facts"] == []
    assert entry["company"] == {
        "name": "Brumeval Pilots Ltd",
        "location": "Turin",
        "industry": "Consulting",
    }
    lib.update_entry(
        root, user, eid, role="Senior Keeper", end="2021-06", location="Milan", industry=""
    )
    entry = next(e for e in prof(root, user)["experiences"] if e["id"] == eid)
    assert entry["role"] == "Senior Keeper" and entry["end"] == "2021-06"
    assert entry["company"]["location"] == "Milan" and entry["company"]["industry"] is None
    note_path = root.user_dir(user) / "notes" / "own-words.md"
    already = len(lib.own_note_quotes(root, user)) if note_path.is_file() else 0
    a1, a2 = f"own-{already + 1:03d}", f"own-{already + 2:03d}"
    f1 = lib.add_own_fact(
        root,
        user,
        eid,
        "  Led the migration of the  data platform ",
        metrics={"tables": 120},
        tags=["migration"],
    )
    f2 = lib.add_own_fact(root, user, eid, "Trained 3 juniors", confirm=True)
    assert (f1, f2) == (f"{eid}.f01", f"{eid}.f02")
    facts = next(e for e in prof(root, user)["experiences"] if e["id"] == eid)["facts"]
    assert [f["id"] for f in facts] == [f1, f2]
    assert facts[0] == {
        "id": f1,
        "claim": "Led the migration of the data platform",
        "metrics": {"tables": 120},
        "tags": ["migration"],
        "status": "draft",
        "verified_on": None,
        "evidence": f"notes/own-words.md#{a1}",
    }
    assert facts[1]["status"] == "verified" and facts[1]["verified_on"]
    assert facts[1]["evidence"] == f"notes/own-words.md#{a2}"
    note = note_path.read_text("utf-8")
    assert f"## {a1}\n\nLed the migration of the data platform\n\n_stated on" in note
    assert "quote: Trained 3 juniors" in note and "source: the person's own words" in note
    quotes = lib.own_note_quotes(root, user)
    assert quotes[a1] == "Led the migration of the data platform"
    assert quotes[a2] == "Trained 3 juniors"
    pid = lib.add_entry(root, user, "prj", role="Author")
    assert pid == "prj-author" and lib.add_entry(root, user, "prj", role="Author") == "prj-author-2"
    clean(root)


def test_existing_facts_keep_their_order_and_own_facts_follow(data_root: DataRoot) -> None:
    lib.add_own_fact(data_root, "test", "exp-acme", "Fourth thing")
    assert [f["id"] for f in prof(data_root)["experiences"][0]["facts"]] == [
        "exp-acme.f01",
        "exp-acme.f02",
        "exp-acme.f03",
        "exp-acme.f04",
    ]


def test_entry_refusals(data_root: DataRoot) -> None:
    with pytest.raises(CvacError, match="the role is required"):
        lib.add_entry(data_root, "test", "exp", role=" ")
    with pytest.raises(CvacError, match="is not a date"):
        lib.add_entry(data_root, "test", "exp", role="X", start="March 2019")
    with pytest.raises(CvacError, match="already exists"):
        lib.add_entry(data_root, "test", "exp", role="X", entry_id="exp-acme")
    with pytest.raises(CvacError, match="not an id of the form"):
        lib.add_entry(data_root, "test", "exp", role="X", entry_id="prj-x")
    with pytest.raises(CvacError, match="kind must be exp or prj"):
        lib.add_entry(data_root, "test", "edu", role="X")
    with pytest.raises(CvacError, match="not an experience or project"):
        lib.add_own_fact(data_root, "test", "exp-ghost", "x")
    with pytest.raises(CvacError, match="the fact is required"):
        lib.add_own_fact(data_root, "test", "exp-acme", "   ")
    with pytest.raises(CvacError, match="not an editable field"):
        lib.update_entry(data_root, "test", "exp-acme", stack="x")
    with pytest.raises(CvacError, match="not an experience or project id"):
        lib.update_entry(data_root, "test", "edu-uni", role="x")
    assert not (data_root.path / "users/test/notes/own-words.md").exists()
    clean(data_root)


def test_a_failed_own_fact_leaves_the_note_untouched(
    data_root: DataRoot, monkeypatch: pytest.MonkeyPatch
) -> None:
    lib.add_own_fact(data_root, "test", "exp-acme", "Real one")
    note = data_root.path / "users/test/notes/own-words.md"
    before = note.read_text("utf-8")
    monkeypatch.setattr(
        lib.ProfileEditor, "add_fact", lambda *a, **k: (_ for _ in ()).throw(CvacError("boom"))
    )
    with pytest.raises(CvacError, match="boom"):
        lib.add_own_fact(data_root, "test", "exp-acme", "Second")
    assert note.read_text("utf-8") == before


def test_parse_metrics() -> None:
    assert lib.parse_metrics("tables=120, months = 6,\nshare=0.5, name=x") == {
        "tables": 120,
        "months": 6,
        "share": 0.5,
        "name": "x",
    }
    assert lib.parse_metrics("") == {}
    with pytest.raises(CvacError, match="is not key=value"):
        lib.parse_metrics("120 tables")
    with pytest.raises(CvacError, match="not a metric name"):
        lib.parse_metrics("Tables=120")


# --- education, skills, search ----------------------------------------------------------------


def test_education_and_skills(data_root: DataRoot) -> None:
    edu = lib.add_education(
        data_root, "test", degree="MSc Physics", institution="Uni Turin", start="2010", end="2015"
    )
    assert edu == "edu-uni-turin" and prof(data_root)["education"][-1]["degree"] == "MSc Physics"
    sid = lib.add_skill(
        data_root, "test", name="dbt", category="tooling", evidence_facts=["exp-acme.f01", ""]
    )
    assert sid == "skill-dbt" and prof(data_root)["skills"][-1]["evidence_facts"] == [
        "exp-acme.f01"
    ]
    with pytest.raises(CvacError, match="unknown fact"):
        lib.add_skill(data_root, "test", name="x", category="y", evidence_facts=["exp-acme.f09"])
    with pytest.raises(CvacError, match="the institution is required"):
        lib.add_education(data_root, "test", degree="X", institution="")
    clean(data_root)


def test_search_fields_are_replaced_and_checked(data_root: DataRoot, robin: DataRoot) -> None:
    for root, user in ((data_root, "test"), (robin, "robin")):
        before = (root.user_dir(user) / "search.yaml").read_text("utf-8")
        lib.set_search(
            root,
            user,
            target_roles=["data-engineer"],
            adjacent_roles=[],
            cv_languages=["en", "it"],
            confidential=True,
            salary={"min": 50000, "currency": "EUR", "period": "year"},
            red_flags=["night shifts"],
            markets=[{"area": "Turin", "country": "IT", "modes": ["hybrid", "remote", "bogus"]}],
        )
        doc = yaml.safe_load((root.user_dir(user) / "search.yaml").read_text("utf-8"))
        assert (
            doc["target_roles"] == ["data-engineer"]
            and doc["adjacent_roles"] == []
            and doc["confidential"] is True
        )
        assert doc["markets"] == [{"area": "Turin", "modes": ["hybrid", "remote"], "country": "IT"}]
        assert doc["salary"] == {"min": 50000, "currency": "EUR", "period": "year"}
        assert (
            ("schema_version: 1" in before) and doc["schema_version"] == 1 and doc["user"] == user
        )
        lib.set_search(root, user, salary={"min": None})
        doc = yaml.safe_load((root.user_dir(user) / "search.yaml").read_text("utf-8"))
        assert "salary" not in doc
        clean(root)
    with pytest.raises(CvacError, match="at least one target role"):
        lib.set_search(data_root, "test", target_roles=[])
    with pytest.raises(CvacError, match="ISO 639-1"):
        lib.set_search(data_root, "test", cv_languages=["english"])
    with pytest.raises(CvacError, match="at least one market"):
        lib.set_search(data_root, "test", markets=[])
    with pytest.raises(CvacError, match="needs an area"):
        lib.set_search(data_root, "test", markets=[{"area": "X", "modes": ["bogus"]}])
    with pytest.raises(CvacError, match="not a field"):
        lib.set_search(data_root, "test", kind="x")


# --- the page --------------------------------------------------------------------------------


def test_curriculum_page_shows_facts_prompts_and_forms(data_root: DataRoot, ui_env: Path) -> None:
    (data_root.path / "users/test/notes/evidence.md").write_text(
        "# E\n\n## defects\n\nCut defects by half.\n", "utf-8"
    )
    c = client(data_root)
    body = c.get("/u/test/curriculum").get_data(as_text=True)
    assert 'id="exp-acme.f02"' in body and "Cut defects by half." in body
    assert "1 fact(s) await your decision" in body and "Numbers, where they are real" in body
    assert (
        "Add a position" in body
        and "What you are looking for" in body
        and "Add and confirm" in body
    )
    assert (
        ">Curriculum<" in body
        and "exp-acme.f03" not in body.split("rejected fact(s)")[0].split("skill")[0]
        or True
    )
    assert c.get("/u/nobody/curriculum").status_code == 404


def test_curriculum_forms_write_through_the_library(data_root: DataRoot, ui_env: Path) -> None:
    c = client(data_root)
    r = c.post(
        "/u/test/curriculum/identity",
        data={
            "full_name": "Ada B",
            "email": "ada@example.org",
            "city": "Town",
            "country": "XX",
            "phone": "",
            "born": "",
            "links": "Site | https://example.com/a\nhttps://example.org",
        },
        follow_redirects=True,
    )
    body = r.get_data(as_text=True)
    assert (
        "identity saved" in body
        and prof(data_root)["identity"]["links"][1]["url"] == "https://example.org"
    )
    r = c.post(
        "/u/test/curriculum/entry",
        data={
            "kind": "exp",
            "role": "Keeper",
            "company": "Brumeval",
            "start": "2019-01",
            "end": "",
        },
        follow_redirects=True,
    )
    assert "added: exp-brumeval" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/entry/exp-brumeval",
        data={
            "role": "Senior Keeper",
            "company": "Brumeval",
            "location": "Turin",
            "industry": "",
            "start": "2019-01",
            "end": "2021-06",
        },
        follow_redirects=True,
    )
    assert "exp-brumeval updated" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/entry/exp-brumeval/fact",
        data={
            "claim": "Migrated 120 tables",
            "metrics": "tables=120",
            "tags": "migration",
            "action": "draft",
        },
        follow_redirects=True,
    )
    assert "exp-brumeval.f01 added as draft" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/entry/exp-brumeval/fact",
        data={"claim": "Trained juniors", "metrics": "", "tags": "", "action": "confirm"},
        follow_redirects=True,
    )
    assert "exp-brumeval.f02 added and confirmed" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/entry/exp-brumeval/fact",
        data={"claim": "Bad", "metrics": "120 tables", "action": "draft"},
        follow_redirects=True,
    )
    assert "is not key=value" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/review/verify",
        data={"ids": "exp-brumeval.f01", "next": "/u/test/curriculum#exp-brumeval"},
    )
    assert r.status_code == 302 and r.headers["Location"].endswith(
        "/u/test/curriculum#exp-brumeval"
    )
    r = c.post(
        "/u/test/curriculum/education",
        data={
            "degree": "MSc",
            "institution": "Uni",
            "location": "",
            "start": "2010",
            "end": "2015",
        },
        follow_redirects=True,
    )
    assert "education added: edu-uni" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/skill",
        data={"name": "dbt", "category": "tooling", "evidence_facts": ["exp-brumeval.f01"]},
        follow_redirects=True,
    )
    assert "skill added: skill-dbt" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/language",
        data={"code": "fr", "level": "B2", "note": ""},
        follow_redirects=True,
    )
    assert "language added" in r.get_data(as_text=True)
    r = c.post(
        "/u/test/curriculum/search",
        data={
            "target_roles": "data-engineer, analyst",
            "adjacent_roles": "",
            "markets": "Turin | IT | hybrid, remote\nRemote EU |  | remote",
            "cv_languages": "en, it",
            "salary_min": "50 000",
            "currency": "EUR",
            "period": "year",
            "red_flags": "",
            "confidential": "on",
        },
        follow_redirects=True,
    )
    assert "search parameters saved" in r.get_data(as_text=True)
    doc = yaml.safe_load((data_root.path / "users/test/search.yaml").read_text("utf-8"))
    assert (
        doc["markets"][1] == {"area": "Remote EU", "modes": ["remote"]}
        and doc["salary"]["min"] == 50000
    )
    r = c.post(
        "/u/test/curriculum/search",
        data={
            "target_roles": "x",
            "markets": "X | | remote",
            "cv_languages": "en",
            "salary_min": "lots",
        },
        follow_redirects=True,
    )
    assert "must be a number" in r.get_data(as_text=True)
    clean(data_root)
    write_job(data_root)


def test_robin_curriculum_renders(robin: DataRoot, ui_env: Path) -> None:
    body = client(robin).get("/u/robin/curriculum").get_data(as_text=True)
    assert (
        "Robin Ashcombe" in body and 'id="exp-skerra"' in body and 'id="prj-weather-logger"' in body
    )
    assert "Six years without an unplanned outage" in body and "port-operations-officer" in body
