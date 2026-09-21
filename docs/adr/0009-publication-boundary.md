# ADR-0009 — Publication boundary: fresh history and a mechanical test

- **Status**: accepted
- **Date**: 2026-09-21

## Context

The framework was extracted from a private repository whose history contains
personal documents, contact details, an employer's internal material and the
names of that employer's clients. Such a history cannot be scrubbed reliably,
and a public portfolio repository that leaks any of it would defeat its
purpose. The boundary between what is published and what is not had to be
defined by construction, not by discipline, and it had to catch not only
structural mistakes (a data directory committed by accident) but strings —
a client's name in a doc example, a phone number in a test fixture.

## Decision

- **The public repository starts with fresh history.** Nothing is imported
  from the private one except code and documents re-authored for publication.
- **A structural test runs everywhere**, in the pre-commit hook and in CI, over
  every tracked file: no `users/` directory outside `example/` and only the
  allow-listed persona inside it; no PDF or office documents; no `interviews/`,
  `sources/` or `inbox/` directories outside the example; no e-mail outside the
  `example.*` domains; no phone-shaped or date-of-birth-shaped strings outside
  the example's reserved fake values.
- **A keyed denylist runs wherever the key exists.** The maintainer keeps a
  plain-text list of private strings outside any repository; its entries are
  hashed with HMAC-SHA256 under a key held locally and as a CI secret, and only
  the digests are committed. Matching normalises text and hashes token n-grams
  and digit runs, so a phone number is caught in any spacing; a hit reports a
  location, never the text. Forks without the key skip this check and keep the
  structural rules.
- **Before the repository goes public, the whole history is scanned**, commit
  messages included; the only history rewrite ever allowed is on a repository
  that has never been pushed, to remove such a hit.
- The test itself lands **before any code** in the repository's history.

## Consequences

- Publishing personal data is a failing test, not an oversight; the repository
  can prove it does not contain what it cannot name.
- Cost: a plain-text list to maintain and a key to keep in two places; false
  positives on short or common words, mitigated by a minimum entry length and
  by reporting `file:line`.
- Known limit: the boundary catches strings and shapes, not stories. An
  anonymised anecdote can still be recognisable; that is the human review's
  job, and the contributing guide says so.

## Alternatives considered

- **Scrubbing the private history** with a filter tool. Not reliably complete,
  and the private repository must keep its history anyway.
- **A plain-text denylist committed to the repository.** Publishes exactly what
  it is meant to protect.
- **Unkeyed hashes of the denylist.** A phone number or a date has too little
  entropy: the hash is reversible by brute force.
- **Discipline and review only.** The first draft of a commit message in this
  very repository named a company from the maintainer's search; the history
  check caught it, review had not.
