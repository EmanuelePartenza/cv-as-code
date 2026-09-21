# ADR-0012 — Rendering reproducibility: Typst from PyPI, vendored fonts

- **Status**: accepted
- **Date**: 2026-09-22

## Context

The framework promises that the same resolved JSON and the same template give
the same PDF: the frozen JSON is the audit of what was sent, and the PDF must
be recomputable from it. With an external compiler binary and system fonts
that promise was machine-dependent — a different font on another machine, or
no `typst` on PATH, changed or broke the output — and the install story needed
one more step than a Python package.

## Decision

- **The Typst compiler comes from PyPI** (`typst`, pinned to a minor version)
  as a normal dependency: `pip install` is the whole install, in CI too.
- **Fonts are vendored** in the package (Lato, SIL Open Font License 1.1) and
  **system fonts are ignored** at compile time, so glyph coverage and metrics
  are the package's, not the machine's.
- **Rendering happens in a transient `build/` directory** next to the spec:
  Typst cannot import across its root, so the template and the shared lib are
  copied there on every render — the data root's `templates/` overriding the
  package's — together with the resolved JSON and a two-line entry file.
  `build/` is never versioned; the resolved JSON next to the spec remains the
  audit snapshot.
- **A final render stamps the spec's approval date as the PDF's creation
  time**; Typst would otherwise embed the current time, and a re-render of an
  approved CV must be byte-identical. Draft renders keep the current time.

## Consequences

- One install command, no binary, identical PDFs across machines and across the
  Python versions CI runs; a test asserts byte-for-byte reproducibility.
- Cost: the package carries ~1 MB of font files with their licence; a template
  that names another font falls back to Lato unless the data root ships it.
- Known limit: reproducibility holds per pinned `typst` version; a compiler
  upgrade may change output and is treated as a change to review.

## Alternatives considered

- **External `typst` binary on PATH.** One more install step per OS and per
  CI job, and no control over the compiler version a user has.
- **System fonts with fallbacks.** Different machines, different glyphs and
  line breaks; the page budget could pass here and fail there.
- **Copying the templates into every data root.** Would make templates user
  data and leave existing roots without framework fixes; the transient copy at
  render time keeps one source.
