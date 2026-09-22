# Architecture

What exists, how it fits together, and — separately, at the end — what is
roadmap. Rule zero: *documented ≠ built*. Every section before §10 describes
the repository as it is; §10 describes what it is not yet.

## 1. Principles

1. **One source of truth per entity.** Career facts live only in a user's
   `profile.yaml`; everything else (specs, resolved JSON, PDFs) is derived.
2. **Facts are atomic and citable** ([ADR-0001](adr/0001-fact-grounded-profile.md)):
   an id, a claim in the user's pivot language, optional real metrics, a status
   (`draft | verified | rejected`) and evidence pointers. `verified` requires the
   user's explicit confirmation; facts are never deleted, only rejected.
3. **Anti-invention is mechanical where possible, human where not.** The
   validator proves that every rendered line cites existing facts and that an
   approved spec cites only verified ones; the resolver refuses a final render
   otherwise. Whether a rewording is *faithful* stays with the human gate.
4. **The human gate is forever.** No code path and no stage instruction sets a
   fact to `verified` or a spec to `approved`.
5. **Deterministic tail.** From approved spec to PDF everything is plain Python
   + Typst; intelligence lives only in the LLM stages, upstream of approval, and
   is swappable ([ADR-0002](adr/0002-file-contract-llm-stages.md)).
6. **Framework and data are separate by construction**
   ([ADR-0006](adr/0006-code-data-split-and-data-root.md)): the framework is a
   package, a user's data is a data root it never contains.
7. **English surface, any user language**
   ([ADR-0007](adr/0007-language-layers.md)).

## 2. Layout

The package:

```
src/cv_as_code/
├── cli.py          cvac: init · validate · resolve · render · cv · letter · stage · skills · profile · fact
├── dataroot.py     the data-root contract: location, user paths, asset lookup with overrides
├── validate.py     form (JSON Schema) + references + evidence paths + the approval gate
├── resolve.py      profile × cv-spec × labels → cv.resolved.json (draft/final modes)
├── render.py       resolved JSON → PDF via Typst in a transient build/ directory
├── letter.py       letter.md × profile × labels → PDF in the CV's style
├── stages.py       stage contracts: list, resolve against a data root, pack for any engine
├── skills.py       the Claude Code adapter: `cvac skills install` copies skills/ into a data root
├── report.py       `cvac profile report`: a generated Markdown view with a completeness checklist
├── facts.py        `cvac fact verify|reject`: the human gate on facts, layout-preserving
├── documents.py    YAML and markdown-with-frontmatter documents; dates normalised to strings
├── errors.py       CvacError > ValidationError, RenderError
├── schemas/        profile · search · cv-spec · cv-resolved · labels · data-root · job · match ·
│                   cover-letter · evidence · questionnaire · stage-io
├── pipeline/       03_extract · 05_interview · 10_normalize · 20_match · 30_tailor · 60_letter
│                   (INSTRUCTIONS.md + io.yaml each; 05 also ships the questionnaire skeleton)
├── skills/         cv-master · job-ingest · cv-tailor · cover-letter · onboard · interview-prep
├── i18n/           labels.it.yaml · labels.fr.yaml · labels.en.yaml
└── templates/      classic/{template,letter}.typ · lib/common.typ · fonts/ (Lato, OFL)
```

`example/` is a complete data root — the fictional user Robin Ashcombe, produced
through the stages above — and CI renders it on every push. A data root
(created by `cvac init`; the framework reads and writes nothing outside one):

```
<data root>/
├── cvac.yaml                  kind: data-root · schema_version · default_user
├── users/<slug>/
│   ├── profile.yaml           facts (source of truth)
│   ├── search.yaml            target roles, markets, constraints
│   ├── notes/  sources/       evidence cited by facts · original documents
│   ├── interviews/  inbox/    questionnaires · raw drops for extraction (gitignored)
│   ├── masters/<name>/        cv-spec.yaml · cv.resolved.json · the PDF · build/ (transient)
│   ├── applications/<job_id>/ cv-spec.yaml · letter.md · resolved JSON · PDFs
│   └── matches/               match verdicts (see §4)
├── jobs/<job_id>/             raw.txt verbatim · job.yaml normalised (see §4)
├── i18n/  templates/          optional overrides of the package's labels and templates
```

## 3. Data model

Every YAML document carries `kind` and `schema_version` (integer, bumped only
on a breaking change); JSON only for the resolved render input. Ids are
kebab-case (`exp-acme`, `edu-uni`, `skill-sql`); fact ids are `<parent>.fNN`;
dates are quoted ISO strings, `null` meaning ongoing or unknown, never inferred.
Tags and categories are free-form: matching is semantic, on the LLM side.

| kind | file | status | notes |
|---|---|---|---|
| `profile` | `users/<u>/profile.yaml` | built | facts with status and evidence; skills point to `evidence_facts` |
| `search` | `users/<u>/search.yaml` | built | target roles, markets and modes, salary floor, `confidential` |
| `cv-spec` | masters and applications | built | a master is a cv-spec with `job_id: null`; `based_on` is provenance only (copy, never merge); optional `footer` |
| `cv-resolved` | `cv.resolved.json` | built | the generator ↔ template contract: no ids, no refs, final display text |
| `labels` | `i18n/labels.<lang>.yaml` | built | headings, "present", date format, month names, language and level names |
| `data-root` | `cvac.yaml` | built | the marker and contract of a data root |
| `job` | `jobs/<id>/job.yaml` | built | normalised posting; requirements quoted verbatim, never paraphrased |
| `match` | `users/<u>/matches/<id>.yaml` | built | `verdict: apply \| stretch \| skip`, strengths with fact refs, gaps, angle; no numeric score |
| `cover-letter` | frontmatter of `letter.md` | built | `source_facts`, status, approval date |
| `evidence` | frontmatter of `notes/<name>.md` | built | facts proposed by `03_extract`, each with the verbatim passage it rests on |
| `questionnaire` | frontmatter of `interviews/<name>.md` | built | the profile interview of `05_interview`; the body is free text |

Every kind above is validated by `cvac validate`; a markdown document
(`letter.md`) is validated through its YAML frontmatter.

## 4. Pipeline

```
posting (text)
  │ [00 ingest]     manual: jobs/<id>/raw.txt verbatim, immutable by convention
  ▼ [10 normalize]  LLM → job.yaml → validate
  ▼ [20 match]      LLM → matches/<id>.yaml → validate; verdict skip ⇒ stop (match kept)
  ▼ [30 tailor]     LLM → applications/<id>/cv-spec.yaml (draft) → validate → DRAFT preview
  ▼ [HUMAN GATE]    explicit approval → status: approved
  ▼ resolve         deterministic, --mode final: fails on a broken ref, an unverified fact,
  │                 a non-approved spec, a missing label
  ▼ render          deterministic: Typst → clean PDF; page budget checked
  ▼ [60 letter]     LLM (optional) → letter.md with source_facts → human gate → render
  ▼ [70 prep]       LLM, at a real interview → interview-prep.md, internal (ADR-0005)
```

Upstream of the profile, two more stages bring data *in*: `03_extract` (a
document or a filled questionnaire → draft facts + an evidence note) and
`05_interview` (profile + search → a questionnaire in the user's language, only
the missing items in update mode). Facts always enter as `draft`; `cvac fact
verify|reject` is the gate and `cvac profile report` the view
([data-in.md](data-in.md), [ADR-0013](adr/0013-data-in.md)).

An LLM stage is a directory `pipeline/<NN_name>/` with `INSTRUCTIONS.md` (the
prompt: inputs, outputs, rules; it never names an engine) and `io.yaml` (the
contract: inputs with placeholders, output path and schema, `gate`, output
language). Three engines consume the same files: a Claude Code skill in
session, `cvac stage pack` for any chat (paste the bundle, paste the answer
back, validate — see [manual-path.md](manual-path.md)), and an API runner
(roadmap). `cvac stage list` and `cvac stage show` print the contracts
resolved against a data root.

| Stage | Gate | Status |
|---|---|---|
| `03_extract` | none (facts land as draft) | built; exercised by the example |
| `05_interview` | none | built; exercised by the example |
| `10_normalize` | none | built |
| `20_match` | none | built |
| `30_tailor` | human | built |
| `60_letter` | human | built |
| `70_interview_prep` | none (internal) | roadmap, at a user's first interview |

Deterministic today: `resolve` (draft: any facts, stamps `meta.draft`; final:
approved spec, verified facts), `render` (DRAFT watermark and `-DRAFT` suffix
from the resolved flag; `max_pages` warns in draft, fails in final), `letter`.

Idempotence: `raw.txt` is immutable by convention; 10 re-runs overwrite the
normalised posting; 20 and 30 re-run while the spec is `draft`; after an
application is sent its artefacts are frozen by convention and commit
discipline, and `cv.resolved.json` is never re-diffed against the current
profile — it is the snapshot of what was sent.

## 5. Skills

Thin orchestrators in `.claude/skills/`: they sequence commands and stage
contracts, they never duplicate a stage's rules.

| Skill | Status | What it does |
|---|---|---|
| `/verify`, `/wrap`, `/decide`, `/adr` | built | the working method (gates, session close, decision queue, ADRs) |
| `cv-master`, `job-ingest`, `cv-tailor`, `cover-letter` | built | run a stage through `cvac stage show`, preview, ask for the gate, render |
| `onboard`, `interview-prep` | built as written procedures | scaffold + interview + extraction + verification; the preparation document (ADR-0005) by hand until stage 70 exists |

Domain skills ship in the package (`src/cv_as_code/skills/`) and are installed
into a data root by `cvac skills install`, because Claude Code loads skills from
the project it is opened in; the copies under this repository's `.claude/skills/`
are kept identical to the sources by a test.

## 6. Templates and rendering

- One template = one directory exporting `cv(data)` (and `letter(data)`);
  `data` is the resolved JSON; its schema is the generator ↔ template contract.
  New template = new directory, zero script changes; a data root's
  `templates/<name>/` overrides the package's.
- **Zero language strings in templates**: labels arrive resolved in the JSON.
- Rendering happens in a transient `build/` next to the spec (template copy,
  lib, JSON, a two-line entry file), with the package's vendored fonts and
  system fonts ignored; a final render stamps the approval date as creation
  time, so re-rendering an approved CV is byte-identical
  ([ADR-0012](adr/0012-rendering-reproducibility.md)).
- Known weak point: the resolver cannot predict typographic overflow; the page
  budget is checked after rendering, and the fix is an edit-spec/re-render loop.

## 7. Postings

Postings enter by hand: paste the text into `jobs/<id>/raw.txt` first (postings
disappear), then stage 10. There is **no scraping of platforms that forbid it**,
and no browser automation of any kind. Job ids are
`YYYYMMDD-<company-slug>-<role-slug>`; deduplication is by eye until a
connector exists (roadmap).

## 8. The split

The framework is a package; a user's data is a data root
([ADR-0006](adr/0006-code-data-split-and-data-root.md)). One copy of the code:
the maintainer's own data repository contains none and refuses it in a hook.
Nothing personal enters this repository, by test
([ADR-0009](adr/0009-publication-boundary.md)); the example data root under
`example/` stands in for every user and is produced through the framework's
own stages ([ADR-0008](adr/0008-example-user-is-a-user.md)).

## 9. Declared limits

1. Semantic fidelity of rewordings is human-gated, not machine-proven.
2. Multi-user is designed in (`users/<slug>/`) and exercised with the example
   and the maintainer; not with a team.
3. File-based storage: right for one person and hundreds of postings; a
   database would be a new ADR.
4. LLM stages are non-deterministic upstream of approval, by design.
5. The page-overflow feedback loop is manual.
6. Immutability of `raw.txt` and of sent applications is convention, not
   enforcement.
7. No automated ATS text-extraction check of the PDF.

## 10. Roadmap

Each line is roadmap: designed or intended, not built, and not claimed in the
README.

- `cvac stage run` — an API runner consuming the same stage contracts.
- `40_gap_plan` — from a match's declared gaps, an internal plan whose
  deliverables are evidence, never facts; built at a user's first real use.
- `70_interview_prep` — the stage of ADR-0005, at a user's first interview.
- Connectors for posting aggregators with public APIs; `dedup_key`.
- Application tracking (`application.yaml`, a generated index).
- `i18n/markets/` — market conventions beyond language (photo, date of birth).
- A deterministic `apply` of an evidence note into the profile (needs a
  format-preserving YAML writer); an HTML view of the profile report; a photo
  asset for markets that expect one.
- PyPI release; Claude Code plugin packaging of the skills.
- A CI job on Windows.
