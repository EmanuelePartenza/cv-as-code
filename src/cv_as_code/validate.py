"""Validate data files: JSON Schema form, referential integrity, the approval gate.

Three levels:
  1. Form  - YAML parses, `kind` is known, the document matches the schema for that kind
  2. Refs  - every ref / source_facts / evidence_facts points to an existing entity or
             fact in the owning user's profile; every evidence path exists on disk
  3. Gate  - a cv-spec with status: approved may only cite facts with status: verified
             (the mechanical core of the "never invent facts" rule, ADR-0001)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .dataroot import MARKER, DataRoot, package_dir
from .documents import has_front_matter, load_document
from .errors import CvacError


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


_schema_cache: dict[str, dict[str, Any] | None] = {}


def load_schema(root: DataRoot, kind: str) -> dict[str, Any] | None:
    if kind not in _schema_cache:
        path = root.schema_path(kind)
        _schema_cache[kind] = json.loads(path.read_text("utf-8")) if path.is_file() else None
    return _schema_cache[kind]


def _load(path: Path, where: str, rep: Report) -> Any:
    try:
        return load_document(path, where)
    except CvacError as e:
        rep.error(where, str(e).replace(f"{where}: ", "").replace(f"{where} ", ""))
        return None


def evidence_list(value: Any) -> list[str]:
    """A fact's evidence as a list of path strings (string, list or null accepted)."""
    if not value:
        return []
    return [value] if isinstance(value, str) else [str(v) for v in value]


def citable_ids(profile: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    """Return (entity_ids, fact_status): everything a cv-spec is allowed to cite."""
    entity_ids: set[str] = set()
    fact_status: dict[str, str] = {}
    for section in ("experiences", "projects"):
        for exp in profile.get(section) or []:
            entity_ids.add(exp.get("id"))
            for fact in exp.get("facts") or []:
                fact_status[fact.get("id")] = fact.get("status")
    for edu in profile.get("education") or []:
        entity_ids.add(edu.get("id"))
    for skill in profile.get("skills") or []:
        entity_ids.add(skill.get("id"))
    entity_ids.discard(None)
    return entity_ids, fact_status


def validate_form(root: DataRoot, doc: dict[str, Any], where: str, rep: Report) -> bool:
    kind = doc.get("kind")
    if not kind:
        rep.error(where, "missing `kind` field")
        return False
    schema = load_schema(root, kind)
    if schema is None:
        rep.error(where, f"no schema for kind `{kind}` (expected schemas/{kind}.schema.json)")
        return False
    ok = True
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        rep.error(where, f"schema: [{loc}] {err.message}")
        ok = False
    return ok


def check_profile(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    entity_ids, fact_status = citable_ids(doc)
    user_dir = path.parent

    seen: set[str] = set()
    all_ids: list[str] = list(fact_status)
    for section in ("experiences", "projects"):
        all_ids += [e.get("id") for e in doc.get(section) or []]
    all_ids += [e.get("id") for e in doc.get("education") or []]
    all_ids += [s.get("id") for s in doc.get("skills") or []]
    for i in all_ids:
        if i in seen:
            rep.error(where, f"duplicate id `{i}`")
        seen.add(i)

    for section in ("experiences", "projects"):
        for exp in doc.get(section) or []:
            for fact in exp.get("facts") or []:
                fid = fact.get("id", "")
                if not fid.startswith(f"{exp.get('id')}."):
                    rep.error(
                        where, f"fact `{fid}` does not belong to its parent `{exp.get('id')}`"
                    )
                for ev in evidence_list(fact.get("evidence")):
                    target = user_dir / ev.split("#", 1)[0]
                    if not target.exists():
                        rep.error(where, f"fact `{fid}` evidence path `{ev}` does not exist")

    unevidenced = []
    for skill in doc.get("skills") or []:
        evidence = skill.get("evidence_facts") or []
        for fid in evidence:
            if fid not in fact_status:
                rep.error(where, f"skill `{skill.get('id')}` cites unknown fact `{fid}`")
        if not evidence:
            unevidenced.append(skill.get("id"))
    if unevidenced:
        rep.warn(
            where,
            f"{len(unevidenced)} skill(s) without evidence_facts: {', '.join(unevidenced)}",
        )


def check_cvspec(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    user = doc.get("user")
    profile_path = root.profile_path(str(user))
    if not profile_path.exists():
        rep.error(where, f"profile not found for user `{user}` ({root.rel(profile_path)})")
        return
    profile = _load(profile_path, root.rel(profile_path), rep)
    if profile is None:
        return
    entity_ids, fact_status = citable_ids(profile)
    citable = entity_ids | set(fact_status)
    cited_facts: set[str] = set()

    def check_refs(refs: Any, at: str) -> None:
        for r in refs or []:
            if r not in citable:
                rep.error(where, f"{at} cites `{r}` which does not exist in the profile")
            elif r in fact_status:
                cited_facts.add(r)

    if isinstance(doc.get("summary"), dict):
        check_refs(doc["summary"].get("source_facts"), "summary")
    for i, exp in enumerate(doc.get("experience") or []):
        if exp.get("ref") not in entity_ids:
            rep.error(where, f"experience[{i}] refs unknown entity `{exp.get('ref')}`")
        for j, bullet in enumerate(exp.get("bullets") or []):
            check_refs(bullet.get("source_facts"), f"experience[{i}].bullets[{j}]")
    for ed in doc.get("education") or []:
        if ed.get("ref") not in entity_ids:
            rep.error(where, f"education refs unknown entity `{ed.get('ref')}`")
    for om in doc.get("omitted") or []:
        if om.get("ref") not in citable:
            rep.error(where, f"omitted refs unknown entity `{om.get('ref')}`")

    template = doc.get("template")
    if template and root.template_dir(template) is None:
        rep.error(where, f"template `{template}` not found (data root templates/ or the package)")

    language = doc.get("language")
    if language and root.labels_path(language) is None:
        rep.error(
            where,
            f"no labels file for language `{language}` (add i18n/labels.{language}.yaml "
            "to the data root)",
        )

    job_id = doc.get("job_id")
    if job_id and not root.job_dir(job_id).is_dir():
        rep.error(where, f"job_id `{job_id}` has no jobs/{job_id}/ directory")

    if doc.get("status") == "approved":
        unverified = sorted(f for f in cited_facts if fact_status.get(f) != "verified")
        if unverified:
            rep.error(
                where,
                f"status is `approved` but cites non-verified fact(s): {', '.join(unverified)}",
            )
        if not doc.get("approved_on"):
            rep.warn(where, "status is `approved` but approved_on is not set")


def check_search(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    user = doc.get("user")
    if user and not root.user_dir(str(user)).is_dir():
        rep.error(where, f"user `{user}` has no users/{user}/ directory")


def check_labels(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    expected = path.name.removeprefix("labels.").removesuffix(".yaml")
    if doc.get("language") != expected:
        rep.error(where, f"language `{doc.get('language')}` does not match the file name")


def check_dataroot(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    user = doc.get("default_user")
    if user and not (path.parent / "users" / user).is_dir():
        rep.error(where, f"default_user `{user}` has no users/{user}/ directory")


def check_job(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    if doc.get("id") != path.parent.name:
        rep.error(where, f"id `{doc.get('id')}` does not match the directory `{path.parent.name}`")
    if not (path.parent / "raw.txt").is_file():
        rep.error(where, "raw.txt is missing next to job.yaml (the verbatim posting)")


def _cited_facts(
    root: DataRoot, doc: dict, where: str, rep: Report, refs: Any, at: str
) -> tuple[list[str], dict[str, str]] | None:
    """Check that every ref in `refs` is a fact of the document's user; return (cited, statuses)."""
    user = doc.get("user")
    profile_path = root.profile_path(str(user))
    if not profile_path.exists():
        rep.error(where, f"profile not found for user `{user}` ({root.rel(profile_path)})")
        return None
    profile = _load(profile_path, root.rel(profile_path), rep)
    if profile is None:
        return None
    _, fact_status = citable_ids(profile)
    cited = []
    for r in refs or []:
        if r not in fact_status:
            rep.error(where, f"{at} cites unknown fact `{r}`")
        else:
            cited.append(r)
    return cited, fact_status


def check_match(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    job_id = doc.get("job_id")
    if job_id != path.stem:
        rep.error(where, f"job_id `{job_id}` does not match the file name `{path.stem}`")
    if job_id and not root.job_dir(str(job_id)).is_dir():
        rep.error(where, f"job_id `{job_id}` has no jobs/{job_id}/ directory")
    for i, strength in enumerate(doc.get("strengths") or []):
        if (
            _cited_facts(root, doc, where, rep, strength.get("source_facts"), f"strengths[{i}]")
            is None
        ):
            return


def check_letter(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    job_id = doc.get("job_id")
    if job_id and path.parent.name != job_id:
        rep.error(
            where,
            f"job_id `{job_id}` does not match the application directory `{path.parent.name}`",
        )
    if job_id and not root.job_dir(str(job_id)).is_dir():
        rep.error(where, f"job_id `{job_id}` has no jobs/{job_id}/ directory")
    language = doc.get("language")
    if language and root.labels_path(language) is None:
        rep.error(where, f"no labels file for language `{language}`")
    template = doc.get("template")
    if template and root.template_dir(template) is None:
        rep.error(where, f"template `{template}` not found (data root templates/ or the package)")
    result = _cited_facts(root, doc, where, rep, doc.get("source_facts"), "source_facts")
    if result is None:
        return
    cited, fact_status = result
    if doc.get("status") == "approved":
        unverified = sorted(f for f in cited if fact_status.get(f) != "verified")
        if unverified:
            rep.error(
                where,
                f"status is `approved` but cites non-verified fact(s): {', '.join(unverified)}",
            )
        if not doc.get("approved_on"):
            rep.warn(where, "status is `approved` but approved_on is not set")


def check_evidence(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    user_dir = path.parent.parent
    source = str(doc.get("source") or "")
    if "/" in source and "://" not in source and not (user_dir / source).exists():
        rep.error(where, f"source `{source}` does not exist under {root.rel(user_dir)}")
    new_parents = {np.get("id") for np in doc.get("new_parents") or []}
    profile_path = root.profile_path(str(doc.get("user")))
    known: set[str] = set()
    if profile_path.exists():
        profile = _load(profile_path, root.rel(profile_path), rep)
        if profile is not None:
            known, _ = citable_ids(profile)
    for i, fact in enumerate(doc.get("facts") or []):
        parent = fact.get("parent")
        if parent not in known and parent not in new_parents:
            rep.error(
                where, f"facts[{i}] parent `{parent}` is neither in the profile nor in new_parents"
            )


def check_questionnaire(root: DataRoot, doc: dict, path: Path, where: str, rep: Report) -> None:
    user = doc.get("user")
    if user and not root.user_dir(str(user)).is_dir():
        rep.error(where, f"user `{user}` has no users/{user}/ directory")


CHECKS = {
    "profile": check_profile,
    "cv-spec": check_cvspec,
    "search": check_search,
    "labels": check_labels,
    "data-root": check_dataroot,
    "job": check_job,
    "match": check_match,
    "cover-letter": check_letter,
    "evidence": check_evidence,
    "questionnaire": check_questionnaire,
}


def validate_file(root: DataRoot, path: Path, rep: Report) -> None:
    where = root.rel(path)
    if not path.exists():
        rep.error(where, "file not found")
        return
    if path.suffix == ".md" and not has_front_matter(path.read_text("utf-8")):
        # Free-form notes are legitimate; a letter without a frontmatter is not.
        if path.name == "letter.md":
            rep.error(where, "has no YAML frontmatter")
        return
    doc = _load(path, where, rep)
    if doc is None:
        return
    if not isinstance(doc, dict):
        rep.error(where, "top-level document is not a mapping")
        return
    if path.suffix == ".md" and "kind" not in doc:
        # Notes and questionnaires may be free-form documents; a letter may not.
        if path.name == "letter.md":
            rep.warn(
                where,
                "no `kind` in the frontmatter: not validated "
                "(add `kind: cover-letter` to enable the gate)",
            )
        return
    if validate_form(root, doc, where, rep):
        check = CHECKS.get(doc.get("kind"))
        if check:
            check(root, doc, path, where, rep)


def discover_all(root: DataRoot) -> list[Path]:
    """Every data file the framework knows how to validate, in this data root and the package."""
    patterns = [
        "users/*/profile.yaml",
        "users/*/search.yaml",
        "users/*/masters/*/cv-spec.yaml",
        "users/*/applications/*/cv-spec.yaml",
        "users/*/applications/*/letter.md",
        "users/*/notes/*.md",
        "users/*/interviews/*.md",
        "users/*/matches/*.yaml",
        "jobs/*/job.yaml",
        "i18n/labels.*.yaml",
    ]
    files: list[Path] = []
    marker = root.path / MARKER
    if marker.is_file():
        files.append(marker)
    for pattern in patterns:
        files.extend(sorted(root.path.glob(pattern)))
    files.extend(sorted((package_dir() / "i18n").glob("labels.*.yaml")))
    return files


def validate_files(root: DataRoot, files: list[Path]) -> Report:
    rep = Report()
    for path in files:
        validate_file(root, Path(path), rep)
    return rep
