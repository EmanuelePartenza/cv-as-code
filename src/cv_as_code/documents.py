"""Reading the documents the framework validates: YAML files and markdown files with a
YAML frontmatter (cover letters, questionnaires)."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

import yaml

from .errors import CvacError

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def normalise_dates(value: Any) -> Any:
    """YAML turns an unquoted 2026-01-02 into a date object; the contracts want ISO strings."""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: normalise_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise_dates(v) for v in value]
    return value


def has_front_matter(text: str) -> bool:
    return FRONT_MATTER_RE.match(text) is not None


def parse_front_matter(text: str, where: str) -> tuple[dict[str, Any], str]:
    """Split a markdown document into (frontmatter mapping, body); the frontmatter is required."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        raise CvacError(f"{where} has no YAML frontmatter")
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        raise CvacError(f"{where}: frontmatter YAML parse error: {e}") from e
    if not isinstance(fm, dict):
        raise CvacError(f"{where}: frontmatter is not a mapping")
    return normalise_dates(fm), m.group(2).strip()


def load_document(path: Path, where: str | None = None) -> Any:
    """The validatable mapping of a file: the YAML document, or a markdown file's frontmatter."""
    where = where or str(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        return parse_front_matter(text, where)[0]
    try:
        return normalise_dates(yaml.safe_load(text))
    except yaml.YAMLError as e:
        raise CvacError(f"{where}: YAML parse error: {e}") from e
