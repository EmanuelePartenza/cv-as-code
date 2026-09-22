---
schema_version: 1
kind: evidence
user: robin
source: sources/skerra-logbook-2025-excerpt.md
document_date: 2025-02-11
extracted_on: 2026-09-19
language: en
status: applied
new_parents: []
facts:
  - parent: exp-skerra
    claim: Guided the lifeboat by VHF and searchlight to a kayaker stranded below the north cliff at night (7 October 2023); casualty recovered, no injuries
    metrics: {date: "2023-10-07", lifeboat_alongside_minutes: 26}
    tags: [incident-coordination, radio]
    quote: "Guided the lifeboat by VHF to the ledge from the gallery, searchlight on the casualty; lifeboat alongside 23:18, casualty recovered 23:24."
    anchor: kayaker-2023-10-07
  - parent: exp-skerra
    claim: Changed the standby generator's test cycle in May 2021; diesel drawn over the following landing period fell from 760 l to 610 l year on year
    metrics: {diesel_before_l: 760, diesel_after_l: 610, reduction_pct: 19.7}
    tags: [maintenance, efficiency]
    quote: "Diesel drawn since 03 May: 610 l against 760 l the same period last year (from 2020 landing notes)."
    anchor: diesel-2021
  - parent: exp-skerra
    claim: Restored the light within 40 minutes after a drive-belt failure in a storm (11 February 2025) using the spare belt
    metrics: {outage_minutes: 40}
    tags: [maintenance, incident]
    quote: "Light stopped: drive belt failure in storm; light restored 05:15 on the spare belt (40 min outage)."
    anchor: outage-2025
---

# Logbook excerpt — extraction (2026-09-19)

Three facts proposed from [[../sources/skerra-logbook-2025-excerpt]]. The
questionnaire had left two of them `draft` (notes/01-onboarding.md, anchors
`kayaker` and `diesel`); this document sharpens both with dates and numbers.

## kayaker-2023-10-07
> Coastguard call: kayaker reported stranded on the ledge below the north cliff, no injuries, tide rising. Lifeboat launched 22:52. Guided the lifeboat by VHF to the ledge from the gallery, searchlight on the casualty; lifeboat alongside 23:18, casualty recovered 23:24.

Sharpens `exp-skerra.f08` (the date Robin was unsure of): applied as a second
evidence pointer on f08, which Robin then verified with `cvac fact verify`.

## diesel-2021
> Diesel drawn since 03 May: 610 l against 760 l the same period last year (from 2020 landing notes).

Sharpens `exp-skerra.f09` ("about a fifth"): 610 against 760 is a 19.7 %
reduction over one landing period, not a year. Applied as a second evidence
pointer on f09; **left `draft`** — one period is not "consumption", and Robin
wants to see the other landings before confirming.

## outage-2025
> Light stopped: drive belt failure in storm; light restored 05:15 on the spare belt (40 min outage).

New fact, applied as `exp-skerra.f10`, `draft`: Robin said in the questionnaire
that the outage does not go on a CV. It is recorded because it happened and the
recovery time is a fact; whether to cite it is a spec decision, not a profile one.
