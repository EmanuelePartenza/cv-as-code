"""The example data root, end to end: validates clean, renders one-page PDFs, packs every stage,
and the gates refuse what they must."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pypdf import PdfReader

from cv_as_code.dataroot import DataRoot
from cv_as_code.errors import CvacError
from cv_as_code.letter import render_letter
from cv_as_code.render import render
from cv_as_code.resolve import resolve
from cv_as_code.stages import pack, resolve_stage
from cv_as_code.validate import discover_all, validate_files

EXAMPLE = Path(__file__).resolve().parents[1] / "example"
JOB = "20260915-saltmere-port-operations-officer"
APP = f"users/robin/applications/{JOB}"
MASTERS = ("users/robin/masters/port-operations-en", "users/robin/masters/port-operations-fr")


@pytest.fixture
def example(tmp_path: Path) -> DataRoot:
    root = tmp_path / "example"
    shutil.copytree(EXAMPLE, root)
    return DataRoot.load(root)


def pdf_text(path: Path) -> str:
    return "".join(p.extract_text() for p in PdfReader(str(path)).pages)


def test_example_validates_with_no_errors_and_no_warnings(example: DataRoot) -> None:
    rep = validate_files(example, discover_all(example))
    assert rep.errors == [] and rep.warnings == []


def test_example_renders_three_one_page_cvs_and_a_letter(example: DataRoot) -> None:
    for spec in (*MASTERS, APP):
        resolve(example, spec, "final")
        res = render(example, spec)
        assert res.pages == 1 and not res.draft, spec
        assert "DRAFT" not in pdf_text(res.out_path)
    assert "Robin Ashcombe" in pdf_text(
        example.path / MASTERS[0] / "Robin_Ashcombe_Port_Operations_EN.pdf"
    )
    letter = render_letter(example, APP)
    assert letter.pages == 1 and not letter.draft


def test_french_master_renders_french_labels_from_an_english_pivot(example: DataRoot) -> None:
    resolve(example, MASTERS[1], "final")
    text = pdf_text(render(example, MASTERS[1]).out_path)
    assert "EXPÉRIENCE PROFESSIONNELLE" in text and "Anglais" in text and "Présent" in text


def test_footer_is_on_the_example_cvs(example: DataRoot) -> None:
    resolve(example, MASTERS[0], "final")
    assert "Generated with cv-as-code" in pdf_text(render(example, MASTERS[0]).out_path)


def test_every_production_stage_packs_on_the_example(example: DataRoot) -> None:
    params = {"user": "robin", "job_id": JOB, "master": "port-operations-en"}
    for stage in ("10_normalize", "20_match", "30_tailor", "60_letter"):
        text = pack(example, resolve_stage(example, stage, params))
        assert text.startswith(f"# Stage {stage}")
    text = pack(
        example,
        resolve_stage(
            example,
            "03_extract",
            {"user": "robin", "document": "interviews/01-onboarding.md", "name": "01-onboarding"},
        ),
    )
    assert "## Input users/robin/interviews/01-onboarding.md" in text


def test_the_gates_refuse_a_draft_fact_in_an_approved_spec(example: DataRoot) -> None:
    spec = example.path / MASTERS[0] / "cv-spec.yaml"
    spec.write_text(
        spec.read_text().replace("exp-skerra.f03]", "exp-skerra.f03, exp-skerra.f09]", 1)
    )
    rep = validate_files(example, [spec])
    assert any("cites non-verified fact(s): exp-skerra.f09" in e for e in rep.errors)
    with pytest.raises(CvacError, match="not verified"):
        resolve(example, MASTERS[0], "final")


def test_the_gates_refuse_a_final_render_of_a_draft(example: DataRoot) -> None:
    spec = example.path / MASTERS[1] / "cv-spec.yaml"
    spec.write_text(spec.read_text().replace("status: approved", "status: draft", 1))
    with pytest.raises(CvacError, match="requires status: approved"):
        resolve(example, MASTERS[1], "final")
