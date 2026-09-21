"""Render a resolved cv-spec to PDF with Typst.

Reads cv.resolved.json produced by `resolve` and compiles it inside a transient
`build/` directory next to the spec (ADR-0012): Typst cannot import across its
root, so the template and the shared lib are copied there on every render, the
data root's `templates/` overriding the package's. Fonts are the package's own
and system fonts are ignored, so the same JSON and the same template give the
same PDF on any machine.

The draft flag comes from the resolved JSON: a draft resolve yields a `-DRAFT`
file name and a watermarked page. The page budget (`max_pages`) fails a final
render and only warns a draft one.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

from .dataroot import DataRoot, load_yaml
from .errors import RenderError

BUILD_DIR = "build"


@dataclass
class RenderResult:
    out_path: Path
    pages: int
    draft: bool
    warnings: list[str] = field(default_factory=list)


def prepare_build(root: DataRoot, build: Path, template: str) -> Path:
    """Assemble a self-contained Typst root: the template and the shared lib, nothing else."""
    tdir = root.template_dir(template)
    if tdir is None:
        raise RenderError(
            f"template `{template}` not found (looked in {root.rel(root.path / 'templates')} "
            "and the package)"
        )
    dest = build / "templates"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(tdir, dest / template)
    shutil.copytree(root.template_lib_dir(), dest / "lib")
    return build


def approval_timestamp(approved_on: object) -> int | None:
    """Final PDFs carry the approval date as creation time, so a re-render is byte-identical."""
    if not approved_on:
        return None
    y, m, d = (int(x) for x in str(approved_on).split("-")[:3])
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def compile_typst(
    entry: Path, output: Path, build: Path, fonts_dir: Path, timestamp: int | None = None
) -> None:
    import typst  # imported here: the compiler is heavy and only render needs it

    try:
        typst.compile(
            str(entry),
            output=str(output),
            root=str(build),
            font_paths=[str(fonts_dir)],
            ignore_system_fonts=True,
            timestamp=timestamp,
        )
    except RuntimeError as e:  # typst reports compiler diagnostics as RuntimeError
        raise RenderError(f"typst compile failed:\n{e}") from e


def page_count(pdf: Path) -> int:
    return len(PdfReader(str(pdf)).pages)


def draft_name(output_name: str, draft: bool) -> str:
    return output_name[:-4] + "-DRAFT.pdf" if draft else output_name


def render(root: DataRoot, spec_arg: str | Path) -> RenderResult:
    spec_dir = root.resolve_dir(spec_arg)
    spec_file = spec_dir / "cv-spec.yaml"
    resolved_file = spec_dir / "cv.resolved.json"
    for f in (spec_file, resolved_file):
        if not f.exists():
            raise RenderError(
                f"missing {root.rel(f)} - run `cvac resolve {root.rel(spec_dir)}` first"
            )

    spec = load_yaml(spec_file)
    resolved = json.loads(resolved_file.read_text("utf-8"))
    draft = bool(resolved["meta"]["draft"])
    max_pages = int(spec.get("max_pages", 2))

    build = prepare_build(root, spec_dir / BUILD_DIR, spec["template"])
    shutil.copy2(resolved_file, build / "cv.resolved.json")
    entry = build / "cv.typ"
    entry.write_text(
        f'#import "/templates/{spec["template"]}/template.typ": cv\n'
        '#cv(json("/cv.resolved.json"))\n',
        "utf-8",
    )

    out_path = spec_dir / draft_name(spec["output_name"], draft)
    stamp = None if draft else approval_timestamp(spec.get("approved_on"))
    compile_typst(entry, out_path, build, root.fonts_dir(), timestamp=stamp)
    pages = page_count(out_path)

    result = RenderResult(out_path=out_path, pages=pages, draft=draft)
    if pages > max_pages:
        msg = f"{pages} pages exceeds max_pages={max_pages}"
        if draft:
            result.warnings.append(f"{msg} (tighten the spec before final render)")
        else:
            raise RenderError(msg)
    return result
