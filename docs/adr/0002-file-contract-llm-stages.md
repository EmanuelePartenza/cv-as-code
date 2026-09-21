# ADR-0002 — File-contract LLM stages, three engines

- **Status**: accepted
- **Date**: 2026-07-23 (re-authored for the public repository on 2026-09-22 with the same number and decision, widened to name the engines)

## Context

The framework must work today with an agent working in a session over the
user's files, without an application to run, and it must be usable by other
people with other engines — a web chat, another agent, a programmatic API
call — without restructuring anything. The intelligent steps (normalising a
posting, judging a match, drafting a spec, writing a letter) are the only
non-deterministic part of the system; everything after approval must stay
deterministic.

## Decision

- An intelligent step is a **stage**: a directory under `pipeline/` with two
  files. `INSTRUCTIONS.md` is the prompt — it speaks only of inputs, outputs and
  rules, and never names an engine. `io.yaml` is the machine-readable contract:
  inputs (paths with placeholders), output path and schema, `gate: human|none`,
  the language the output must be written in.
- Three engines consume the same two files and nothing else changes: a **Claude
  Code skill** that reads the contract and works in session; **`cvac stage
  pack`**, which assembles instructions and inputs into one document a person
  pastes into any chat, then pastes the answer back and validates; and an **API
  runner** (roadmap) that builds the same call programmatically.
- The tail is deterministic Python + Typst (`resolve`, `render`, `letter`):
  intelligence never touches it, and a stage never sets `approved`.

## Consequences

- The LLM attachment point is a file contract: engines are swappable and the
  framework has no dependency on any model or vendor.
- LLM stages are non-deterministic upstream of approval, accepted by design;
  reproducibility is guaranteed downstream by the frozen resolved JSON.
- Known limit: a stage's *quality* depends on the engine; the contract fixes
  what is asked and how the answer is checked, not how well it is answered.

## Alternatives considered

- **Code that calls a model directly.** Ties the framework to a vendor and an
  API shape, and makes the in-session and web-chat uses second-class.
- **Prompts embedded in the skills.** Claude-Code-only; the same prompt would
  have to be copied for every other engine.
- **A workflow engine with typed steps.** Heavier than the problem: four stages
  and a human gate do not need an orchestrator.
