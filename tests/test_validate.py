"""Every anti-invention rule of the validator must fail when it should, and name the culprit."""

from __future__ import annotations

import copy
from pathlib import Path

from conftest import PROFILE, dump, spec_doc, write_spec

from cv_as_code.dataroot import DataRoot
from cv_as_code.validate import Report, discover_all, validate_files


def errors_of(root: DataRoot, path: Path) -> list[str]:
    return validate_files(root, [path]).errors


def profile_path(root: DataRoot) -> Path:
    return root.profile_path("test")


# --- happy path --------------------------------------------------------------------------


def test_clean_root_has_no_errors_and_one_warning(data_root: DataRoot) -> None:
    write_spec(data_root)
    rep: Report = validate_files(data_root, discover_all(data_root))
    assert rep.errors == []
    assert len(rep.warnings) == 1 and "skill-unproven" in rep.warnings[0]


def test_discover_all_lists_marker_user_files_and_package_labels(data_root: DataRoot) -> None:
    write_spec(data_root)
    names = [p.name for p in discover_all(data_root)]
    assert names.count("cvac.yaml") == 1
    assert "profile.yaml" in names and "search.yaml" in names and "cv-spec.yaml" in names
    assert {"labels.en.yaml", "labels.fr.yaml", "labels.it.yaml"} <= set(names)


# --- form --------------------------------------------------------------------------------


def test_missing_kind_is_an_error(data_root: DataRoot) -> None:
    p = dump(data_root.path / "users" / "test" / "matches" / "x.yaml", {"schema_version": 1})
    assert any("missing `kind` field" in e for e in errors_of(data_root, p))


def test_unknown_kind_is_an_error(data_root: DataRoot) -> None:
    p = dump(data_root.path / "users" / "test" / "matches" / "x.yaml", {"kind": "mystery"})
    assert any("no schema for kind `mystery`" in e for e in errors_of(data_root, p))


def test_yaml_parse_error_is_reported_not_raised(data_root: DataRoot) -> None:
    p = data_root.path / "users" / "test" / "matches" / "broken.yaml"
    p.parent.mkdir(parents=True)
    p.write_text("kind: [unclosed\n")
    assert any("YAML parse error" in e for e in errors_of(data_root, p))


def test_schema_violation_names_the_location(data_root: DataRoot) -> None:
    d = write_spec(data_root, max_pages=0)
    errs = errors_of(data_root, d / "cv-spec.yaml")
    assert any("schema: [max_pages]" in e for e in errs)


def test_missing_file_is_an_error(data_root: DataRoot) -> None:
    errs = errors_of(data_root, data_root.path / "users" / "test" / "nope.yaml")
    assert errs == ["users/test/nope.yaml: file not found"]


# --- profile -----------------------------------------------------------------------------


def test_fact_not_prefixed_by_parent_is_an_error(data_root: DataRoot) -> None:
    prof = copy.deepcopy(PROFILE)
    prof["experiences"][0]["facts"][0]["id"] = "exp-other.f01"
    prof["skills"][0]["evidence_facts"] = []
    dump(profile_path(data_root), prof)
    errs = errors_of(data_root, profile_path(data_root))
    assert any("`exp-other.f01` does not belong to its parent `exp-acme`" in e for e in errs)


def test_duplicate_id_is_an_error(data_root: DataRoot) -> None:
    prof = copy.deepcopy(PROFILE)
    prof["skills"].append(dict(prof["skills"][0]))
    dump(profile_path(data_root), prof)
    assert any(
        "duplicate id `skill-widgets`" in e for e in errors_of(data_root, profile_path(data_root))
    )


def test_skill_citing_unknown_fact_is_an_error(data_root: DataRoot) -> None:
    prof = copy.deepcopy(PROFILE)
    prof["skills"][0]["evidence_facts"] = ["exp-acme.f99"]
    dump(profile_path(data_root), prof)
    errs = errors_of(data_root, profile_path(data_root))
    assert any("skill `skill-widgets` cites unknown fact `exp-acme.f99`" in e for e in errs)


def test_missing_evidence_path_is_an_error(data_root: DataRoot) -> None:
    prof = copy.deepcopy(PROFILE)
    prof["experiences"][0]["facts"][0]["evidence"] = "notes/missing.md"
    dump(profile_path(data_root), prof)
    errs = errors_of(data_root, profile_path(data_root))
    assert any(
        "fact `exp-acme.f01` evidence path `notes/missing.md` does not exist" in e for e in errs
    )


def test_evidence_list_with_anchor_resolves(data_root: DataRoot) -> None:
    assert (
        errors_of(data_root, profile_path(data_root)) == []
    )  # f02 cites notes/evidence.md#defects


# --- cv-spec references and the gate ------------------------------------------------------


def test_unknown_source_fact_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, facts=("exp-acme.f99",))
    errs = errors_of(data_root, d / "cv-spec.yaml")
    assert any("summary cites `exp-acme.f99` which does not exist" in e for e in errs)


def test_approved_spec_citing_draft_fact_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved", facts=("exp-acme.f02",))
    errs = errors_of(data_root, d / "cv-spec.yaml")
    assert any(
        "status is `approved` but cites non-verified fact(s): exp-acme.f02" in e for e in errs
    )


def test_approved_spec_citing_rejected_fact_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved", facts=("exp-acme.f03",))
    errs = errors_of(data_root, d / "cv-spec.yaml")
    assert any("non-verified fact(s): exp-acme.f03" in e for e in errs)


def test_approved_spec_citing_only_verified_facts_passes(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved")
    assert errors_of(data_root, d / "cv-spec.yaml") == []


def test_draft_spec_may_cite_draft_facts(data_root: DataRoot) -> None:
    d = write_spec(data_root, facts=("exp-acme.f02",))
    assert errors_of(data_root, d / "cv-spec.yaml") == []


def test_approved_without_date_is_a_warning(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved", approved_on=None)
    rep = validate_files(data_root, [d / "cv-spec.yaml"])
    assert rep.errors == [] and any("approved_on is not set" in w for w in rep.warnings)


def test_unknown_experience_ref_is_an_error(data_root: DataRoot) -> None:
    doc = spec_doc()
    doc["experience"][0]["ref"] = "exp-ghost"
    d = data_root.path / "users" / "test" / "masters" / "x"
    dump(d / "cv-spec.yaml", doc)
    assert any(
        "experience[0] refs unknown entity `exp-ghost`" in e
        for e in errors_of(data_root, d / "cv-spec.yaml")
    )


def test_unknown_education_and_omitted_refs_are_errors(data_root: DataRoot) -> None:
    d = write_spec(
        data_root,
        education=[{"ref": "edu-ghost", "degree": "x"}],
        omitted=[{"ref": "exp-ghost", "reason": "y"}],
    )
    errs = errors_of(data_root, d / "cv-spec.yaml")
    assert any("education refs unknown entity `edu-ghost`" in e for e in errs)
    assert any("omitted refs unknown entity `exp-ghost`" in e for e in errs)


def test_missing_profile_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, user="nobody")
    assert any(
        "profile not found for user `nobody`" in e for e in errors_of(data_root, d / "cv-spec.yaml")
    )


def test_language_without_labels_file_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, language="zz")
    assert any(
        "no labels file for language `zz`" in e for e in errors_of(data_root, d / "cv-spec.yaml")
    )


def test_missing_template_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, template="nope")
    assert any("template `nope` not found" in e for e in errors_of(data_root, d / "cv-spec.yaml"))


def test_job_id_without_directory_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root, job_id="20260101-acme-widget")
    assert any(
        "has no jobs/20260101-acme-widget/ directory" in e
        for e in errors_of(data_root, d / "cv-spec.yaml")
    )
    (data_root.path / "jobs" / "20260101-acme-widget").mkdir()
    assert errors_of(data_root, d / "cv-spec.yaml") == []


# --- labels, search, data root ------------------------------------------------------------


def test_labels_missing_key_is_an_error(data_root: DataRoot) -> None:
    import yaml

    doc = yaml.safe_load(data_root.labels_path("en").read_text("utf-8"))
    del doc["present"]
    p = dump(data_root.path / "i18n" / "labels.en.yaml", doc)
    assert any("'present' is a required property" in e for e in errors_of(data_root, p))


def test_labels_language_must_match_file_name(data_root: DataRoot) -> None:
    import yaml

    doc = yaml.safe_load(data_root.labels_path("en").read_text("utf-8"))
    p = dump(data_root.path / "i18n" / "labels.xx.yaml", doc)
    assert any("language `en` does not match the file name" in e for e in errors_of(data_root, p))


def test_search_user_without_directory_is_an_error(data_root: DataRoot) -> None:
    p = data_root.path / "users" / "test" / "search.yaml"
    import yaml

    doc = yaml.safe_load(p.read_text("utf-8"))
    doc["user"] = "ghost"
    dump(p, doc)
    assert any("user `ghost` has no users/ghost/ directory" in e for e in errors_of(data_root, p))


def test_data_root_default_user_must_exist(data_root: DataRoot) -> None:
    p = data_root.path / "cvac.yaml"
    p.write_text("schema_version: 1\nkind: data-root\ndefault_user: ghost\n")
    assert any(
        "default_user `ghost` has no users/ghost/ directory" in e for e in errors_of(data_root, p)
    )
