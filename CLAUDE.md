# CLAUDE.md

Entry point for Claude Code on this repository, loaded at every session. It is a
**navigator**: what the project is, which rules always apply, which document to
load for which task. It indexes the documents; it does not duplicate them.

## What this project is

**cv-as-code** — fact-grounded CV generation. Verified career facts in a user's
data root → an LLM-drafted content spec whose every line cites its source facts →
a human approval gate → a deterministic Python + Typst tail that renders the PDF.
The framework is public and reusable; every user's data lives in a private data
root of their own, never here.

Horizon: multi-year. Stack: Python 3.10+, Typst from PyPI, pytest, ruff.

**At session start**: read [STATUS.md](STATUS.md) and resume from there.

## Where to look first

| You need... | Document |
|---|---|
| Design, data model, pipeline, roadmap | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| How code is written (**binding**) | [docs/02-engineering-conventions.md](docs/02-engineering-conventions.md) |
| How we work, Definition of Done (**binding**) | [docs/03-development-process.md](docs/03-development-process.md) |
| Decisions that belong to the maintainer, open queue | [docs/05-decisions-open.md](docs/05-decisions-open.md) |
| Decisions taken, archive | [docs/06-decisions-taken.md](docs/06-decisions-taken.md) |
| The why of a choice | [docs/adr/](docs/adr/) |
| What is in progress, blockers | [STATUS.md](STATUS.md) |
| Problems found and not fixed | [DEVLOG.md](DEVLOG.md) |
| What the tests cover, and do not | [tests/README.md](tests/README.md) |
| What never enters this repository | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Non-negotiable rules

They apply in every session. The details live in the conventions and the process;
this is the core that is not waived without an ADR.

1. **Interview before implementing.** For a functional change (bug fix, feature,
   non-trivial refactor) **write no code** before presenting: (a) a short
   **diagnosis** of what you understood — file, function, observed behaviour;
   (b) a **plan in 2-4 points**; (c) the **open questions**. Proceed after the
   answers. Exceptions: obvious typos, agreed renames, purely mechanical changes
   already described in detail.

2. **Substantive decisions asynchronously, not on screen.** When a choice that
   belongs to the maintainer comes up (product scope, legal, publication,
   irreversible architecture, a data contract), **do not** use `AskUserQuestion`:
   write a structured entry — *context · options with pros/cons · reasoned
   recommendation* — in [docs/05-decisions-open.md](docs/05-decisions-open.md).
   Meanwhile proceed with the recommendation **only if reversible and low-risk**,
   marked provisional; otherwise pause that part and work elsewhere.
   `AskUserQuestion` stays for **technical micro-clarifications** only. See
   [ADR-0003](docs/adr/0003-async-first-interaction.md).

3. **Non-obvious decisions → ADR.** Every architectural or process choice that is
   costly to undo becomes an ADR in `docs/adr/` (template `0000`). Accepted ADRs
   are **immutable**: minds change with a new ADR that supersedes the old one.
   Where the choice lives in code, a comment `# see ADR-NNNN` makes it findable.

4. **Traceability without duplication.** The same content is not written in
   three places: the **extended why** goes in the **commit body**;
   [CHANGELOG.md](CHANGELOG.md) **indexes** (one slim entry per session, newest
   first); [STATUS.md](STATUS.md) is **live**, not history; [DEVLOG.md](DEVLOG.md)
   collects problems found and **not** fixed.

5. **Register, do not fix on your own initiative.** Weaknesses, latent bugs, code
   smells or dead code outside the task's scope go into DEVLOG, nothing more.
   `grep` DEVLOG and CHANGELOG first: the problem is usually already tracked.

6. **Git.** **Conventional Commits**; frequent **local** commits at every completed
   step, without asking, with the local gates green. **Push, PRs and merges only on
   explicit request.** Never `--amend`, never `git add -A`: selective staging. If a
   hook fails, fix the cause; never `--no-verify`. See
   [ADR-0011](docs/adr/0011-commit-cadence-push-on-request.md).

7. **Verify before saying "done".** After every functional change run `/verify`
   (all deterministic gates in one go). A red gate is fixed **in the code, never by
   bypassing the gate**. On high-risk code — the anti-invention gates, the
   publication boundary, anything writing into a data root — add an
   **adversarial re-read** of the diff.

8. **Tests.** Every **new part** has deep behaviour tests: happy path **+ edges +
   malformed input rejected at the boundary + invariants**. Before "done", run a
   **completeness audit** ("what is NOT covered?") and keep
   [tests/README.md](tests/README.md) honest. A failing test is diagnosed, never
   disabled or rewritten to pass.

9. **Anti-overengineering (binding, amended).** No infrastructure file is built
   before the session in which a user of the framework exercises it end to end.
   **The example user counts as a user**, on one condition: its data is produced
   through the framework's own stages and gates, never hand-written as a fixture.
   *Documented ≠ built*: the roadmap may describe what does not exist yet; the
   repository may not. See [ADR-0008](docs/adr/0008-example-user-is-a-user.md).

10. **Anti-degradation.** Soft caps **~500 lines per module**, **~60 per
    function**: triggers, not limits — when crossed, consider a split before adding
    more. A feature outside a module's responsibility goes into a **new module**.
    No TODOs untracked in DEVLOG, no dead code.

11. **Comments: default none.** Comment **only** the non-obvious *why*: a hidden
    constraint, a workaround, surprising behaviour. Never the *what*, never
    "removed X / added for Y" (that goes in the commit). Docstrings: one concise
    line for the contract.

12. **Documentation in the same commit.** Adding, removing or moving a module, or
    changing the pipeline, a data contract, the CLI or the configuration, updates
    the relevant documents **in the same commit**.

13. **Brutally honest.** Criticise the work — mine and yours — without softening,
    and always include a proposed fix. If a request is wrong, say so before
    executing it; if it is then confirmed, execute it in full.

14. **Never invent facts.** In this codebase that rule has two faces. On the
    engineering side: numbers, APIs, library behaviour are verified or marked
    `TO VERIFY` (greppable). On the product side: no code path and no stage
    instruction ever fabricates a career fact, sets a fact to `verified`, or sets a
    spec to `approved` — those are the user's acts, and **the human gate is
    forever** ([ADR-0001](docs/adr/0001-fact-grounded-profile.md)).

15. **The publication boundary.** Nothing personal enters this repository: no user
    data outside `example/`, no office documents, nothing from the maintainer's
    denylist. Enforced by `tests/test_publication_boundary.py` in the pre-commit
    hook and in CI ([ADR-0009](docs/adr/0009-publication-boundary.md)). Examples
    describe the example persona's world, never a real person's.

16. **English surface, any user language.** Everything in this repository — code,
    messages, docs, stage instructions, skill names — is English. User data is
    never assumed to be English: facts, notes, questionnaires and CVs are in the
    user's languages, driven by `pivot_language` and the labels files
    ([ADR-0007](docs/adr/0007-language-layers.md)).

## Language

- **Everything in this repository is English**: identifiers, prose, commits,
  ADRs, skills, CLI output.
- **User data is locale data**: the framework reads the user's `pivot_language`
  and the target CV language and never leaks its own English into a rendered CV
  or into what it asks a user.

## How we work (the cycle of a change)

Details in [docs/03-development-process.md](docs/03-development-process.md).

0. **Frame** — does it touch a non-obvious decision? ADR first.
1. **Interview** — diagnosis + 2-4 point plan + open questions (rule 1).
2. **Build** the thinnest vertical slice that delivers value, end to end.
3. **Test** the behaviour (rule 8).
4. **Verify** — `/verify`, plus an adversarial re-read on risky code.
5. **Track** — STATUS, CHANGELOG, DEVLOG per rule 4.
6. **Commit** locally (Conventional Commits, why in the body). Push only on request.

## Where an instruction lives

| Where | What goes there |
|---|---|
| **`CLAUDE.md`** (this file) | what applies to **every file** of the project |
| **`.claude/rules/*.md`** with `paths:` | what applies to a **subset of paths**; loaded only when a matching file is opened |
| **`.claude/settings.json`** | what must be **prevented**, not recommended |
| **auto memory** (`/memory`) | facts about **this machine's environment and tools** |

The first two are **context**: Claude reads them and tries to follow them, without
guarantee. The third is **enforced by the client** whatever Claude decides. If
something must never happen, do not write it as a rule here. **Never work state in
auto memory**: it goes in [STATUS.md](STATUS.md), versioned and human-readable.

## Skills

Defined in `.claude/skills/<name>/SKILL.md`:

| Skill | Purpose | Who invokes it |
|---|---|---|
| `/verify` | Run every deterministic gate and report GREEN/RED | you or Claude |
| `/wrap` | Close the session: CHANGELOG + STATUS + grouped commits, with confirmation | only you |
| `/decide` | Open an entry in the asynchronous decision queue (`docs/05`) | only you |
| `/adr` | Create a new numbered ADR from the template | only you |

"Only you" is `disable-model-invocation: true`: they have side effects — they write
documents, propose commits — so they never start on Claude's initiative. The
domain skills (`cv-master`, `job-ingest`, `cv-tailor`, `cover-letter`, and the
placeholders `onboard`, `interview-prep`) are installed into a data root by
`cvac skills install` once the stage contracts exist; see STATUS.md for where
that stands.

Built-in skills this project uses: **`/code-review`** for the adversarial re-read
(fresh context: the author is not the judge), **`/context`** to see what is really
loaded, **`/doctor`** for a configuration check-up.

Project commands (from `.claude/project.conf`):

| Purpose | Command |
|---|---|
| Full verification | `bash .claude/scripts/verify.sh` |
| Tests | `.venv/bin/python -m pytest -q` |
| Lint + format check | `.venv/bin/ruff format --check . && .venv/bin/ruff check .` |
| The tool itself | `.venv/bin/cvac --help` |
| Publication boundary only | `.venv/bin/python -m pytest -q tests/test_publication_boundary.py` |

## Environment

- Any OS: paths are built with `pathlib`, never by concatenating separators;
  CI runs on Linux with Python 3.10 and 3.12.
- Virtual environment `.venv` (`make install`); every command goes through it.
- Repository: `EmanuelePartenza/cv-as-code` (public once v0.1.0 is tagged).
- Git hooks: `git config core.hooksPath .githooks` once per clone.

## Current state

Phase, work in progress and next steps: [STATUS.md](STATUS.md).
