"""The local UI: a Flask adapter over the library, nothing more (ADR-0014)."""

from .app import create_app, serve

__all__ = ["create_app", "serve"]
