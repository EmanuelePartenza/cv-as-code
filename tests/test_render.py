"""Rendering: draft vs final artefacts, the page budget, the build directory, template overrides."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from conftest import dump, spec_doc, write_spec
from pypdf import PdfReader

from cv_as_code.dataroot import DataRoot, package_dir
from cv_as_code.errors import RenderError
from cv_as_code.render import draft_name, render
from cv_as_code.resolve import resolve


def pdf_text(path: Path) -> str:
    return "".join(p.extract_text() for p in PdfReader(str(path)).pages)


def test_draft_name() -> None:
    assert draft_name("A_B.pdf", True) == "A_B-DRAFT.pdf"
    assert draft_name("A_B.pdf", False) == "A_B.pdf"


def test_render_before_resolve_is_an_error(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    with pytest.raises(RenderError, match="run `cvac resolve users/test/masters/base` first"):
        render(data_root, d)


def test_draft_render_is_watermarked_and_suffixed(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    resolve(data_root, d, "draft")
    res = render(data_root, d)
    assert res.out_path.name == "Test_User_CV-DRAFT.pdf" and res.pages == 1 and res.draft
    assert "DRAFT" in pdf_text(res.out_path)


def test_final_render_has_no_watermark(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved")
    resolve(data_root, d, "final")
    res = render(data_root, d)
    assert res.out_path.name == "Test_User_CV.pdf" and not res.draft
    text = pdf_text(res.out_path)
    assert "DRAFT" not in text and "Widget Engineer" in text


def test_final_render_is_byte_for_byte_reproducible(data_root: DataRoot) -> None:
    d = write_spec(data_root, status="approved")
    resolve(data_root, d, "final")
    first = render(data_root, d).out_path.read_bytes()
    second = render(data_root, d).out_path.read_bytes()
    assert first == second


def test_build_directory_is_self_contained(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    resolve(data_root, d, "draft")
    render(data_root, d)
    build = d / "build"
    assert (build / "cv.typ").is_file() and (build / "cv.resolved.json").is_file()
    assert (build / "templates" / "classic" / "template.typ").is_file()
    assert (build / "templates" / "lib" / "common.typ").is_file()
    assert not (d / "cv.typ").exists()


def _long_spec(status: str) -> dict:
    doc = spec_doc(status=status, max_pages=1)
    bullet = {
        "text": "A long widget sentence that fills the line and then some more. " * 4,
        "source_facts": ["exp-acme.f01"],
    }
    doc["experience"][0]["bullets"] = [bullet] * 40
    return doc


def test_page_budget_warns_in_draft_and_fails_in_final(data_root: DataRoot) -> None:
    d = data_root.path / "users" / "test" / "masters" / "long"
    dump(d / "cv-spec.yaml", _long_spec("draft"))
    resolve(data_root, d, "draft")
    res = render(data_root, d)
    assert res.pages > 1 and any("exceeds max_pages=1" in w for w in res.warnings)

    dump(d / "cv-spec.yaml", _long_spec("approved"))
    resolve(data_root, d, "final")
    with pytest.raises(RenderError, match="exceeds max_pages=1"):
        render(data_root, d)


def test_data_root_template_overrides_the_package(data_root: DataRoot) -> None:
    src = package_dir() / "templates" / "classic"
    dst = data_root.path / "templates" / "classic"
    shutil.copytree(src, dst)
    template = dst / "template.typ"
    template.write_text(
        template.read_text("utf-8").replace(
            "// ---------- header ----------", "[OVERRIDE-MARK]\n// ---------- header ----------"
        ),
        "utf-8",
    )
    d = write_spec(data_root)
    resolve(data_root, d, "draft")
    assert "OVERRIDE-MARK" in pdf_text(render(data_root, d).out_path)


def test_missing_template_is_a_render_error(data_root: DataRoot) -> None:
    d = write_spec(data_root)
    resolve(data_root, d, "draft")
    import yaml

    doc = yaml.safe_load((d / "cv-spec.yaml").read_text("utf-8"))
    doc["template"] = "nope"
    dump(d / "cv-spec.yaml", doc)
    with pytest.raises(RenderError, match="template `nope` not found"):
        render(data_root, d)
