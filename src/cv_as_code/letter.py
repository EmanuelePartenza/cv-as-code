"""Render a cover letter (letter.md) to PDF with Typst, in the CV's style.

letter.md = YAML frontmatter + markdown body. Identity comes from the user's
profile; the body is split into paragraphs (blank-line separated, wrapped lines
collapsed to spaces) and rendered as literal text, so no Typst markup surprises.

Gate: mode final (the default when the frontmatter says `status: approved`)
requires `status: approved`. A non-approved letter renders with a DRAFT
watermark and a `-DRAFT` file name. The fact-grounding of a letter is checked by
`cvac validate` on the frontmatter's source_facts and is human-gated at approval.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .dataroot import DataRoot, load_yaml
from .documents import parse_front_matter
from .errors import CvacError
from .render import (
    BUILD_DIR,
    RenderResult,
    approval_timestamp,
    compile_typst,
    draft_name,
    page_count,
    prepare_build,
)
from .resolve import load_labels


def fmt_letter_date(iso: str, months: list[str]) -> str:
    y, mo, d = (iso.split("-") + ["1", "1"])[:3]
    return f"{int(d)} {months[int(mo) - 1]} {y}"


def render_letter(root: DataRoot, app_arg: str | Path, mode: str | None = None) -> RenderResult:
    app_dir = root.resolve_dir(app_arg)
    letter_md = app_dir / "letter.md"
    if not letter_md.exists():
        raise CvacError(f"missing {root.rel(letter_md)}")

    fm, body = parse_front_matter(letter_md.read_text("utf-8"), root.rel(letter_md))
    status = fm.get("status", "draft")
    mode = mode or ("final" if status == "approved" else "draft")
    if mode == "final" and status != "approved":
        raise CvacError(
            f"--mode final requires status: approved (got {status!r}); "
            "the human gate has not signed off"
        )
    draft = mode != "final"

    user = fm.get("user")
    if not user:
        raise CvacError("letter.md frontmatter is missing `user`")
    lang = fm.get("language", "en")
    labels = load_labels(root, lang)
    profile = load_yaml(root.profile_path(str(user)))
    ident = profile["identity"]
    loc = ident["location"]

    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    resolved = {
        "meta": {"draft": draft, "language": lang},
        "identity": {
            "full_name": ident["full_name"],
            "headline": fm.get("headline", ""),
            "location": loc["city"] + (f", {loc['country']}" if loc.get("country") else ""),
            "email": ident["email"],
            "phone": ident.get("phone"),
            "links": ident.get("links") or [],
        },
        "date": fmt_letter_date(str(fm.get("created", "")), labels["months"]),
        "paragraphs": paragraphs,
    }
    resolved_file = app_dir / "letter.resolved.json"
    resolved_file.write_text(json.dumps(resolved, ensure_ascii=False, indent=2) + "\n", "utf-8")

    template = fm.get("template", "classic")
    build = prepare_build(root, app_dir / BUILD_DIR, template)
    shutil.copy2(resolved_file, build / "letter.resolved.json")
    entry = build / "letter.typ"
    entry.write_text(
        f'#import "/templates/{template}/letter.typ": letter\n'
        '#letter(json("/letter.resolved.json"))\n',
        "utf-8",
    )

    out_path = app_dir / draft_name(fm.get("output_name") or "cover-letter.pdf", draft)
    stamp = None if draft else approval_timestamp(fm.get("approved_on"))
    compile_typst(entry, out_path, build, root.fonts_dir(), timestamp=stamp)
    pages = page_count(out_path)
    result = RenderResult(out_path=out_path, pages=pages, draft=draft)
    if pages > 1:
        result.warnings.append(f"cover letter is {pages} pages - tighten it to one")
    return result
