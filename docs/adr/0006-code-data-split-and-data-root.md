# ADR-0006 — Code/data split: two repositories and the data-root contract

- **Status**: accepted
- **Date**: 2026-09-21

## Context

The framework was born inside one person's working repository, next to that
person's profile, applications and documents, with code that read hard-coded
`users/<slug>/` paths from the repository root. Publishing it required a clean
line between the reusable tool and any user's data — a line that must hold by
construction, because the public half may end up as an installable package or
an executable while each user keeps their data wherever suits them, and
because one copy of the code, never two, is the only arrangement that does not
drift.

## Decision

- **Two repositories.** The public one holds the framework only: package,
  schemas, templates, labels, stage contracts, skills, tests, docs, and one
  example data root. A user's data lives in a **data root** of their own —
  a directory, a private repository, anything — that the framework never
  contains.
- **A data root is any directory carrying `cvac.yaml`** (`kind: data-root`,
  `schema_version`, optional `default_user`). Everything the framework reads or
  writes for a user lives under it: `users/<slug>/`, `jobs/`, and optional
  `i18n/` and `templates/` overrides that take precedence over the package's.
- **Location precedence**: `--data-root` flag, then `CVAC_DATA_ROOT`, then
  upward discovery from the current directory (like git finds `.git`); the
  marker is mandatory only for discovery.
- **One copy of the code.** A data root contains no framework code; the
  maintainer's own data repository refuses code in its pre-commit hook and
  points at the framework installed alongside (an editable install). Framework
  changes are made in the framework repository and reach every data root
  through the installed package.
- **Documents are the interface.** Every YAML the framework touches carries
  `kind` and `schema_version` and has a schema in the package; `cvac validate`
  is the only thing both sides must agree on.

## Consequences

- The boundary is demonstrable: `cvac` runs against any directory with the
  marker, and the example data root proves it from a fresh clone.
- Data-root overrides give "new language = one YAML file" and "new template =
  one directory" without forking the framework.
- Cost: two working copies for the maintainer (framework and data), and the
  discipline of not patching the framework from a data session — enforced by
  the data repository's hook, not by memory.
- Known limit: the contract is file-based; a database-backed data root would be
  a new ADR.

## Alternatives considered

- **A private repository embedding the public one as a submodule.** Clean on
  paper; submodules are a daily tax and the code would exist in two working
  trees anyway.
- **Periodic copy from the private repository to the public one.** Simple today,
  guaranteed drift tomorrow; and it never proves that the code works outside
  its birthplace.
- **An environment variable only.** Invisible state that breaks on a new shell
  or machine; kept as an override, not as the mechanism.
- **A per-machine configuration file naming the data root.** Couples a machine
  to one data root; the maintainer has two (the example and their own).
