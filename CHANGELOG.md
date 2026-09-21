# CHANGELOG — cv-as-code

Chronological index of changes. **New entries go at the top.** This file
**indexes, it does not explain**: the extended why lives in the commit body
(`git show <hash>`). At most 5-8 bullets per entry.

**When no entry is written**: purely cosmetic changes (renames, formatting, type
hints). The commit is enough.

Tags: `arch`, `perf`, `ui`, `test`, `docs`, `fix`, `cleanup`, `sec`.

---

## 2026-09-22

### feat(example): Robin Ashcombe, a complete data root through the stages [arch, test]

- `example/`: a fictional lighthouse keeper applying for a port role; questionnaire
  filled, evidence note extracted, profile with facts at the three statuses,
  search, English and French masters, posting, `stretch` match, tailored
  application, letter — all approved by the persona, all rendered on one page.
- `tests/test_end_to_end.py`: the example validates clean, renders, packs every
  stage, and the gates refuse a draft fact in an approved spec and a final
  render of a draft.
- CI builds the four PDFs on Python 3.10 and 3.12, uploads them, and a final job
  proves they are byte-identical across versions.
- Files: `example/`, `tests/test_end_to_end.py`, `.github/workflows/ci.yml`.

### feat(stages): stage contracts, job/match/letter schemas, cvac stage [arch]

- `pipeline/10_normalize`, `20_match`, `30_tailor`, `60_letter`: `INSTRUCTIONS.md`
  + `io.yaml`, validated by `stage-io.schema.json`; gates declared.
- Schemas `job`, `match`, `cover-letter`; the validator checks postings
  (id = directory, `raw.txt` present), matches (strengths cite facts, job
  exists) and letters (frontmatter, source facts, approved ⇒ verified).
- `cvac stage list|show|pack`: the manual path for any chat, documented in
  `docs/manual-path.md`; `pack` states the output language from the profile.
- `documents.py` reads YAML and markdown-with-frontmatter documents.
- Files: `src/cv_as_code/pipeline/`, `schemas/`, `stages.py`, `validate.py`,
  `tests/test_stages.py`.

### docs: navigator, status, conventions, process, decision queues and ADRs [docs]

- `CLAUDE.md` rewritten as a navigator with the sixteen non-negotiable rules;
  `STATUS.md` live, `DEVLOG.md` with four open items.
- `docs/02-engineering-conventions.md`, `docs/03-development-process.md`
  (binding), `docs/05-decisions-open.md`, `docs/06-decisions-taken.md`.
- ADRs 0001-0003 and 0005 re-authored with their original numbers, 0004
  reserved, 0006-0012 new (split, language layers, amended rule, boundary,
  docs home, commit cadence, rendering reproducibility).
- `docs/ARCHITECTURE.md` describing what exists, with status columns and a
  separate roadmap.
- Files: `CLAUDE.md`, `STATUS.md`, `DEVLOG.md`, `docs/`.

### chore(process): verification engine, git hooks, settings and process skills [docs, sec]

- `.claude/scripts/verify.sh` runs every gate declared in `.claude/project.conf`
  and prints GREEN/RED; `check_doc_drift.py`, `refresh_status.py`,
  `propose_commit.py` alongside.
- Git hooks: pre-commit (secrets, publication boundary, doc drift, quick gates),
  commit-msg (Conventional Commits), post-commit (STATUS refresh).
- `.claude/settings.json` denies push, amend, blanket staging and `--no-verify`
  to the agent; `record-edit.sh` logs the session's edits.
- Skills `/verify`, `/wrap`, `/decide`, `/adr`; Python rules loaded on `.py` files.
- Files: `.claude/`, `.githooks/`.

### feat(boundary): keyed denylist, pre-commit hook, history check [sec, test]

- `scripts/denylist.py`: seed from a profile, build HMAC digests, check files,
  stdin or the whole git history (commit messages included).
- `tests/data/denylist.hmac` committed; key local and as the `CVAC_DENYLIST_KEY`
  CI secret; forks without the key skip only that check.
- Numeric entries match by digit string only; hits print a location, never text.
- `CONTRIBUTING.md`: what never enters this repository.
- Files: `scripts/denylist.py`, `tests/test_publication_boundary.py`,
  `.githooks/pre-commit`, `CONTRIBUTING.md`.

### test: behaviour suite for validate, resolve, render, letter, data root and CLI; CI workflow [test]

- 92 tests on an invented minimal data root; every anti-invention rule fails on
  demand and names the culprit; resolver join pinned field by field.
- Render: draft watermark and suffix, page budget, transient `build/`, template
  overrides, byte-for-byte reproducibility (final PDFs stamp the approval date).
- `cvac validate` usage error exits 2; GitHub Actions on Python 3.10 and 3.12.
- Files: `tests/`, `.github/workflows/ci.yml`, `README.md` (badge).

### feat(cli): cvac command with data-root discovery and the ported pipeline [arch]

- Package `cv_as_code` with `cvac init|validate|resolve|render|cv|letter`.
- Data root marked by `cvac.yaml` (flag > env > upward discovery); `i18n/` and
  `templates/` overrides in the data root win over the package's.
- Typst from PyPI, Lato vendored (OFL), system fonts ignored; transient `build/`.
- Labels carry `kind`, `date_format`, month names, validated by a schema; the
  validator checks evidence paths, labels for the spec language, templates.
- Files: `src/cv_as_code/`, `pyproject.toml`.

### chore: repository bootstrap with licence, packaging and the publication boundary test [docs, sec]

- MIT licence, `pyproject.toml`, README stub, `.gitignore`, `Makefile`.
- Structural publication-boundary test committed before any code.
- Files: `LICENSE`, `pyproject.toml`, `tests/test_publication_boundary.py`.
