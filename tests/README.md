# Tests

`pytest` from the repository root. Fixtures in `conftest.py` build a minimal,
invented data root in a temporary directory: one experience, one project, three
facts at the three statuses, one evidenced skill and one without. No test uses a
real person's data; the publication-boundary test enforces that on the whole
repository.

| File | Covers |
|---|---|
| `test_validate.py` | every rule of `cvac validate`: form, references, evidence paths, labels, the approved ⇒ verified gate; each failing when it should and naming the culprit |
| `test_resolve.py` | the join (dates, organisations, projects split, overrides, education, languages, sections), draft/final modes, both gates, data-root label overrides |
| `test_render.py` | draft watermark and suffix, final without watermark, byte-for-byte reproducibility, the page budget (warn in draft, fail in final), the transient build directory, data-root template overrides |
| `test_letter.py` | frontmatter gate, language-aware date from the labels' months, paragraph collapsing |
| `test_dataroot.py` | flag > env > discovery, error messages, display paths, asset lookup order |
| `test_cli.py` | exit codes 0/1/2, `--data-root` before or after the subcommand, `cvac init` |
| `test_publication_boundary.py` | nothing personal is tracked: structural rules on every tracked file, plus the rules tested on synthetic input |

## What is NOT covered, on purpose

- **Semantic fidelity of a rewording.** Whether a bullet says what its cited
  facts say is the human gate's job; the validator proves citations resolve and
  statuses allow, nothing more (ADR-0001).
- **The LLM stages.** `pipeline/*/INSTRUCTIONS.md` are prompts; tests check their
  `io.yaml` contracts and that `cvac stage pack` assembles them, not what a
  model writes.
- **Typographic overflow.** The page budget is checked after rendering; there is
  no prediction of line breaks.
- **Fonts other than the vendored ones.** System fonts are ignored by design; a
  data-root template that names another font falls back to Lato.
- **Windows paths.** The code uses `pathlib` throughout but CI runs on Linux only.
