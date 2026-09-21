"""The `cvac` command line: the only surface a data root and its tools share.

Exit codes: 0 ok · 1 a validation, gate or render failure (the message names the
offending ids and paths) · 2 usage error. Output is English; user data is not.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .dataroot import ENV_VAR, MARKER, DataRoot
from .errors import CvacError
from .letter import render_letter
from .render import render
from .resolve import resolve
from .validate import discover_all, validate_files

INIT_GITIGNORE = """\
# Rendering products are regenerated: commit only what you deliberately deliver.
*-DRAFT.pdf
build/
*.report.md

# Raw document inbox: nothing enters git until it is archived in users/<slug>/sources/.
users/*/inbox/*
!users/*/inbox/README.md

# Agent-local configuration and session ephemera.
.claude/project.conf
.claude/settings.local.json
.claude/edit-log.jsonl
.claude/edit-log-archive/
"""

INIT_README = """\
# A cv-as-code data root

This directory holds *data only*: your profile, your search parameters, your
CVs and applications. The framework that reads it is the `cv-as-code` package
(https://github.com/EmanuelePartenza/cv-as-code); the `cvac.yaml` marker is
what tells it where the data root is.

```
cvac.yaml                 marker: schema_version, kind, default_user
users/<slug>/profile.yaml career facts, each with an id, a status and evidence
users/<slug>/search.yaml  target roles, markets, constraints
users/<slug>/masters/     generic CVs (cv-spec.yaml + rendered PDF)
users/<slug>/applications/<job_id>/   tailored CV, cover letter
users/<slug>/notes/       evidence notes cited by facts
users/<slug>/sources/     original documents (CVs, reviews), read-only
users/<slug>/inbox/       drop raw documents here for extraction (gitignored)
jobs/<job_id>/            postings: raw.txt verbatim + job.yaml normalised
i18n/, templates/         optional overrides of the package's labels and templates
```

Run `cvac validate --all` after every change; `cvac cv <spec-dir> --mode draft`
for a watermarked preview; `--mode final` only renders an approved spec that
cites verified facts.
"""

INBOX_README = """\
# Inbox

Drop raw documents here (old CVs, reviews, notes). They are extracted into
draft facts with an evidence note, then archived under `sources/`. Nothing in
this directory is tracked by git except this file.
"""


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.dir).expanduser().resolve()
    marker = target / MARKER
    if marker.exists():
        raise CvacError(f"{marker} already exists; refusing to overwrite a data root")
    target.mkdir(parents=True, exist_ok=True)
    lines = [
        "# cv-as-code data root - https://github.com/EmanuelePartenza/cv-as-code",
        "schema_version: 1",
        "kind: data-root",
    ]
    lines.append(f"default_user: {args.user}" if args.user else "# default_user: <slug>")
    marker.write_text("\n".join(lines) + "\n", "utf-8")
    (target / "users").mkdir(exist_ok=True)
    (target / "jobs").mkdir(exist_ok=True)
    (target / "jobs" / ".gitkeep").touch()
    gitignore = target / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(INIT_GITIGNORE, "utf-8")
    readme = target / "README.md"
    if not readme.exists():
        readme.write_text(INIT_README, "utf-8")
    if args.user:
        udir = target / "users" / args.user
        for sub in ("notes", "sources", "interviews", "inbox", "masters", "applications"):
            (udir / sub).mkdir(parents=True, exist_ok=True)
        (udir / "inbox" / "README.md").write_text(INBOX_README, "utf-8")
    else:
        (target / "users" / ".gitkeep").touch()
    print(f"initialised data root {target}")
    print("next: add users/<slug>/profile.yaml and search.yaml, then `cvac validate --all`")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = DataRoot.locate(args.data_root)
    if args.all:
        files = discover_all(root)
    elif args.files:
        files = [Path(f).expanduser().resolve() for f in args.files]
    else:
        args.parser.error("nothing to validate: pass files or --all")
    rep = validate_files(root, files)
    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")
    print(
        f"\n{len(files)} file(s) checked - {len(rep.errors)} error(s), "
        f"{len(rep.warnings)} warning(s)"
    )
    return 1 if rep.errors else 0


def _do_resolve(root: DataRoot, spec: str, mode: str) -> None:
    res = resolve(root, spec, mode)
    tag = "  [DRAFT]" if res.draft else ""
    print(f"resolved {root.rel(res.spec_dir)} -> cv.resolved.json{tag}")
    if res.draft and res.unverified:
        print(f"  note: {len(res.unverified)} cited fact(s) not yet verified (fine in draft)")


def _do_render(root: DataRoot, spec: str) -> None:
    res = render(root, spec)
    tag = "  [DRAFT]" if res.draft else ""
    print(f"rendered {root.rel(res.out_path)} - {res.pages} page(s){tag}")
    for w in res.warnings:
        print(f"  WARN: {w}")


def cmd_resolve(args: argparse.Namespace) -> int:
    _do_resolve(DataRoot.locate(args.data_root), args.spec, args.mode)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    _do_render(DataRoot.locate(args.data_root), args.spec)
    return 0


def cmd_cv(args: argparse.Namespace) -> int:
    root = DataRoot.locate(args.data_root)
    _do_resolve(root, args.spec, args.mode)
    _do_render(root, args.spec)
    return 0


def cmd_letter(args: argparse.Namespace) -> int:
    root = DataRoot.locate(args.data_root)
    res = render_letter(root, args.app, args.mode)
    tag = "  [DRAFT]" if res.draft else ""
    print(f"rendered {root.rel(res.out_path)} - {res.pages} page(s){tag}")
    for w in res.warnings:
        print(f"  WARN: {w}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cvac",
        description="cv-as-code: fact-grounded CVs with a human gate and a deterministic tail.",
    )
    parser.add_argument("--version", action="version", version=f"cvac {__version__}")
    parser.add_argument(
        "--data-root",
        metavar="PATH",
        help=f"data root to use (default: ${ENV_VAR}, else the nearest {MARKER} upward from cwd)",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    # accepted after the subcommand too; SUPPRESS keeps the global value when absent
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--data-root", metavar="PATH", default=argparse.SUPPRESS, help=argparse.SUPPRESS
    )

    p = sub.add_parser("init", parents=[common], help="scaffold a new data root")
    p.add_argument("dir")
    p.add_argument("--user", metavar="SLUG", help="also create users/<slug>/ and set default_user")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser(
        "validate", parents=[common], help="form + references + gates for data files"
    )
    p.add_argument("files", nargs="*", help="YAML files to validate")
    p.add_argument("--all", action="store_true", help="every known data file in the data root")
    p.set_defaults(func=cmd_validate, parser=p)

    for name, func, doc in (
        ("resolve", cmd_resolve, "profile x cv-spec x labels -> cv.resolved.json"),
        ("cv", cmd_cv, "resolve then render, in one shot"),
    ):
        p = sub.add_parser(name, parents=[common], help=doc)
        p.add_argument("spec", help="cv-spec.yaml or its directory")
        p.add_argument("--mode", choices=["draft", "final"], default="draft")
        p.set_defaults(func=func)

    p = sub.add_parser(
        "render", parents=[common], help="cv.resolved.json -> PDF (draft flag from the JSON)"
    )
    p.add_argument("spec", help="cv-spec.yaml or its directory")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("letter", parents=[common], help="letter.md -> PDF in the CV's style")
    p.add_argument("app", help="application directory containing letter.md")
    p.add_argument(
        "--mode",
        choices=["draft", "final"],
        default=None,
        help="default: final when the letter is approved, draft otherwise",
    )
    p.set_defaults(func=cmd_letter)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except CvacError as e:
        print(f"ERROR ({args.command}): {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
