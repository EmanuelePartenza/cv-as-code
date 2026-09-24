# ADR-0015 — Claude Code in print mode as the first engine that runs a stage

- **Status**: accepted
- **Date**: 2026-09-24

## Context

A stage is a file contract ([ADR-0002](0002-file-contract-llm-stages.md)):
`INSTRUCTIONS.md` and `io.yaml`, consumed by any engine. Two engines existed —
a Claude Code session with the skills, and any chat through `cvac stage pack` —
and both need a person in the loop to carry text around. The maintainer wants
the UI to *run* a stage: drop a posting, press a button, get a draft to
review. That needs an engine the tool can call. The candidates: Claude Code's
non-interactive print mode (`claude -p`), which uses the login the person
already has and runs with tools inside a working directory; the Claude Agent
SDK, a Python wrapper that still requires the `claude` executable; the API
directly, which needs a key, per-token billing and a tool loop of our own.
Verified against the Claude Code documentation on 2026-09-24: print mode
accepts `--output-format stream-json`, `--permission-mode`, `--allowedTools`,
`--disallowedTools`, `--max-turns`, `--max-budget-usd`, `--add-dir`, reads a
prompt from stdin, uses the subscription login without an API key, and loads
the working directory's `CLAUDE.md` and skills unless `--bare` is given.

## Decision

- **`cvac stage run <stage> …` runs a stage with an engine; the first engine
  is Claude Code in print mode**, spawned as a subprocess with the data root
  as working directory. The prompt is the same bundle `cvac stage pack`
  produces, followed by an engine note (write the output with your tools,
  validate it, touch nothing else, never set `approved` or `verified`).
- **Confined by construction, not by trust**: `--permission-mode acceptEdits`,
  an allow-list of tools (read, search, write and edit files; `cvac validate`
  and `cvac stage`), git and the web denied, a turn cap and an optional spend
  cap, `--add-dir` limited to the data root. The run's stream is written to a
  log under the user's cache directory, never into the data root.
- **The result is checked, not believed**: a run succeeds only if the output
  file exists and validates; the validator's verdict is the run's verdict.
  The human gate is untouched: a stage with `gate: human` produces a draft,
  and approval stays a button or a command.
- **The executable is found, never bundled**: `CVAC_CLAUDE_BIN`, then `claude`
  on `PATH`, then the binary shipped with the Claude Code VS Code extension as
  a last resort; when none exists the message says how to install it.
- **Engine-agnostic stays true**: the runner takes an engine name; the API
  runner remains roadmap and would plug into the same command.

## Consequences

- A person with Claude Code installed runs every stage from the UI or the
  terminal with their own login; there is no key to manage and no second
  billing relationship.
- Cost: each run spends the person's Claude usage; the log shows the reported
  cost when the engine reports one.
- The engine runs the stage with tools inside the data root: it can read
  every file there. That is what the skills already do in session; the
  allow-list keeps it from reaching git or the network.
- Print mode does not answer permission prompts: a tool outside the allow-list
  is denied, which surfaces in the log as a failed run rather than a hang.
- Tests use a fake `claude` executable through `CVAC_CLAUDE_BIN`; the real
  engine is exercised on the example user by hand and by the maintainer.

## Alternatives considered

- **The Agent SDK.** Cleaner streaming, but a new dependency that still wraps
  the same executable; the subprocess gives the same events as JSON lines.
- **The Anthropic API directly.** Requires a key and a tool loop of our own;
  kept as the roadmap runner for people without Claude Code.
- **`--dangerously-skip-permissions`.** Never: the allow-list plus
  `acceptEdits` covers what a stage needs.
