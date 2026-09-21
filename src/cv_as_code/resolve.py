"""Resolve a cv-spec into cv.resolved.json, the render input.

Joins three sources and fully denormalises them so the Typst template carries no
refs and no language strings:
  - the cv-spec        (selection + reworded bullets, in the target language)
  - the user's profile (facts, organisations, dates, education, languages)
  - labels.<lang>.yaml (section headings, "present", date format, names of languages)

Anti-invention gates (the mechanical core of "never invent facts", ADR-0001):
  - always: every cited ref (source_facts, education, omitted) must exist in the
    profile; a broken ref fails the resolve
  - mode final: the spec must be `approved` AND every cited fact `verified`
  - mode draft: anything goes; meta.draft is stamped so the template watermarks

The output is validated against cv-resolved.schema.json before it is written.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .dataroot import DataRoot, load_yaml
from .errors import CvacError, RenderError

FACT_RE = re.compile(r"^(exp|prj)-[a-z0-9-]+\.f\d{2}$")
SECTIONS = ("summary", "experience", "projects", "skills", "education", "languages")
DATE_FORMATS = {"MM/YYYY": "{m}/{y}", "YYYY-MM": "{y}-{m}", "MM.YYYY": "{m}.{y}"}


@dataclass
class ResolveResult:
    spec_dir: Path
    out_json: Path
    draft: bool
    unverified: list[str]


def fmt_date(d: Any, date_format: str = "MM/YYYY") -> str | None:
    """'2024-07' -> '07/2024' (per date_format); '2024' -> '2024'; day precision is dropped."""
    if not d:
        return None
    parts = str(d).split("-")
    if len(parts) == 1:
        return parts[0]
    return DATE_FORMATS[date_format].format(y=parts[0], m=parts[1])


def fmt_range(start: Any, end: Any, present: str, date_format: str) -> str:
    s, e = fmt_date(start, date_format), fmt_date(end, date_format)
    if s is None and e is None:
        return ""
    if end is None:  # ongoing
        e = present
    if s is None:
        return str(e)
    if s == e:
        return s
    return f"{s} – {e}"  # en dash


def load_labels(root: DataRoot, lang: str) -> dict[str, Any]:
    path = root.labels_path(lang)
    if path is None:
        raise CvacError(
            f"no labels file for language `{lang}` (add i18n/labels.{lang}.yaml to the data root)"
        )
    labels = load_yaml(path)
    if not isinstance(labels, dict) or labels.get("kind") != "labels":
        raise CvacError(f"{root.rel(path)} is not a labels document (run `cvac validate` on it)")
    return labels


def resolve(root: DataRoot, spec_arg: str | Path, mode: str) -> ResolveResult:
    spec_dir = root.resolve_dir(spec_arg)
    spec_path = spec_dir / "cv-spec.yaml"
    spec = load_yaml(spec_path)
    if not isinstance(spec, dict) or spec.get("kind") != "cv-spec":
        raise CvacError(f"{root.rel(spec_path)} is not a cv-spec document")

    if mode == "final" and spec.get("status") != "approved":
        raise CvacError(
            f"--mode final requires status: approved (got {spec.get('status')!r}); "
            "the human gate has not signed off this spec"
        )

    profile = load_yaml(root.profile_path(str(spec["user"])))
    labels = load_labels(root, spec["language"])
    date_format = labels.get("date_format", "MM/YYYY")
    present = labels["present"]
    lsec = labels["sections"]

    exp_by_id = {e["id"]: e for e in profile.get("experiences") or []}
    prj_by_id = {p["id"]: p for p in profile.get("projects") or []}
    edu_by_id = {e["id"]: e for e in profile.get("education") or []}
    skill_by_id = {s["id"]: s for s in profile.get("skills") or []}
    fact_status: dict[str, str] = {}
    for section in ("experiences", "projects"):
        for e in profile.get(section) or []:
            for fact in e.get("facts") or []:
                fact_status[fact["id"]] = fact.get("status")
    entity_ids = set(exp_by_id) | set(prj_by_id) | set(edu_by_id) | set(skill_by_id)

    errors: list[str] = []
    unverified: list[str] = []

    def cite(ref: str, where: str) -> None:
        """Register a cited ref; record broken refs and (fact) verification."""
        if FACT_RE.match(ref):
            if ref not in fact_status:
                errors.append(f"{where} cites unknown fact `{ref}`")
            elif fact_status[ref] != "verified":
                unverified.append(f"{ref} ({where}, status={fact_status[ref]})")
        elif ref not in entity_ids:
            errors.append(f"{where} cites unknown entity `{ref}`")

    summary = None
    if isinstance(spec.get("summary"), dict):
        summary = spec["summary"]["text"]
        for r in spec["summary"].get("source_facts") or []:
            cite(r, "summary")

    # experience and projects share the spec array; the profile decides the bucket
    resolved_exp: list[dict[str, Any]] = []
    resolved_prj: list[dict[str, Any]] = []
    for i, item in enumerate(spec.get("experience") or []):
        ref = item["ref"]
        if ref in exp_by_id:
            entity, bucket = exp_by_id[ref], resolved_exp
        elif ref in prj_by_id:
            entity, bucket = prj_by_id[ref], resolved_prj
        else:
            errors.append(f"experience[{i}] refs unknown entity `{ref}`")
            continue
        bullets = []
        for j, b in enumerate(item["bullets"]):
            bullets.append(b["text"])
            for r in b.get("source_facts") or []:
                cite(r, f"{ref} bullet[{j}]")
        org = item.get("subtitle")
        if org is None:
            company = (entity.get("company") or {}).get("name")
            eloc = (entity.get("company") or {}).get("location")
            org = f"{company}, {eloc}" if company and eloc else (company or eloc)
        bucket.append(
            {
                "role": item.get("title") or entity.get("role", ""),
                "org": org,
                "dates": fmt_range(entity.get("start"), entity.get("end"), present, date_format),
                "bullets": bullets,
            }
        )

    layout = spec.get("skills_layout") or {}
    groups = [{"label": g["label"], "items": list(g["items"])} for g in layout.get("groups") or []]
    emphasis = list(layout.get("emphasis") or [])

    education = []
    for ed in spec.get("education") or []:
        ref = ed["ref"]
        if ref not in edu_by_id:
            errors.append(f"education refs unknown `{ref}`")
            continue
        e = edu_by_id[ref]
        education.append(
            {
                "degree": ed["degree"],
                "institution": e.get("institution", ""),
                "location": e.get("location"),
                "dates": fmt_range(e.get("start"), e.get("end"), present, date_format),
                "notes": ed.get("notes"),
            }
        )

    lang_names = labels.get("language_names") or {}
    levels = labels.get("levels") or {}
    languages = [
        {
            "name": lang_names.get(lg["code"], lg["code"]),
            "level": levels.get(lg["level"], lg["level"]),
        }
        for lg in profile.get("languages") or []
    ]

    for om in spec.get("omitted") or []:
        if om["ref"] not in entity_ids:
            errors.append(f"omitted refs unknown entity `{om['ref']}`")

    if errors:
        raise CvacError("broken references:\n  - " + "\n  - ".join(errors))
    if mode == "final" and unverified:
        raise CvacError(
            "--mode final but these cited facts are not verified:\n  - " + "\n  - ".join(unverified)
        )

    ident = profile["identity"]
    loc = ident["location"]
    location = loc["city"] + (f", {loc['country']}" if loc.get("country") else "")

    resolved: dict[str, Any] = {
        "meta": {
            "draft": mode == "draft",
            "language": spec["language"],
            "source": root.rel(spec_dir),
        },
        "labels": {
            "summary": lsec["summary"],
            "experience": lsec["experience"],
            "projects": lsec["projects"],
            "skills": lsec["skills"],
            "education": lsec["education"],
            "languages": lsec["languages"],
            "present": present,
        },
        "identity": {
            "full_name": ident["full_name"],
            "headline": spec["headline"],
            "location": location,
            "email": ident["email"],
            "phone": ident.get("phone"),
            "born": ident.get("born"),
            "links": ident.get("links") or [],
            "photo": None,
        },
        "summary": summary,
        "sections": [s for s in spec["sections"] if s in SECTIONS],
        "experience": resolved_exp,
        "projects": resolved_prj,
        "skills": {"groups": groups, "emphasis": emphasis},
        "education": education,
        "languages": languages,
    }

    if spec.get("footer"):
        resolved["meta"]["footer"] = spec["footer"]

    schema = json.loads(root.schema_path("cv-resolved").read_text("utf-8"))
    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(resolved), key=lambda e: list(e.absolute_path)
    )
    if schema_errors:
        msgs = [
            f"[{'/'.join(str(p) for p in e.absolute_path) or '<root>'}] {e.message}"
            for e in schema_errors
        ]
        raise RenderError(
            "resolved JSON fails cv-resolved.schema.json:\n  - " + "\n  - ".join(msgs)
        )

    out_json = spec_dir / "cv.resolved.json"
    out_json.write_text(json.dumps(resolved, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return ResolveResult(
        spec_dir=spec_dir, out_json=out_json, draft=mode == "draft", unverified=unverified
    )
