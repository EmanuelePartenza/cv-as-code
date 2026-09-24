"""The UI's own language: its chrome in en/fr/de/it; library messages stay English (ADR-0016)."""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

import yaml
from flask import g, has_request_context, request

LANGUAGES = {"en": "English", "fr": "Français", "de": "Deutsch", "it": "Italiano"}
DEFAULT = "en"
CATALOG_DIR = Path(__file__).parent / "i18n"
KEY_RE = re.compile(r"""\bt\(\s*(['"])((?:\\.|(?!\1).)*)\1""")


@cache
def catalog(lang: str) -> dict[str, str]:
    path = CATALOG_DIR / f"{lang}.yaml"
    if lang == DEFAULT or not path.is_file():
        return {}
    doc = yaml.safe_load(path.read_text("utf-8")) or {}
    return {str(k): str(v) for k, v in doc.items()}


def translate(lang: str, text: str, **values: object) -> str:
    out = catalog(lang).get(text, text)
    return out.format(**values) if values else out


def current_language() -> str:
    if not has_request_context():
        return DEFAULT
    return getattr(g, "lang", DEFAULT)


def t(text: str, **values: object) -> str:
    """Translate a chrome string into the request's language; the English text is the key."""
    return translate(current_language(), text, **values)


def negotiate(saved: str | None) -> str:
    """The saved choice, else the browser's best match among the four, else English."""
    if saved in LANGUAGES:
        return saved
    best = request.accept_languages.best_match(list(LANGUAGES))
    return best or DEFAULT


def used_keys() -> set[str]:
    """Every chrome string the templates and handlers pass to t(); the catalogs must cover them."""
    keys: set[str] = set()
    for path in list(Path(__file__).parent.glob("*.py")) + list(
        (Path(__file__).parent / "templates").glob("*.html")
    ):
        for m in KEY_RE.finditer(path.read_text("utf-8")):
            keys.add(m.group(2).replace("\\'", "'").replace('\\"', '"'))
    return keys
