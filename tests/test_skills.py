"""Domain skills: shipped in the package, installed into a data root, never drifting."""

from __future__ import annotations

from pathlib import Path

from cv_as_code.cli import main
from cv_as_code.dataroot import DataRoot
from cv_as_code.skills import NOTICE, install, list_skills, rendered

REPO = Path(__file__).resolve().parents[1]
DOMAIN = ["cover-letter", "cv-master", "cv-tailor", "interview-prep", "job-ingest", "onboard"]


def test_the_six_domain_skills_ship_with_frontmatter() -> None:
    assert list_skills() == DOMAIN
    for name in DOMAIN:
        text = rendered(name)
        assert text.startswith("---\n") and "description:" in text
        assert "disable-model-invocation: true" in text
        head, _, rest = text.partition("\n---\n")
        assert rest.startswith(NOTICE.split("{")[0])


def test_install_writes_into_a_data_root(data_root: DataRoot, tmp_path: Path) -> None:
    written = install(tmp_path / "skills")
    assert [p.parent.name for p in written] == DOMAIN
    assert main(["skills", "install", "--data-root", str(data_root.path)]) == 0
    assert (data_root.path / ".claude" / "skills" / "cv-tailor" / "SKILL.md").is_file()


def test_repository_copies_match_the_sources() -> None:
    """The framework repo carries installed copies so a contributor has them; they may not drift."""
    for name in DOMAIN:
        copy = REPO / ".claude" / "skills" / name / "SKILL.md"
        assert copy.is_file(), f"run `cvac skills install --to .claude/skills` ({name} missing)"
        assert copy.read_text("utf-8") == rendered(name), f"{name}: stale copy, re-run install"
