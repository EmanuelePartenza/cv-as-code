"""Cover letters: frontmatter gate, language-aware date, paragraph handling."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.letter import fmt_letter_date, parse_front_matter, render_letter

FRONT = """\
---
kind: cover-letter
user: test
job_id: 20260101-acme-widget
language: {lang}
headline: Widget Engineer
template: classic
output_name: Test_User_Letter.pdf
status: {status}
created: 2026-02-01
source_facts: [exp-acme.f01]
---
"""

BODY = """\
Dear Acme team,

I built the widget
pipeline end to end.

Kind regards,
Test User
"""


def write_letter(root: DataRoot, status: str = "draft", lang: str = "en") -> Path:
    d = root.path / "users" / "test" / "applications" / "20260101-acme-widget"
    d.mkdir(parents=True, exist_ok=True)
    (d / "letter.md").write_text(FRONT.format(lang=lang, status=status) + BODY, "utf-8")
    return d


def test_fmt_letter_date_uses_the_labels_months() -> None:
    months = ["gennaio", "febbraio"] + ["x"] * 10
    assert fmt_letter_date("2026-02-01", months) == "1 febbraio 2026"


def test_parse_front_matter_requires_a_mapping() -> None:
    with pytest.raises(CvacError, match="has no YAML frontmatter"):
        parse_front_matter("no frontmatter here", "letter.md")
    with pytest.raises(CvacError, match="frontmatter is not a mapping"):
        parse_front_matter("---\n- a list\n---\nbody", "letter.md")


def test_draft_letter_renders_watermarked_with_collapsed_paragraphs(data_root: DataRoot) -> None:
    d = write_letter(data_root)
    res = render_letter(data_root, d)
    assert res.out_path.name == "Test_User_Letter-DRAFT.pdf" and res.pages == 1 and res.draft
    import json

    resolved = json.loads((d / "letter.resolved.json").read_text("utf-8"))
    assert resolved["paragraphs"][1] == "I built the widget pipeline end to end."
    assert resolved["date"] == "1 February 2026"
    text = PdfReader(str(res.out_path)).pages[0].extract_text()
    assert "DRAFT" in text and "Dear Acme team" in text


def test_italian_letter_date(data_root: DataRoot) -> None:
    d = write_letter(data_root, lang="it")
    render_letter(data_root, d)
    import json

    assert json.loads((d / "letter.resolved.json").read_text("utf-8"))["date"] == "1 febbraio 2026"


def test_final_requires_approval(data_root: DataRoot) -> None:
    d = write_letter(data_root)
    with pytest.raises(CvacError, match="requires status: approved"):
        render_letter(data_root, d, "final")


def test_approved_letter_defaults_to_final(data_root: DataRoot) -> None:
    d = write_letter(data_root, status="approved")
    res = render_letter(data_root, d)
    assert res.out_path.name == "Test_User_Letter.pdf" and not res.draft
    assert "DRAFT" not in PdfReader(str(res.out_path)).pages[0].extract_text()


def test_missing_user_and_missing_file(data_root: DataRoot) -> None:
    d = write_letter(data_root)
    (d / "letter.md").write_text("---\nstatus: draft\n---\nbody\n", "utf-8")
    with pytest.raises(CvacError, match="missing `user`"):
        render_letter(data_root, d)
    (d / "letter.md").unlink()
    with pytest.raises(
        CvacError, match="missing users/test/applications/20260101-acme-widget/letter.md"
    ):
        render_letter(data_root, d)
