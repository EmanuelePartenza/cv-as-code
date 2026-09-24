"""Stage contracts: list them, resolve their inputs for a data root, pack them for any engine.

A stage is `pipeline/<NN_name>/` with INSTRUCTIONS.md (the prompt) and io.yaml (the
contract, schema stage-io.schema.json). `pack` assembles instructions and inputs into
one markdown document: the manual path for a person with only a chat window, and the
same material a skill or an API runner would use (ADR-0002).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .dataroot import DataRoot, load_yaml, package_dir
from .errors import CvacError

PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")
FLAGS = {
    "user": "--user",
    "job_id": "--job",
    "master": "--master",
    "mode": "--mode",
    "document": "--document",
    "name": "--name",
}


def pipeline_dir() -> Path:
    return package_dir() / "pipeline"


def list_stages() -> list[str]:
    return sorted(p.name for p in pipeline_dir().iterdir() if (p / "io.yaml").is_file())


@dataclass
class Stage:
    name: str
    contract: dict[str, Any]
    instructions: str

    @property
    def gate(self) -> str:
        return str(self.contract["gate"])

    @property
    def params(self) -> list[str]:
        return list(self.contract["params"])


def load_stage(name: str) -> Stage:
    d = pipeline_dir() / name
    if not (d / "io.yaml").is_file():
        raise CvacError(f"unknown stage `{name}` (known: {', '.join(list_stages())})")
    contract = load_yaml(d / "io.yaml")
    schema = json.loads((package_dir() / "schemas" / "stage-io.schema.json").read_text("utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda e: list(e.path))
    if errors:
        msgs = [
            f"[{'/'.join(str(p) for p in e.absolute_path) or '<root>'}] {e.message}" for e in errors
        ]
        raise CvacError(
            f"pipeline/{name}/io.yaml fails stage-io.schema.json:\n  - " + "\n  - ".join(msgs)
        )
    if contract["stage"] != name:
        raise CvacError(f"pipeline/{name}/io.yaml declares stage `{contract['stage']}`")
    instructions = (d / "INSTRUCTIONS.md").read_text("utf-8")
    return Stage(name=name, contract=contract, instructions=instructions)


def fill(template: str, params: dict[str, str], where: str) -> str:
    """Substitute {placeholders}; a missing param is an error naming it."""
    missing = sorted({m.group(1) for m in PLACEHOLDER_RE.finditer(template)} - set(params))
    if missing:
        raise CvacError(f"{where} needs {', '.join(FLAGS.get(m, '--' + m) for m in missing)}")
    return PLACEHOLDER_RE.sub(lambda m: params[m.group(1)], template)


@dataclass
class ResolvedStage:
    stage: Stage
    params: dict[str, str]
    inputs: list[tuple[str, Path, bool]] = field(default_factory=list)  # (template, path, optional)
    output: Path | None = None
    output_rel: str = ""

    @staticmethod
    def is_dir_input(template: str) -> bool:
        """An input whose path ends with `/` is a directory: each regular file in it is an input."""
        return template.endswith("/")

    def present(self, path: Path, template: str) -> bool:
        return path.is_dir() if self.is_dir_input(template) else path.is_file()


def files_in(directory: Path) -> list[Path]:
    """The documents of a directory input: regular files, hidden and README left out, sorted."""
    if not directory.is_dir():
        return []
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.name.lower() != "readme.md"
    )


def resolve_stage(root: DataRoot, name: str, params: dict[str, str]) -> ResolvedStage:
    stage = load_stage(name)
    given = {k: v for k, v in params.items() if v}
    if "user" in stage.params and "user" not in given and root.default_user:
        given["user"] = root.default_user
    resolved = ResolvedStage(stage=stage, params=given)
    for item in stage.contract["inputs"]:
        rel = fill(item["path"], given, f"stage {name} input `{item['path']}`")
        resolved.inputs.append((item["path"], root.path / rel, bool(item.get("optional", False))))
    out_rel = fill(stage.contract["output"]["path"], given, f"stage {name} output")
    resolved.output = root.path / out_rel
    resolved.output_rel = out_rel
    return resolved


def describe(root: DataRoot, rs: ResolvedStage) -> str:
    c = rs.stage.contract
    lines = [
        f"stage:           {rs.stage.name}",
        f"engine:          {c['engine']}   gate: {c['gate']}   "
        f"output language: {c['output_language']}",
        f"params:          {', '.join(f'{k}={v}' for k, v in rs.params.items()) or '-'}",
        "inputs:",
    ]
    for template, path, optional in rs.inputs:
        if rs.is_dir_input(template):
            n = len(files_in(path))
            mark = (
                f"{n} file(s)" if path.is_dir() else ("absent, optional" if optional else "MISSING")
            )
        else:
            mark = "present" if path.is_file() else ("absent, optional" if optional else "MISSING")
        lines.append(f"  - {root.rel(path)}  [{mark}]")
    out = c["output"]
    lines.append(f"output:          {rs.output_rel}  ({out['format']}, schema {out['schema']})")
    lines.append(f"instructions:    <package>/pipeline/{rs.stage.name}/INSTRUCTIONS.md")
    return "\n".join(lines)


def language_note(root: DataRoot, rs: ResolvedStage) -> str:
    """What 'output language' means for this user, so a chat engine cannot miss it."""
    rule = rs.stage.contract["output_language"]
    user = rs.params.get("user")
    pivot = None
    if user:
        profile_path = root.profile_path(user)
        if profile_path.is_file():
            pivot = load_yaml(profile_path).get("pivot_language")
    if rule == "pivot":
        return f"Write prose in the user's pivot language: `{pivot or 'see profile.yaml'}`."
    if rule == "target":
        return "Write in the target language of the CV/letter (the spec's `language`)."
    if rule == "posting":
        return "Keep the posting's own language and wording."
    return "Write in English."


def _fenced(rel: str, path: Path) -> list[str]:
    try:
        body = path.read_text("utf-8").rstrip()
    except UnicodeDecodeError:
        return ["", f"## Input {rel}", "", f"_(binary document at `{rel}`: read it from disk)_"]
    fence = "yaml" if path.suffix in {".yaml", ".yml"} else "text"
    return ["", f"## Input {rel}", "", f"```{fence}", body, "```"]


def pack(root: DataRoot, rs: ResolvedStage) -> str:
    """One markdown document: instructions, every input fenced, what to do with the output."""
    c = rs.stage.contract
    parts = [
        f"# Stage {rs.stage.name}",
        "",
        f"- gate: **{c['gate']}**"
        + (
            " — the output is a draft; only a person sets it to approved"
            if c["gate"] == "human"
            else ""
        ),
        f"- output language: {language_note(root, rs)}",
        f"- output: `{rs.output_rel}` ({c['output']['format']}"
        + (f", must validate against `{c['output']['schema']}`" if c["output"]["schema"] else "")
        + ")",
        "",
        "---",
        "",
        rs.stage.instructions.strip(),
        "",
    ]
    for attachment in c.get("attachments") or []:
        body = (pipeline_dir() / rs.stage.name / attachment).read_text("utf-8").rstrip()
        parts += ["", "---", "", f"# Attachment {attachment}", "", "```markdown", body, "```"]
    parts += ["", "---", "", "# Inputs"]
    for template, path, optional in rs.inputs:
        rel = root.rel(path)
        if not rs.present(path, template):
            if optional:
                parts += ["", f"## Input {rel}", "", "_(absent; this input is optional)_"]
                continue
            raise CvacError(f"stage {rs.stage.name}: input {rel} is missing (from `{template}`)")
        files = files_in(path) if rs.is_dir_input(template) else [path]
        if rs.is_dir_input(template):
            listing = "\n".join(f"- `{root.rel(f)}`" for f in files) or "_(no document)_"
            parts += ["", f"## Input {rel} ({len(files)} document(s))", "", listing]
        for f in files:
            parts += _fenced(root.rel(f), f)
    parts += [
        "",
        "---",
        "",
        "# What to do with the output",
        "",
        f"Write the result to `{rs.output_rel}` exactly as specified above, then run",
        f"`cvac validate {rs.output_rel}`. If it fails, fix the document and validate again.",
        "Never set `status: approved` or a fact to `verified`: those are the user's acts.",
        "",
    ]
    return "\n".join(parts)
