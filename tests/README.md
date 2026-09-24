# Tests

`pytest` from the repository root. Fixtures in `conftest.py` build a minimal,
invented data root in a temporary directory: one experience, one project, three
facts at the three statuses, one evidenced skill and one without, a posting, a
match and a letter. No test uses a real person's data; the publication-boundary
test enforces that on the whole repository.

| File | Covers |
|---|---|
| `test_validate.py` | every rule of `cvac validate`: form, references, evidence paths, labels, jobs, matches, letters, evidence notes, questionnaires, the approved ⇒ verified gate; each failing when it should and naming the culprit |
| `test_resolve.py` | the join (dates, organisations, projects split, overrides, education, languages, sections), draft/final modes, both gates, data-root label overrides, identity fields (labels default, spec override, date of birth formatted, born without a label refused) |
| `test_render.py` | draft watermark and suffix, final without watermark, byte-for-byte reproducibility, the page budget (warn in draft, fail in final), the transient build directory, template overrides, the footer, the date of birth printed only when shown |
| `test_letter.py` | frontmatter gate, language-aware date from the labels' months, paragraph collapsing, the header follows the labels' identity fields |
| `test_dataroot.py` | flag > env > discovery, error messages, display paths, asset lookup order |
| `test_stages.py` | every `io.yaml` validates and names a shipped schema; placeholders resolve; `pack` carries instructions, inputs, attachments and the output language; missing inputs and params are named; `04_apply` targets the profile |
| `test_skills.py` | the seven domain skills ship with frontmatter, install into a data root, and the repository's copies equal the sources |
| `test_runner.py` | `cvac stage run` with a fake `claude` executable: the prompt is the pack plus the engine note, the command confines the engine, success only when the output exists and validates, engine errors and exit codes surface, the executable is found or the message says how to install it; a deterministic stage runs with no engine at all |
| `test_triage.py` | documents read together: a directory input lists and packs every document, the sources index and each of its rules, apply and archive keeping the index true (moved paths, duplicates, context, notes), the sort → extract → apply → archive run extracting only the evidence, sort alone, a run may not start with a code step |
| `test_guided.py` | the guided path: rewording a fact (verified goes back to draft, folded claims), archiving an applied document, several uploads at once with bad ones named, extraction chained to apply with the archive, extract-all over the pending inbox, the review page (quotes, confirm and reject selected, reword), the questionnaire form (byte-identical round trip of Robin's and the skeleton, answers in sittings, repeated positions, filled and reopened), the start page's doors |
| `test_ui_i18n.py` | the four UI languages: every catalog covers every chrome string and nothing else, placeholders preserved; negotiation from the browser, the header choice persisted, library messages left English; the chooser's folder browser (hidden folders skipped, data roots marked, create here, new folder, refusals); German CV labels |
| `test_apply.py` | stage 04 as code: facts appended as draft with continued ids on both list layouts, new parents, empty lists of a scaffolded profile, duplicates skipped, every refusal leaves the profile untouched, a result that would not validate is not written, search parameters pointed out and never written |
| `test_scaffold.py` | a new data root and a new user: valid from the first file, default user set once, never overwriting |
| `test_end_to_end.py` | the example data root validates clean, renders three one-page CVs and a letter, packs every stage, and the gates refuse a draft fact in an approved spec and a final render of a draft |
| `test_data_in.py` | the profile report (sections, counts, completeness checklist) and `cvac fact verify\|reject` (only the status lines change, unknown ids and facts without evidence refused) |
| `test_cli.py` | exit codes 0/1/2, `--data-root` before or after the subcommand, `cvac init` |
| `test_specs.py` | approval of a spec or a letter: only `status` and `approved_on` change, a trailing comment survives, refused through the validator (draft cited fact, twice, wrong kind, no frontmatter) |
| `test_ui.py` | the local UI (skipped without the `ui` extra): pages on the fixture and on Robin, evidence quotes, verify/reject/approve/render buttons with the CLI's refusals, PDF preview, 404 on unknown or traversal paths, the missing-extra message; the chooser (redirect, open, create only when asked), the new-user form, postings saved verbatim and never overwritten, stage runs from a job page with the fake engine and their log page, uploads (type-checked), extraction and questionnaire runs, the editor saving only what validates, binary inputs in a pack |
| `test_publication_boundary.py` | nothing personal is tracked: structural rules on every tracked file, the keyed denylist where the key exists, plus the rules tested on synthetic input |

## What is NOT covered, on purpose

- **Semantic fidelity of a rewording.** Whether a bullet says what its cited
  facts say is the human gate's job; the validator proves citations resolve and
  statuses allow, nothing more (ADR-0001).
- **What a model writes.** `pipeline/*/INSTRUCTIONS.md` are prompts; tests
  check the contracts and the packs, not an engine's output. The example user
  is the one worked output, and it was reviewed by hand. `cvac stage run` is
  tested with a fake engine; the real Claude Code binary is exercised by hand.
- **Typographic overflow.** The page budget is checked after rendering; there
  is no prediction of line breaks.
- **Fonts other than the vendored ones.** System fonts are ignored by design; a
  data-root template that names another font falls back to Lato.
- **Windows paths.** The code uses `pathlib` throughout but CI runs on Linux only.
- **Typst's exception type on a compile error** (DEVLOG 2.1).
