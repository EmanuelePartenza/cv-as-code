# ADR-0014 — A local, server-rendered UI as a thin adapter over the library

- **Status**: accepted
- **Date**: 2026-09-23

## Context

The tool had three surfaces: the `cvac` CLI, the Claude Code skills and
`cvac stage pack` for any chat. All three are adapters over one library where
every rule lives once (`validate`, `resolve`, `render`, `facts`, `report`,
`stages`). What a person does most with the tool is the human gate and its
views: see the profile and what it lacks, verify or reject facts, review a
draft PDF, approve a spec or a letter, render the final. Those are clicks and
looks, and a terminal serves them badly; the maintainer asked for a UI
(decision D-06). The constraints are the existing ones: the UI reads and
writes only through a data root ([ADR-0006](0006-code-data-split-and-data-root.md));
no code path sets `verified` or `approved` except on a person's explicit act
([ADR-0001](0001-fact-grounded-profile.md)); English surface, user-language
data ([ADR-0007](0007-language-layers.md)); nothing built before a user
exercises it, the example user counts ([ADR-0008](0008-example-user-is-a-user.md));
Python 3.10+, ruff and pytest as the whole quality floor. Running an LLM
stage from a UI needs an engine the UI can call; the API runner is roadmap, so
the first value of a UI is the gate, not the stages.

## Decision

- **The UI is a fourth adapter, not a second implementation.** It lives in
  `src/cv_as_code/ui/`, imports the library and is imported by nothing in the
  library; a rule that the UI needs and the library lacks is added to the
  library first (as `specs.approve` was) so that the CLI, the skills and the UI
  stay equivalent.
- **Local and server-rendered.** `cvac ui` starts a Flask application bound
  to the loopback interface and opens the browser; pages are Jinja2 templates
  and plain HTML forms; no JavaScript build step, no bundler, no external
  asset at runtime. Single user, no authentication by design: it is a local
  program with a window, not a service.
- **An optional extra.** `pip install "cv-as-code[ui]"` adds Flask; the core
  dependency set of the CLI does not change. The CLI reports the missing extra
  in one line.
- **The gate stays a person's act.** Verify, reject and approve are buttons
  whose handlers call the same library functions the CLI calls, with the same
  refusals (no evidence, unverified cited facts, validation errors). Nothing in
  the UI approves or verifies on a timer, a rule or a default.
- **The UI never commits.** It shows the data root's git status and leaves
  committing to the person, like the skills do.
- **Built in vertical slices, each exercised on the example user**: (1) gate
  and views, (2) the manual stage path in the browser, (3) the stage screen
  over the API runner once that exists (its own ADR).

## Consequences

- Every screen is a second surface to keep honest: each slice ships with
  route tests on the synthetic fixture and on Robin, and the documentation
  lists what the UI does not do.
- Flask, Jinja2 and Werkzeug enter the dependency tree of the `ui` extra
  (BSD-3-Clause, `TO VERIFY` on each upgrade; Flask 3.1 requires Python 3.9+).
- A local server is still a server: it binds to `127.0.0.1` by default and
  `--host` exists only for a person who knows why; the documentation says so.
- Partial page updates (HTMX or similar) are deferred until a screen needs
  them; adding a vendored script then is a local change, not a new decision.
- Roadmap line "an HTML view of the profile report" is superseded: the
  profile screen is that view.

## Alternatives considered

- **A terminal UI (Textual).** No PDF preview, the artefact reviewers look at;
  long texts (questionnaires, evidence quotes) are painful; harder to test.
- **A single-page application over a JSON API.** A second language, a Node
  toolchain and a build step in CI for a single-user local tool of two
  thousand lines of Python; the rule against over-engineering exists for this.
  A JSON route next to an HTML one is possible in Flask if a client ever needs
  it.
- **Streamlit or NiceGUI.** Fast first screen; their rerun-on-every-click
  state model fights file-based data and makes a gate feel accidental.
- **Claude Code and Obsidian as the UI.** Already true and kept; it leaves the
  gates in the terminal and a stranger without Claude Code with the CLI only.
- **A separate repository for the UI.** Duplicates the process machinery and
  splits the data contracts from their consumer.
