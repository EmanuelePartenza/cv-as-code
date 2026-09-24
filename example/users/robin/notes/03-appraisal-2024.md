---
schema_version: 1
kind: evidence
user: robin
source: sources/2024-appraisal-district-superintendent.md
document_date: 2025-01-14
extracted_on: 2026-09-24
language: en
status: applied
new_parents: []
facts:
  - parent: exp-skerra
    claim: Ran the district's relief-keeper induction at Skerra Head in April 2024 for two new keepers, five days each, using the station handbook as the syllabus
    metrics: {date: "2024-04", keepers_inducted: 2, days_per_keeper: 5}
    tags: [training, documentation]
    quote: "The keeper ran the district's relief-keeper induction at Skerra Head in April 2024 for two new keepers, over five days each, using the station handbook as the syllabus."
    anchor: induction-2024
  - parent: exp-skerra
    claim: Both keepers inducted in April 2024 were signed off for solo relief duty by the end of 2024
    metrics: {keepers_signed_off: 2}
    tags: [training]
    quote: "Both were signed off for solo relief duty by the end of the year."
    anchor: signed-off-2024
  - parent: exp-skerra
    claim: Planned and hosted the contractor's three-day overhaul of the lens drive in September 2024
    metrics: {date: "2024-09", overhaul_days: 3}
    tags: [maintenance, planning, contractor-management]
    quote: "In September 2024 the keeper planned and hosted the contractor's three-day overhaul of the lens drive"
    anchor: overhaul-2024
  - parent: exp-skerra
    claim: Scheduled the September 2024 lens-drive overhaul in daylight hours so that the light was exhibited every night of the contractor's visit; no outage was recorded
    metrics: {outages: 0}
    tags: [maintenance, planning, reliability]
    quote: "scheduling the work in daylight hours so that the light was exhibited every night of the visit; no outage was recorded."
    anchor: overhaul-no-outage
  - parent: exp-skerra
    claim: The 2024 district appraisal recorded another year without a defect on the light
    metrics: {year: 2024, defects: 0}
    tags: [reliability, aids-to-navigation, appraisal]
    quote: "Another year without a defect on the light."
    anchor: no-defect-2024
  - parent: exp-skerra
    claim: First-aid-at-work certificate renewed in March 2024, valid to March 2027
    metrics: {renewed: "2024-03", valid_to: "2027-03"}
    tags: [certification, safety]
    quote: "First-aid-at-work certificate renewed in March 2024 (valid to March 2027)"
    anchor: first-aid-2024
  - parent: exp-skerra
    claim: Completed the Northern Isles Lights Board's fire-safety refresher in March 2024
    metrics: {date: "2024-03"}
    tags: [certification, safety]
    quote: "the keeper also completed the Board's fire-safety refresher in the same month."
    anchor: fire-safety-2024
---

# 2024 appraisal — extraction (2026-09-24)

Seven facts proposed from [[../sources/2024-appraisal-district-superintendent]],
the District Superintendent's annual appraisal for January to December 2024,
meeting held 14 January 2025. All attach to `exp-skerra`; the document names no
position or project the profile lacks. Two of the facts sharpen existing ones
(see below); none repeats a fact already in the profile.

## induction-2024
> The keeper ran the district's relief-keeper induction at Skerra Head in April 2024 for two new keepers, over five days each, using the station handbook as the syllabus.

Sharpens `exp-skerra.f06` (five relief keepers trained, 40-page handbook): the
appraisal gives one training episode a date, a head count, a duration per keeper
and the handbook's role as syllabus. Whether these two are among the five in f06
or come on top of them is not stated by either document; Robin should say.

## signed-off-2024
> Both were signed off for solo relief duty by the end of the year.

Outcome of the induction above, kept as its own fact: the sign-off is the
district's act, and the document does not say who signed them off.

## overhaul-2024
> In September 2024 the keeper planned and hosted the contractor's three-day overhaul of the lens drive, scheduling the work in daylight hours so that the light was exhibited every night of the visit; no outage was recorded.

Two facts rest on this passage. This one is the overhaul itself: planned and
hosted, three days, September 2024. It is the first document that shows Robin
managing a contractor's visit rather than doing the maintenance alone.

## overhaul-no-outage
> scheduling the work in daylight hours so that the light was exhibited every night of the visit; no outage was recorded.

The scheduling decision and its result. The document says "no outage was
recorded", not "no unplanned outage"; the claim keeps the document's words.

## no-defect-2024
> Another year without a defect on the light.

Sharpens `exp-skerra.f02` (six years without an unplanned outage, 2018–2024)
with a third-party source for the year 2024. The appraisal says "defect", f02
says "unplanned outage"; the two are not the same word and the claim keeps the
appraisal's. On apply, this could also be added as a second evidence pointer on
f02 rather than as a separate fact; that is Robin's call.

## first-aid-2024
> First-aid-at-work certificate renewed in March 2024 (valid to March 2027)

The profile has no first-aid certificate; the document says "renewed", so an
earlier certificate existed, but it gives no date for it and none is proposed.

## fire-safety-2024
> the keeper also completed the Board's fire-safety refresher in the same month.

"The Board" is the Northern Isles Lights Board, named in the document header.
"The same month" is March 2024, from the preceding sentence.

## Not proposed

- "Skerra Head remains the station the district sends new keepers to first" is
  the superintendent's remark about the station, not a fact about what Robin
  did; it is consistent with f06 and `induction-2024` but adds nothing citable.
- Point 4, *Development*: "The keeper asked for exposure to harbour operations;
  the superintendent will raise a short attachment with a harbour authority for
  2025. Not yet arranged at the time of the meeting." A request and an intention,
  not something done or held. Relevant to `search.yaml` and to the gap plan
  (harbour operations is the target domain), not to the profile. If the
  attachment later takes place, that will be a fact with its own document.
