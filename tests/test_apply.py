"""Stage 04 as code: additive, layout-preserving, refused through the validator."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from conftest import dump

from cv_as_code.apply import apply_note
from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.validate import discover_all, validate_files

NOTE = """---
schema_version: 1
kind: evidence
user: test
source: inbox/old-cv.md
extracted_on: "2026-01-05"
status: proposed
new_parents: {parents}
facts:
{facts}
---

# Old CV — extraction

## releases
twelve releases in 2021
{tail}
"""

FACT = """  - parent: {parent}
    claim: {claim}
    metrics: {metrics}
    tags: {tags}
    quote: "q"
    anchor: {anchor}
"""


TAGS = '[gadgets, "it\'s"]'


def fact(parent: str, claim: str, anchor: str, metrics: str = "{}", tags: str = "[]") -> str:
    return FACT.format(parent=parent, claim=claim, anchor=anchor, metrics=metrics, tags=tags)


def write_note(
    root: DataRoot, facts: str, parents: str = "[]", tail: str = "", name: str = "old-cv"
) -> Path:
    inbox = root.path / "users" / "test" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "old-cv.md").write_text("an old cv\n", "utf-8")
    path = root.path / "users" / "test" / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(NOTE.format(parents=parents, facts=facts, tail=tail), "utf-8")
    return path


def profile_of(root: DataRoot) -> dict:
    return yaml.safe_load(root.profile_path("test").read_text("utf-8"))


def old_lines_survive(before: str, after: str) -> bool:
    """Every line of the old text appears, in order, in the new text."""
    it = iter(after.splitlines())
    return all(any(line == new for new in it) for line in before.splitlines())


def test_facts_are_appended_as_draft_with_continued_ids(data_root: DataRoot) -> None:
    note = write_note(
        data_root,
        fact(
            "exp-acme",
            "Shipped 12 widget releases in 2021",
            "releases",
            "{releases: 12}",
            "[delivery]",
        )
        + fact("prj-tool", "Counted 7 widgets a day", "seven"),
    )
    before = data_root.profile_path("test").read_text("utf-8")
    result = apply_note(data_root, "test", "old-cv")
    after = data_root.profile_path("test").read_text("utf-8")
    assert result.added == ["exp-acme.f04", "prj-tool.f02"] and result.skipped == []
    assert old_lines_survive(before, after)
    prof = profile_of(data_root)
    new = {f["id"]: f for e in prof["experiences"] + prof["projects"] for f in e["facts"]}
    assert new["exp-acme.f04"] == {
        "id": "exp-acme.f04",
        "claim": "Shipped 12 widget releases in 2021",
        "metrics": {"releases": 12},
        "tags": ["delivery"],
        "status": "draft",
        "verified_on": None,
        "evidence": "notes/old-cv.md#releases",
    }
    assert new["prj-tool.f02"]["status"] == "draft" and new["prj-tool.f02"]["metrics"] == {}
    assert "status: applied" in note.read_text("utf-8")
    assert validate_files(data_root, discover_all(data_root)).errors == []
    assert "every added fact is draft until you verify it" in result.lines


def test_new_parents_are_appended_and_get_their_facts(data_root: DataRoot) -> None:
    parents = """
  - id: prj-gadget
    role: Maker
    company: {name: null}
    start: "2023-05"
    end: null"""
    write_note(
        data_root,
        fact(
            "prj-gadget",
            '"Made a gadget that counts widgets: 3 users"',
            "gadget",
            "{users: 3}",
            TAGS,
        ),
        parents=parents,
    )
    result = apply_note(data_root, "test", "old-cv")
    assert result.new_parents == ["prj-gadget"] and result.added == ["prj-gadget.f01"]
    prof = profile_of(data_root)
    gadget = prof["projects"][-1]
    assert gadget["id"] == "prj-gadget" and gadget["start"] == "2023-05" and gadget["end"] is None
    assert gadget["company"] == {"name": None, "location": None, "industry": None}
    assert gadget["facts"][0]["claim"] == "Made a gadget that counts widgets: 3 users"
    assert gadget["facts"][0]["tags"] == ["gadgets", "it's"]
    assert validate_files(data_root, discover_all(data_root)).errors == []


def test_duplicates_are_skipped_and_an_all_duplicate_note_is_refused(data_root: DataRoot) -> None:
    write_note(data_root, fact("exp-acme", "Built the widget pipeline", "pipeline"))
    with pytest.raises(CvacError, match="nothing to apply"):
        apply_note(data_root, "test", "old-cv")
    write_note(
        data_root,
        fact("exp-acme", "built the  widget pipeline", "pipeline")
        + fact("exp-acme", "New thing", "new"),
    )
    result = apply_note(data_root, "test", "old-cv")
    assert result.added == ["exp-acme.f04"] and len(result.skipped) == 1
    write_note(data_root, fact("exp-acme", "Another", "new"), name="second")
    result = apply_note(data_root, "test", "second")
    assert result.added == ["exp-acme.f05"]


def test_empty_lists_of_a_scaffolded_profile_are_filled(tmp_path: Path) -> None:
    from cv_as_code.scaffold import init_data_root, init_user

    root = DataRoot.load(init_data_root(tmp_path / "dr"))
    init_user(root, "test", "Test", "t@example.org", "X", target_roles=["x"])
    parents = """
  - id: exp-first
    role: Keeper
    company: {name: Lights Board, location: Skerra, industry: null}
    start: "2018-04"
    end: null"""
    write_note(root, fact("exp-first", "Kept the light", "light"), parents=parents)
    result = apply_note(root, "test", "old-cv")
    assert result.added == ["exp-first.f01"]
    prof = profile_of(root)
    assert (
        prof["experiences"][0]["id"] == "exp-first"
        and prof["experiences"][0]["facts"][0]["status"] == "draft"
    )
    assert prof["projects"] == [] and validate_files(root, discover_all(root)).errors == []


def test_a_parent_without_facts_key_or_with_empty_facts(data_root: DataRoot) -> None:
    profile = data_root.profile_path("test")
    prof = yaml.safe_load(profile.read_text("utf-8"))
    prof["projects"][0]["facts"] = []
    prof["experiences"].append(
        {"id": "exp-bare", "role": "Bare", "company": {"name": "B"}, "start": "2010", "end": "2011"}
    )
    dump(profile, prof)
    write_note(
        data_root, fact("prj-tool", "Counted", "c") + fact("exp-bare", "Did bare things", "b")
    )
    result = apply_note(data_root, "test", "old-cv")
    assert result.added == ["prj-tool.f01", "exp-bare.f01"]
    prof = profile_of(data_root)
    assert prof["projects"][0]["facts"][0]["id"] == "prj-tool.f01"
    assert prof["experiences"][-1]["facts"][0]["evidence"] == "notes/old-cv.md#b"


def test_hand_indented_layout_is_kept(data_root: DataRoot) -> None:
    profile = data_root.profile_path("test")
    text = """schema_version: 1
kind: profile
user: test
pivot_language: en
identity:
  full_name: Test User
  location: {city: Testville, country: XX}
  email: test.user@example.com
languages:
  - {code: en, level: native}
experiences:
  - id: exp-acme
    role: Widget Engineer
    company: {name: Acme Widgets}
    start: "2020-03"
    end: null
    facts:
      - id: exp-acme.f01
        claim: Built the widget pipeline
        status: verified
        verified_on: "2026-01-01"
        evidence: notes/evidence.md

projects: []
education: []
skills: []
"""
    profile.write_text(text, "utf-8")
    write_note(data_root, fact("exp-acme", "Shipped releases", "r"))
    apply_note(data_root, "test", "old-cv")
    after = profile.read_text("utf-8")
    assert old_lines_survive(text, after)
    assert "      - id: exp-acme.f02\n        claim: Shipped releases\n" in after
    assert "\nprojects: []\n" in after


def test_refusals_leave_the_profile_untouched(data_root: DataRoot) -> None:
    profile = data_root.profile_path("test")
    before = profile.read_text("utf-8")
    with pytest.raises(CvacError, match="missing users/test/notes/ghost.md"):
        apply_note(data_root, "test", "ghost")
    write_note(data_root, fact("exp-nope", "x", "a"))
    with pytest.raises(CvacError, match="does not validate"):
        apply_note(data_root, "test", "old-cv")
    write_note(data_root, fact("exp-acme", "x", "a"))
    note = data_root.path / "users" / "test" / "notes" / "old-cv.md"
    note.write_text(note.read_text("utf-8").replace("status: proposed", "status: applied"), "utf-8")
    with pytest.raises(CvacError, match="already applied"):
        apply_note(data_root, "test", "old-cv")
    parents = """
  - id: exp-acme
    role: Dup
    company: {name: null}
    start: null
    end: null"""
    write_note(data_root, fact("exp-acme", "x", "a"), parents=parents)
    with pytest.raises(CvacError, match="new parent `exp-acme` already exists"):
        apply_note(data_root, "test", "old-cv")
    assert profile.read_text("utf-8") == before


def test_a_result_that_would_not_validate_is_not_written(data_root: DataRoot) -> None:
    profile = data_root.profile_path("test")
    before = profile.read_text("utf-8")
    write_note(data_root, fact("exp-acme", '"   "', "blank"))
    with pytest.raises(CvacError, match="would not validate; nothing written"):
        apply_note(data_root, "test", "old-cv")
    assert profile.read_text("utf-8") == before
    note = data_root.path / "users" / "test" / "notes" / "old-cv.md"
    assert "status: proposed" in note.read_text("utf-8")


def test_search_parameters_are_pointed_out_not_written(data_root: DataRoot) -> None:
    write_note(
        data_root,
        fact("exp-acme", "Something new", "n"),
        tail="\n## Search parameters (section G)\n\nremote only\n",
    )
    result = apply_note(data_root, "test", "old-cv")
    assert any("search parameters" in line and "search.yaml" in line for line in result.lines)
    search = yaml.safe_load((data_root.path / "users" / "test" / "search.yaml").read_text("utf-8"))
    assert "remote only" not in str(search)
