# Development process

> **How** we work on this project, change after change. Complementary to
> [02-engineering-conventions.md](02-engineering-conventions.md) (the *with
> what*). Binding like the conventions: deviations go in an ADR.

## 1. Principles

1. **Vertical slices, not horizontal layers.** Build the thinnest end-to-end
   slice that delivers value — a real use case from input to output — not "all the
   schemas, then all the logic, then all the CLI".
2. **Domain first, infrastructure last.** Start from the pure logic (the join, the
   gate, the rule), wrap it in a command, and only then connect it to files, the
   compiler, the hooks.
3. **Anti-overengineering, amended.** No infrastructure file is built before the
   session in which a user of the framework exercises it end to end; the example
   user counts as a user when its data goes through the framework's own stages
   ([ADR-0008](adr/0008-example-user-is-a-user.md)). *Documented ≠ built*: the
   roadmap may describe what does not exist yet; the repository may not, and the
   README may not claim it.
4. **Every decision leaves a trace.** Non-obvious choice → ADR; the slice cites
   the ADRs it embodies.
5. **Ask before writing.** The pre-implementation interview (§ 2, step 1) is not a
   courtesy: it is what avoids redoing the work.

## 2. The cycle of a change

0. **Frame.** What is the slice? Does it touch a non-obvious decision? ADR first.
   Does it change a data contract? Schema and validator first, with their tests.
1. **Interview.** Short diagnosis (file, function, observed behaviour) + plan in
   2-4 points + open questions. Proceed after the answers. Exceptions: obvious
   typos, agreed renames, mechanical changes already described in detail.
2. **Define the slice**, end to end, with observable input and output.
3. **Build the core** with the behaviour tests in front.
4. **Connect the infrastructure** only when it is really needed (§ 3).
5. **Verify.** `/verify` for the deterministic gates; adversarial re-read of the
   diff on high-risk code.
6. **Track.** STATUS, CHANGELOG, DEVLOG under the no-duplication rule.
7. **Commit** locally. Push, PRs and merges only on explicit request.

## 3. When a file, when a command, when an external service

- **A new document kind → when a stage needs to read or write it**, not before.
  Until then the information lives in an existing document.
- **A CLI subcommand → after** the underlying function is covered by tests and
  holds. The command is a thin layer that translates arguments into a call:
  **never rules in the CLI**.
- **An LLM engine → always behind the file contract** (`INSTRUCTIONS.md` +
  `io.yaml`, [ADR-0002](adr/0002-file-contract-llm-stages.md)). The framework never
  calls a model; it prepares inputs and validates outputs.
- **A backup, a connector, a runner → behind an interface and a documented manual
  path**, added when a user needs it.

## 4. Definition of Done

A change is "done" when:

- [ ] **Gates green** — `bash .claude/scripts/verify.sh` is GREEN.
- [ ] **Deep behaviour tests**, not only the happy path: **edges** (zero, empty,
      one, many, duplicates) **+ malformed input rejected at the boundary** (never
      a technical exception escaping) **+ invariants** **+ data preservation**
      end to end (exact shape of the resolved JSON: expected keys, optionals
      present).
- [ ] **Test completeness audit** done: you asked explicitly *what is not
      covered* and filled the real holes; `tests/README.md` updated if the answer
      changed.
- [ ] **Adversarial re-read** of the diff if the code is high-risk (the
      anti-invention gates, the publication boundary, writes into a data root).
- [ ] **Boundaries respected**: no unplanned cross-module import; user data only
      through `DataRoot`; nothing personal in the repository.
- [ ] **Anti-degradation**: sizes within the triggers, no untracked TODO, no dead
      code.
- [ ] **Decisions**: non-obvious choice → ADR; `# see ADR-NNNN` in the code.
- [ ] **Documentation in the same commit**: ARCHITECTURE, README, CONTRIBUTING or
      the schemas' descriptions, as applicable. **A README claim is backed by a
      test or a command that a stranger can run**; otherwise it is worded as
      roadmap or removed.
- [ ] **Tracking**: CHANGELOG entry (unless cosmetic), STATUS updated, out-of-scope
      problems in DEVLOG.
- [ ] **Conventional Commit** with the why in the body.

## 5. Verification

`/verify` runs in one go the deterministic gates declared in
`.claude/project.conf` and reports GREEN/RED. A red gate is fixed **in the code,
not by bypassing the gate**; if the gate itself is wrong, that is a decision to
open, not to take on one's own.

The gates say the tests *pass*, not that they are *sufficient*: hence the
completeness audit in the DoD. On high-risk code add the adversarial re-read —
invariants, edge cases, boundaries, malformed input, wide `except`s — actively
looking for the defect, not for confirmation. `/code-review` does this in a fresh
context, which is the point: the reasoning that wrote the code is the worst judge
of it.

## 6. Decisions: who decides what

| Kind of choice | Who | How |
|---|---|---|
| Local, reversible implementation | Claude | Proceeds, records it in the commit |
| Technical micro-clarification | Maintainer | `AskUserQuestion`, immediately |
| Architecture, process, convention | Together | ADR in `docs/adr/` |
| Product scope, legal, publication, irreversible | Maintainer | Entry in [05-decisions-open.md](05-decisions-open.md) |

For the last row the asynchronous workflow of
[ADR-0003](adr/0003-async-first-interaction.md) applies: **no interview on
screen**. Claude writes context, options with pros and cons, and a
recommendation; the maintainer answers in the document. Meanwhile Claude proceeds
with the recommendation **only if reversible and low-risk** (marked provisional),
otherwise pauses that slice and works elsewhere. Once taken **and implemented**,
the entry moves to [06-decisions-taken.md](06-decisions-taken.md).

## 7. Roles

- **Maintainer** — decides (ADRs and the decision queue), reviews, owns the
  publication boundary and the keyed denylist.
- **Claude Code** — driver: proposes slices, interviews before implementing,
  writes code and tests, runs verification and the adversarial re-read, keeps
  the tracking files current.
- **Verification engine** — deterministic gates in one command.
- **Users of the framework** — never present in this repository: their data lives
  in their own data roots. The example user stands in for them.

---
*This process changes with a new ADR, like the [conventions](02-engineering-conventions.md).*
