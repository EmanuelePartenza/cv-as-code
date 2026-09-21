---
schema_version: 1
kind: evidence
user: robin
source: interviews/01-onboarding.md
document_date: 2026-09-15
extracted_on: 2026-09-16
language: en
status: applied
new_parents:
  - id: exp-skerra
    role: Principal Keeper
    company: {name: Northern Isles Lights Board, location: "Skerra Head Lighthouse, Skerra", industry: Aids to navigation}
    start: "2018-04"
    end: null
  - id: exp-fairhaven
    role: Deckhand, then bosun's mate
    company: {name: Marrow Sound Ferries, location: Kirkhaven, industry: Ferry services}
    start: "2013-06"
    end: "2018-03"
  - id: prj-fogsignal
    role: Author (personal project)
    company: {name: null}
    start: "2022-03"
    end: null
facts:
  - parent: exp-skerra
    claim: Sole keeper responsible for the daily operation of a first-order rotating light and its fog signal, on a rota with one relief keeper
    metrics: {}
    tags: [operations, lighthouse]
    quote: "Daily operation of a first-order rotating light and the fog signal, on a rota with one relief keeper."
    anchor: daily-operation
  - parent: exp-skerra
    claim: Maintained the lens drive, the lamp changer and the standby generator; six years without an unplanned outage of the light (2018–2024)
    metrics: {unplanned_outages: 0, years: 6}
    tags: [maintenance, aids-to-navigation, reliability]
    quote: "Six years without an unplanned outage of the light, 2018 to 2024"
    anchor: six-years
  - parent: exp-skerra
    claim: Coordinated by VHF with the coastguard during 14 incidents since 2019, including 3 helicopter medical evacuations
    metrics: {incidents: 14, medical_evacuations: 3}
    tags: [incident-coordination, radio, coastguard]
    quote: "Fourteen incidents with the coastguard on the radio since 2019, three of them helicopter medical evacuations — those are exact, they're in the log."
    anchor: incidents
  - parent: exp-skerra
    claim: Took and transmitted the station's weather observations every three hours for the national meteorological service
    metrics: {observations_per_day: 8}
    tags: [weather, reporting]
    quote: "I take the weather observations every three hours and send them to the met service."
    anchor: weather
  - parent: exp-skerra
    claim: Planned and managed the four supply landings a year — inventory, ordering and the landing plan agreed with the supply vessel's master
    metrics: {landings_per_year: 4}
    tags: [logistics, inventory, planning]
    quote: "I plan the supply landings, four a year: inventory, the order, and the landing plan with the supply vessel's master"
    anchor: landings
  - parent: exp-skerra
    claim: Trained five relief keepers and wrote the 40-page station handbook they work from
    metrics: {relief_keepers_trained: 5, handbook_pages: 40}
    tags: [training, documentation]
    quote: "I trained the relief keepers and wrote the station handbook because there wasn't one. [...] Five relief keepers trained. The handbook is 40 pages."
    anchor: handbook
  - parent: exp-skerra
    claim: Managed the station's budget for consumables and spares, about £40,000 a year (estimate)
    metrics: {budget_gbp_per_year: "~40000"}
    tags: [budget, procurement]
    quote: "The budget is about £40,000 a year — an estimate, it moves with the diesel price."
    anchor: budget
  - parent: exp-skerra
    claim: Assisted a kayaker stranded below the cliffs at night by guiding the lifeboat in by radio (2023, date to be confirmed against the logbook)
    metrics: {}
    tags: [incident-coordination, radio]
    quote: "in 2023 — I think 2023 — a kayaker got stuck below the cliffs at night and I talked the lifeboat in by radio. The log would confirm the date."
    anchor: kayaker
  - parent: exp-skerra
    claim: Reduced the standby generator's diesel consumption by about a fifth by re-scheduling its test runs (2021, figure never measured)
    metrics: {}
    tags: [maintenance, efficiency]
    quote: "I think I cut the generator's diesel use by about a fifth when I re-scheduled the test runs in 2021, but I never worked the figure out properly."
    anchor: diesel
  - parent: exp-fairhaven
    claim: Deck crew on a 40-metre ro-ro ferry making six crossings a day — mooring, cargo lashing and passenger safety briefings
    metrics: {crossings_per_day: 6, vessel_length_m: 40}
    tags: [deck-operations, safety]
    quote: "Mooring, cargo lashing, passenger safety briefings [...] Six crossings a day, 40-metre ro-ro."
    anchor: deck
  - parent: exp-fairhaven
    claim: Promoted to bosun's mate in 2016, responsible for the deck department's daily checks
    metrics: {}
    tags: [promotion, deck-operations]
    quote: "Deckhand, then bosun's mate from 2016. [...] the deck department's daily checks once I was bosun's mate."
    anchor: bosun
  - parent: exp-fairhaven
    claim: Held the radio watch on the bridge; GMDSS General Operator's Certificate obtained in 2014
    metrics: {}
    tags: [radio, gmdss, certification]
    quote: "I held the radio watch on the bridge on the crossings; I got the GMDSS General Operator's Certificate in 2014 for that."
    anchor: gmdss
  - parent: exp-fairhaven
    claim: STCW basic safety training completed in 2013 and renewed in 2018
    metrics: {}
    tags: [certification, safety]
    quote: "STCW basic safety training in 2013, renewed in 2018."
    anchor: stcw
  - parent: exp-fairhaven
    claim: Reduced crossing times by 12%
    metrics: {crossing_time_reduction_pct: 12}
    tags: [performance]
    quote: "I once told someone we cut crossing times by 12% — that was the master's new timetable, not me. Don't use it."
    anchor: twelve-percent
  - parent: prj-fogsignal
    claim: Built a telemetry logger on a Raspberry Pi (Python) recording fog-signal activations and generator running hours; three years of continuous data
    metrics: {years_of_data: 3}
    tags: [python, raspberry-pi, telemetry]
    quote: "A Raspberry Pi that records every fog-signal activation and the generator's running hours. [...] it has run for three years without me touching it."
    anchor: logger
  - parent: prj-fogsignal
    claim: The Lights Board's engineering office uses the logger's monthly export to plan maintenance visits, since 2023
    metrics: {}
    tags: [adoption, maintenance-planning]
    quote: "The Board's engineering office uses the monthly export to plan their maintenance visits, since 2023."
    anchor: adoption
---

# Onboarding questionnaire — extraction (2026-09-16)

Facts proposed from Robin's answers in [[../interviews/01-onboarding]]; each
heading below is the anchor a profile fact points at. Applied to
`profile.yaml` as `draft` on 2026-09-16; Robin confirmed them the same day
except where noted.

## daily-operation
> Daily operation of a first-order rotating light and the fog signal, on a rota with one relief keeper.

## six-years
> Six years without an unplanned outage of the light, 2018 to 2024 (there was one in 2025, storm damage to the drive, 40 minutes; I'm not hiding it, it just ends the run).

The 2025 outage is not a fact for the CV (Robin, C6) but the run is stated
honestly as 2018–2024.

## incidents
> Fourteen incidents with the coastguard on the radio since 2019, three of them helicopter medical evacuations — those are exact, they're in the log.

## weather
> I take the weather observations every three hours and send them to the met service.

## landings
> I plan the supply landings, four a year: inventory, the order, and the landing plan with the supply vessel's master, because the jetty only works in two wind directions.

## handbook
> I trained the relief keepers and wrote the station handbook because there wasn't one. [...] Five relief keepers trained. The handbook is 40 pages.

## budget
> The budget is about £40,000 a year — an estimate, it moves with the diesel price.

## kayaker
> in 2023 — I think 2023 — a kayaker got stuck below the cliffs at night and I talked the lifeboat in by radio. The log would confirm the date.

Left `draft`: the date is uncertain; the logbook excerpt will settle it.

## diesel
> I think I cut the generator's diesel use by about a fifth when I re-scheduled the test runs in 2021, but I never worked the figure out properly.

Left `draft`: no measured figure.

## deck
> Mooring, cargo lashing, passenger safety briefings [...] Six crossings a day, 40-metre ro-ro.

## bosun
> Deckhand, then bosun's mate from 2016. [...] the deck department's daily checks once I was bosun's mate.

## gmdss
> I held the radio watch on the bridge on the crossings; I got the GMDSS General Operator's Certificate in 2014 for that.

## stcw
> STCW basic safety training in 2013, renewed in 2018.

## twelve-percent
> I once told someone we cut crossing times by 12% — that was the master's new timetable, not me. Don't use it.

Proposed and **rejected** by Robin on verification: the figure exists in the
document, the attribution does not. Kept in the profile as `rejected` so it is
never proposed again.

## logger
> A Raspberry Pi that records every fog-signal activation and the generator's running hours. [...] Nothing clever, but it has run for three years without me touching it.

## adoption
> The Board's engineering office uses the monthly export to plan their maintenance visits, since 2023. Before that they guessed.

## Search parameters (section G, carried into search.yaml)

Target: port operations officer; harbour master eventually. Adjacent: marine
coordinator, VTS operator. Northern Isles on site; UK coast on site or hybrid;
Brittany on site. CV languages: en, fr. Floor £34,000/year. Red flag: rotating
night shifts without a relief plan. Confidential: yes.
