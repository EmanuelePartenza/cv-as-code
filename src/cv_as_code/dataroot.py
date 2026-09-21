"""The data root: where a user's data lives, and how framework assets are looked up.

A data root is any directory carrying a `cvac.yaml` marker (see ADR-0006). It is
found, in order, from the `--data-root` flag, the `CVAC_DATA_ROOT` environment
variable, or by walking upward from the current directory like git does. Labels
and templates placed under the data root (`i18n/`, `templates/`) take precedence
over the ones shipped in the package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from .errors import CvacError

MARKER = "cvac.yaml"
ENV_VAR = "CVAC_DATA_ROOT"


def package_dir() -> Path:
    """Directory of the installed package (source checkout for editable installs)."""
    return Path(str(resources.files("cv_as_code")))


def load_yaml(path: Path) -> Any:
    """Parse a YAML file, turning a missing or malformed file into a CvacError."""
    if not path.is_file():
        raise CvacError(f"file not found: {path}")
    from .documents import normalise_dates  # local import: documents depends on errors only

    try:
        with open(path, encoding="utf-8") as f:
            return normalise_dates(yaml.safe_load(f))
    except yaml.YAMLError as e:
        raise CvacError(f"{path}: YAML parse error: {e}") from e


@dataclass
class DataRoot:
    path: Path
    config: dict[str, Any] = field(default_factory=dict)

    # ---- location -----------------------------------------------------------------
    @classmethod
    def locate(cls, explicit: str | os.PathLike[str] | None = None) -> DataRoot:
        """Flag > environment > upward discovery; the marker is mandatory only for discovery."""
        given = explicit or os.environ.get(ENV_VAR)
        if given:
            path = Path(given).expanduser().resolve()
            if not path.is_dir():
                raise CvacError(f"data root is not a directory: {path}")
            return cls.load(path, require_marker=False)
        cwd = Path.cwd().resolve()
        for candidate in (cwd, *cwd.parents):
            if (candidate / MARKER).is_file():
                return cls.load(candidate)
        raise CvacError(
            f"not inside a cv-as-code data root (no {MARKER} found upward from {cwd}); "
            "run 'cvac init <dir>' or pass --data-root"
        )

    @classmethod
    def load(cls, path: Path, require_marker: bool = True) -> DataRoot:
        marker = path / MARKER
        config: dict[str, Any] = {}
        if marker.is_file():
            loaded = load_yaml(marker)
            if not isinstance(loaded, dict):
                raise CvacError(f"{marker}: expected a mapping")
            config = loaded
        elif require_marker:
            raise CvacError(f"{path} has no {MARKER}")
        return cls(path=path, config=config)

    # ---- user data ---------------------------------------------------------------
    @property
    def default_user(self) -> str | None:
        return self.config.get("default_user")

    @property
    def users_dir(self) -> Path:
        return self.path / "users"

    @property
    def jobs_dir(self) -> Path:
        return self.path / "jobs"

    def user_dir(self, user: str) -> Path:
        return self.users_dir / user

    def profile_path(self, user: str) -> Path:
        return self.user_dir(user) / "profile.yaml"

    def job_dir(self, job_id: str) -> Path:
        return self.jobs_dir / job_id

    def rel(self, path: Path | str) -> str:
        """Display form of a path: relative to the data root when inside it."""
        p = Path(path).resolve()
        try:
            return str(p.relative_to(self.path))
        except ValueError:
            pass
        try:
            return "<package>/" + str(p.relative_to(package_dir()))
        except ValueError:
            return str(p)

    def resolve_dir(self, arg: str | os.PathLike[str]) -> Path:
        """A spec/application directory given absolute, cwd-relative or root-relative."""
        p = Path(arg).expanduser()
        if not p.is_absolute():
            from_cwd = Path.cwd() / p
            p = from_cwd if from_cwd.exists() else self.path / p
        p = p.resolve()
        return p if p.is_dir() else p.parent

    # ---- framework assets, data root first ----------------------------------------
    def labels_path(self, lang: str) -> Path | None:
        for base in (self.path / "i18n", package_dir() / "i18n"):
            candidate = base / f"labels.{lang}.yaml"
            if candidate.is_file():
                return candidate
        return None

    def labels_files(self) -> list[Path]:
        """Every labels file in scope: data-root overrides and the package's own."""
        files: list[Path] = []
        for base in (self.path / "i18n", package_dir() / "i18n"):
            files.extend(sorted(base.glob("labels.*.yaml")))
        return files

    def template_dir(self, name: str) -> Path | None:
        for base in (self.path / "templates", package_dir() / "templates"):
            if (base / name).is_dir():
                return base / name
        return None

    def template_lib_dir(self) -> Path:
        local = self.path / "templates" / "lib"
        return local if local.is_dir() else package_dir() / "templates" / "lib"

    def fonts_dir(self) -> Path:
        return package_dir() / "templates" / "fonts"

    def schema_path(self, kind: str) -> Path:
        return package_dir() / "schemas" / f"{kind}.schema.json"
