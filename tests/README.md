# Tests

`pytest` from the repository root. Fixtures in `conftest.py` build a minimal,
invented data root in a temporary directory: one experience, one project, three
facts at the three statuses, one evidenced skill and one without, a posting, a
match and a letter. No test uses a real person's data; the publication-boundary
test enforces that on the whole repository.

| File | Covers |
|---|---|
| `test_validate.py` | every rule of `cvac validate`: form, references, evidence paths, labels, jobs, matches, letters, evidence notes, questionnaires, the approved ⇒ verified gate; each failing when it should and naming the culprit |
| `test_resolve.py` | the join (dates, organisations, projects split, overrides, education, languages, sections), draft/final modes, both gates, data-root label overrides |
| `test_render.py` | draft watermark and suffix, final without watermark, byte-for-byte reproducibility, the page budget (warn in draft, fail in final), the transient build directory, template overrides, the footer |
| `test_letter.py` | frontmatter gate, language-aware date from the labels' months, paragraph collapsing |
| `test_dataroot.py` | flag > env > discovery, error messages, display paths, asset lookup order |
| `test_stages.py` | every `io.yaml` validates and names a shipped schema; placeholders resolve; `pack` carries instructions, inputs, attachments and the output language; missing inputs and params are named |
| `test_skills.py` | the six domain skills ship with frontmatter, install into a data root, and the repository's copies equal the sources |
| `test_end_to_end.py` | the example data root validates clean, renders three one-page CVs and a letter, packs every stage, and the gates refuse a draft fact in an approved spec and a final render of a draft |
| `test_cli.py` | exit codes 0/1/2, `--data-root` before or after the subcommand, `cvac init` |
| `test_publication_boundary.py` | nothing personal is tracked: structural rules on every tracked file, the keyed denylist where the key exists, plus the rules tested on synthetic input |

## What is NOT covered, on purpose

- **Semantic fidelity of a rewording.** Whether a bullet says what its cited
  facts say is the human gate's job; the validator proves citations resolve and
  statuses allow, nothing more (ADR-0001).
- **What a model writes.** `pipeline/*/INSTRUCTIONS.md` are prompts; tests
  check the contracts and the packs, not an engine's output. The example user
  is the one worked output, and it was reviewed by hand.
- **Typographic overflow.** The page budget is checked after rendering; there
  is no prediction of line breaks.
- **Fonts other than the vendored ones.** System fonts are ignored by design; a
  data-root template that names another font falls back to Lato.
- **Windows paths.** The code uses `pathlib` throughout but CI runs on Linux only.
- **Typst's exception type on a compile error** (DEVLOG 2.1).
