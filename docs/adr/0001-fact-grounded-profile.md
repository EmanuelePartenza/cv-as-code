# ADR-0001 — Fact-grounded profile with provenance and a human gate

- **Status**: accepted
- **Date**: 2026-07-23 (decision made at the framework's design; re-authored for the public repository on 2026-09-22 with the same number and decision)

## Context

CVs generated with LLM assistance carry a structural risk: plausible
embellishment. A user who is employed and searching discreetly, or who will be
asked about every line in an interview, needs each claim to be defensible. The
project's hard rule is therefore "never invent facts", and it has to hold
mechanically where a machine can check it and explicitly where only a person can.

## Decision

- Career facts live only in the user's `profile.yaml` as **atomic, citable
  facts**: an id (`exp-x.fNN`), a claim in the user's pivot language, optional
  real metrics, a `status` of `draft | verified | rejected`, and one or more
  `evidence` pointers to a note or source document.
- `verified` requires the user's **explicit confirmation**. Facts are never
  deleted, only `rejected`.
- Every rendered line of a CV (summary, bullets) cites `source_facts`; the
  validator enforces mechanically that citations exist and that a spec with
  `status: approved` cites only `verified` facts; the resolver refuses a final
  render otherwise.
- Approval itself — setting a spec to `approved`, setting a fact to `verified` —
  is a **human act, forever**. No code path and no stage instruction performs it.

## Consequences

- Invention becomes a mechanical failure, not a judgement call: a bullet without
  a source, or with an unverified one, cannot reach a final PDF.
- Cost: every bullet requires provenance bookkeeping. Sustainable because the
  agent writes the YAML and validation is automated.
- Declared limit: validation is syntactic. Whether a *rewording* is faithful to
  the facts it cites remains with the human gate; the system reduces the
  invention risk drastically, it does not zero it.

## Alternatives considered

- **Free-text CV edited by the LLM, reviewed by the user.** No lineage: a
  reviewer cannot tell which sentence rests on what, and the review degrades
  into proofreading.
- **Facts as free prose per experience.** Not citable: a bullet could rest on a
  paragraph that says several things, some of them unverified.
- **Semantic checking of rewordings by a second model.** Adds a non-deterministic
  judge to a gate that is meant to be deterministic; kept out of the tail on
  purpose. It may become an advisory aid upstream of approval, never the gate.
