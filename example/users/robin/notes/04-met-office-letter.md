---
schema_version: 1
kind: evidence
user: robin
source: sources/2025-met-office-letter.md
document_date: 2025-03-03
extracted_on: 2026-09-24
language: en
status: applied
new_parents:
  - id: prj-weather-logger
    role: Volunteer (personal project)
    company: {name: "National Weather Service, Observations Network", location: Skerra Head Lighthouse, industry: Meteorology}
    start: "2022-01"
    end: null
facts:
  - parent: exp-skerra
    claim: Skerra Head submitted its three-hourly synoptic observations to the National Weather Service without a gap from April 2018 to at least March 2025
    metrics: {since: "2018-04", as_of: "2025-03"}
    tags: [weather, reporting, reliability]
    quote: "Our records show that Skerra Head has submitted its three-hourly synoptic observations without a gap since April 2018"
    anchor: unbroken-series
  - parent: exp-skerra
    claim: Skerra Head was the only crewed station in the National Weather Service's northern district with an unbroken observation series over April 2018 to March 2025
    metrics: {}
    tags: [weather, reporting, reliability]
    quote: "which makes it the only crewed station in the northern district with an unbroken series over that period."
    anchor: only-unbroken-station
  - parent: prj-weather-logger
    claim: Proposed to the National Weather Service in January 2022 a volunteer project to log the station's barometer and wind readings automatically at one-minute intervals
    metrics: {proposed: "2022-01", interval_minutes: 1}
    tags: [weather, telemetry, initiative]
    quote: "We also note the volunteer project you proposed in January 2022 and have run since then: the automated logging of the station's barometer and wind readings at one-minute intervals"
    anchor: proposed-2022
  - parent: prj-weather-logger
    claim: Built the instrument shelter that houses the barometer and wind instruments of the one-minute logging project
    metrics: {}
    tags: [weather, telemetry, hands-on]
    quote: "from an instrument shelter you built yourself"
    anchor: instrument-shelter
  - parent: prj-weather-logger
    claim: Has run the one-minute barometer and wind logging since January 2022, sending a monthly export to the National Weather Service's climate section
    metrics: {since: "2022-01", exports_per_month: 1}
    tags: [weather, telemetry, reporting]
    quote: "and have run since then: the automated logging of the station's barometer and wind readings at one-minute intervals, from an instrument shelter you built yourself, with a monthly export sent to our climate section."
    anchor: monthly-export
  - parent: prj-weather-logger
    claim: The National Weather Service's climate section used the one-minute series in two published reports on winter storms, in 2023 and 2024
    metrics: {published_reports: 2, report_years: "2023, 2024"}
    tags: [weather, adoption, impact]
    quote: "The climate section has used that series in two published reports on winter storms (2023 and 2024)"
    anchor: published-reports
---

# National Weather Service letter — extraction (2026-09-24)

Six facts proposed from [[../sources/2025-met-office-letter]], a letter from the
Observations Network Manager of the National Weather Service to Robin, dated
3 March 2025. Two attach to `exp-skerra` and sharpen an existing fact; four
describe a volunteer logging project the profile does not have, proposed here as
`prj-weather-logger`. None repeats a fact already in the profile.

## New parent: prj-weather-logger

The letter describes "the volunteer project you proposed in January 2022 and
have run since then": one-minute logging of barometer and wind readings, a
self-built instrument shelter, a monthly export to the climate section. The
profile's only project, `prj-fogsignal`, is a Raspberry Pi logger of fog-signal
activations and generator hours, started March 2022, with a monthly export to
the Lights Board's engineering office. Different readings, different recipient,
different start date; neither document says the two are one system. The letter's
project is therefore proposed as its own parent, `start: "2022-01"` from the
month it was proposed, `end: null` because the letter says it still runs.
**Robin should say** whether the weather logging runs on the same Raspberry Pi as
the fog-signal logger. If it does, on apply the four project facts go under
`prj-fogsignal` instead and this new parent is dropped. The company is the body
the project was proposed to and reports to; the letter names no employer for it.

## unbroken-series
> Our records show that Skerra Head has submitted its three-hourly synoptic observations without a gap since April 2018

Sharpens `exp-skerra.f04` (observations every three hours for the national
meteorological service) with a third-party statement of continuity and a start
date, April 2018, which matches the start of `exp-skerra`. "Without a gap since
April 2018" holds as of the letter's date, so the claim says "to at least March
2025"; the letter does not vouch for anything later. The letter names the body
the "National Weather Service"; f04 says "national meteorological service".
Robin should confirm they are the same body.

## only-unbroken-station
> which makes it the only crewed station in the northern district with an unbroken series over that period.

Kept apart from the fact above: the continuity is what the station did, the
"only crewed station in the northern district" is the manager's comparison
against other stations, which Robin cannot know first-hand. "That period" is
April 2018 to the letter's date, from the preceding sentence.

## proposed-2022
> We also note the volunteer project you proposed in January 2022 and have run since then: the automated logging of the station's barometer and wind readings at one-minute intervals

The proposal itself: January 2022, Robin's initiative, one-minute intervals as
the document gives them. The letter does not say what hardware or software does
the logging; nothing about that is proposed.

## instrument-shelter
> from an instrument shelter you built yourself

One thing built, kept as its own fact. The letter says nothing about the
shelter's size, materials or standard.

## monthly-export
> and have run since then: the automated logging of the station's barometer and wind readings at one-minute intervals, from an instrument shelter you built yourself, with a monthly export sent to our climate section.

The running of the project and its deliverable, a monthly export to the climate
section. "Since then" is January 2022, from the same sentence. The letter does
not say how many exports were sent or whether any month was missed.

## published-reports
> The climate section has used that series in two published reports on winter storms (2023 and 2024)

Third-party use of the series: two reports, on winter storms, 2023 and 2024.
The letter does not name the reports or say whether Robin is credited in them;
Robin may know the titles, which would make this fact citable in a CV.

## Not proposed

- "Thank you for your continued contribution to the observations network": a
  courtesy, and nothing beyond what f04 and `unbroken-series` already say.
- "and would like to keep receiving it": the climate section's wish, not
  something Robin did or holds.
- "Should the station be automated, we would be glad to discuss how the
  one-minute series could continue": a conditional offer about the future.
  Relevant to the gap plan and to `search.yaml` (the station may be automated,
  which bears on Robin's timing), not to the profile.
- The address line "R. Ashcombe, Principal Keeper, Skerra Head Lighthouse"
  confirms the role in `exp-skerra` but adds nothing the profile lacks.
