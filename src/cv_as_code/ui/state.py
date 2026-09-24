"""Which data root the UI is on, and the roots it remembers (config dir, never a root)."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from flask import current_app

from ..dataroot import MARKER, DataRoot
from ..errors import CvacError
from ..scaffold import init_data_root

MAX_RECENT = 8


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "cvac" / "ui.yaml"


def read_config() -> dict[str, object]:
    path = config_path()
    if not path.is_file():
        return {}
    try:
        doc = yaml.safe_load(path.read_text("utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return doc if isinstance(doc, dict) else {}


def write_config(**updates: object) -> None:
    path = config_path()
    doc = {**read_config(), **updates}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), "utf-8")


def recent_roots() -> list[str]:
    recent = read_config().get("recent")
    return [str(p) for p in recent or [] if isinstance(p, str)]


def remember(root: Path) -> None:
    recent = [str(root)] + [p for p in recent_roots() if p != str(root)]
    write_config(recent=recent[:MAX_RECENT])


def saved_language() -> str | None:
    value = read_config().get("language")
    return str(value) if isinstance(value, str) else None


def save_language(lang: str) -> None:
    write_config(language=lang)


class UiState:
    """The mutable state of one UI process: the current root and the run manager."""

    def __init__(self, root: DataRoot | None, runs: object) -> None:
        self.root = root
        self.runs = runs

    def open(self, raw_path: str, create: bool = False) -> DataRoot:
        """Switch to a data root; with create, scaffold one in an empty or missing directory."""
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            raise CvacError("give an absolute path (or one starting with ~)")
        path = path.resolve()
        if path.is_file():
            raise CvacError(f"{path} is a file, not a folder")
        if (path / MARKER).is_file():
            self.root = DataRoot.load(path)
        elif create and (not path.exists() or (path.is_dir() and not any(path.iterdir()))):
            self.root = DataRoot.load(init_data_root(path))
        elif path.is_dir():
            raise CvacError(
                f"{path} exists and is not a data root (no {MARKER}); choose an empty or new "
                "directory to create one"
            )
        else:
            raise CvacError(
                f"{path} does not exist; tick 'create it' to scaffold a data root there"
            )
        remember(self.root.path)
        return self.root


def state() -> UiState:
    return current_app.extensions["cvac"]


def current_root() -> DataRoot:
    root = state().root
    if root is None:
        raise CvacError("no data root is open")
    return root


FOLDER_NAME_RE = re.compile(r"^[^/\\\0]+$")


def browse(raw_dir: str | None) -> dict[str, object]:
    """One directory of the machine as the chooser shows it: its folders and what each holds."""
    path = Path(raw_dir).expanduser() if raw_dir else Path.home()
    if not path.is_absolute():
        raise CvacError("give an absolute path (or one starting with ~)")
    path = path.resolve()
    if not path.is_dir():
        raise CvacError(f"{path} is not a folder")
    folders = []
    try:
        entries = sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith("."))
    except PermissionError as e:
        raise CvacError(f"{path}: permission denied") from e
    for p in entries:
        folders.append({"name": p.name, "path": str(p), "is_root": (p / MARKER).is_file()})
    try:
        empty = not any(path.iterdir())
    except PermissionError:
        empty = False
    return {
        "path": str(path),
        "parent": str(path.parent) if path.parent != path else None,
        "is_root": (path / MARKER).is_file(),
        "empty": empty,
        "folders": folders,
    }


def new_folder(raw_dir: str, name: str) -> Path:
    """A new empty folder inside an existing one; the caller makes it a data root."""
    name = (name or "").strip()
    if not FOLDER_NAME_RE.match(name) or name.startswith(".") or name in (".", ".."):
        raise CvacError(f"`{name}` is not a folder name")
    base = Path(raw_dir).expanduser().resolve()
    if not base.is_dir():
        raise CvacError(f"{base} is not a folder")
    target = base / name
    if target.exists():
        raise CvacError(f"{target} already exists")
    target.mkdir()
    return target
