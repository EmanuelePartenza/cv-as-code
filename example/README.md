# Example data root — Robin Ashcombe

Robin Ashcombe is fictional: a lighthouse keeper on the (fictional) island of
Skerra applying for a Port Operations Officer post at the (fictional) Port of
Saltmere. Every file here was produced through the framework's own stages, as
a user's would be ([ADR-0008](../docs/adr/0008-example-user-is-a-user.md)); it
is a complete data root, so anything `cvac` does, it does here.

```bash
cd example
cvac validate --all                                     # 0 errors, 0 warnings
cvac cv users/robin/masters/port-operations-en --mode final
cvac cv users/robin/masters/port-operations-fr --mode final
cvac cv users/robin/applications/20260915-saltmere-port-operations-officer --mode final
cvac letter users/robin/applications/20260915-saltmere-port-operations-officer
```

PDFs are never committed; CI builds them as artefacts on every push.

## What each file demonstrates

| File | Stage | Shows |
|---|---|---|
| `users/robin/interviews/01-onboarding.md` | `05_interview`, filled by Robin | the standard questionnaire; answers in the user's own words, with a number Robin refuses to guess and one Robin retracts |
| `users/robin/notes/01-onboarding.md` | `03_extract` | an evidence note: every proposed fact with the verbatim passage it rests on; the anchors profile facts point at |
| `users/robin/profile.yaml` | applied by hand, verified by Robin | 15 `verified` facts, 2 `draft` (the kayaker's date, the diesel figure), 1 `rejected` (the "12%" that was the master's timetable) |
| `users/robin/search.yaml` | section G of the questionnaire | a confidential search with a salary floor and a red flag |
| `users/robin/masters/port-operations-en/` | `30_tailor`, master mode | a generic one-page CV, approved, with a footer |
| `users/robin/masters/port-operations-fr/` | `30_tailor`, `based_on` the English master | the same facts in a French CV: labels, dates and degree names from `labels.fr.yaml`; the pivot language stays English |
| `jobs/20260915-…/raw.txt` → `job.yaml` | `10_normalize` | a posting quoted, never paraphrased |
| `users/robin/matches/20260915-….yaml` | `20_match` | a `stretch` verdict: strengths citing facts, the port-management-system gap named, the confidential-search flag raised |
| `users/robin/applications/20260915-…/cv-spec.yaml` | `30_tailor` | the master re-ordered for the posting; `ats_coverage` honest about what is missing |
| `users/robin/applications/20260915-…/letter.md` | `60_letter` | a letter that says the gap |

## Try this and watch it fail

The gates are mechanical. Two ways to see them:

```bash
# 1. cite a draft fact from an approved spec: validation fails, naming the fact
sed -i 's/exp-skerra.f03\]/exp-skerra.f03, exp-skerra.f08]/' users/robin/masters/port-operations-en/cv-spec.yaml
cvac validate --all            # ERROR ... cites non-verified fact(s): exp-skerra.f08
git checkout -- users/robin/masters/port-operations-en/cv-spec.yaml

# 2. render a draft as final: the resolver refuses
sed -i 's/status: approved/status: draft/' users/robin/masters/port-operations-fr/cv-spec.yaml
cvac cv users/robin/masters/port-operations-fr --mode final   # ERROR (cv): --mode final requires status: approved
git checkout -- users/robin/masters/port-operations-fr/cv-spec.yaml
```

## Run a stage yourself

```bash
cvac stage pack 20_match --user robin --job 20260915-saltmere-port-operations-officer > bundle.md
```

Paste `bundle.md` into any chat; save the answer where it says; `cvac validate`
it. See [docs/manual-path.md](../docs/manual-path.md).
