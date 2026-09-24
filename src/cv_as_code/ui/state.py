"""Which data root the UI is on, and the roots it remembers (config dir, never a root)."""

from __future__ import annotations

import os
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


def recent_roots() -> list[str]:
    path = config_path()
    if not path.is_file():
        return []
    try:
        doc = yaml.safe_load(path.read_text("utf-8")) or {}
    except yaml.YAMLError:
        return []
    recent = doc.get("recent") if isinstance(doc, dict) else None
    return [str(p) for p in recent or [] if isinstance(p, str)]


def remember(root: Path) -> None:
    path = config_path()
    recent = [str(root)] + [p for p in recent_roots() if p != str(root)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"recent": recent[:MAX_RECENT]}, sort_keys=False), "utf-8")


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
