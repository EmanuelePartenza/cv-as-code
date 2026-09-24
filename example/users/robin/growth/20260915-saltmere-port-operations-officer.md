---
schema_version: 1
kind: gap-plan
user: robin
job_id: 20260915-saltmere-port-operations-officer
created: "2026-09-24"
gaps:
  - requirement: "Working knowledge of a port management system (berth planning, vessel scheduling)"
    kind: must
    adjacent_facts: [exp-skerra.f05, prj-fogsignal.f01, prj-fogsignal.f02]
    path:
      - deliverable: >-
          Find out which port management system the Port of Saltmere uses (the
          posting does not name it) and complete that vendor's user training, or
          an equivalent assessed short course on port operations and berth
          planning; provider, format and cost to be verified before committing
        artefact: A dated certificate of completion or assessment result, naming the system or the course
        effort: 2–4 weeks part-time (about 20–40 hours), provider to be verified
      - deliverable: >-
          Shadow the operations desk of a working harbour for three to five days
          during a relief period off the station, using its berth-planning and
          scheduling system alongside the duty officer. Arranged directly with
          the harbour, not through the Lights Board, and asked to be kept
          discreet
        artefact: >-
          A dated note signed by the harbour master or duty officer stating the
          dates, the system used and the tasks done under supervision
        effort: 3–5 days on site, plus travel from Skerra
      - deliverable: >-
          A small Python berth-planning model of a two-basin port. Acceptance
          criteria: berths described by length and depth; vessels by length,
          draught and arrival/departure windows; the model allocates berths,
          flags conflicts, and prints a daily movements schedule; ten sample
          days with at least one conflict each resolved
        artefact: A public repository with README, sample data and a dated tagged release
        effort: about 30–40 hours over 3–4 weeks
    candidate_facts:
      - "Completed [system or course name] user training on berth planning and vessel scheduling ([month year]), certificate held"
      - "Shadowed the operations desk at [harbour] for [n] days ([month year]), planning berths and scheduling vessel movements in [system] under supervision"
      - "Built a berth-allocation and vessel-scheduling model for a two-basin port in Python, with conflict detection ([year])"
  - requirement: VTS operator certification
    kind: nice
    adjacent_facts: [exp-fairhaven.f03, exp-skerra.f03, exp-skerra.f08]
    path:
      - deliverable: >-
          Enrol in a VTS operator course to the IALA V-103/1 model course
          standard at an accredited training centre, ending in the course
          assessment; duration, cost and entry requirements to be verified with
          the provider before committing
        artefact: A VTS operator certificate (V-103/1), dated
        effort: several weeks full-time (to verify) — not compatible with the station rota without leave
    candidate_facts:
      - "Obtained the VTS operator certificate (IALA V-103/1) at [training centre] in [year]"
  - requirement: Experience with vessel traffic monitoring
    kind: nice
    adjacent_facts: [exp-fairhaven.f01, exp-fairhaven.f03]
    path:
      - deliverable: >-
          On personal equipment (not the station's systems), add an AIS receiver
          to a Raspberry Pi and log the vessel traffic passing Skerra Head for
          one month. Acceptance criteria: continuous log with fewer than 24 hours
          of gaps; a monthly report of movements by vessel type and hour, with
          three noteworthy passages annotated from the watch
        artefact: A public repository with the logger code and a dated monthly traffic report
        effort: about 20 hours of build, then one month of logging
      - deliverable: >-
          During the same harbour visit as the shadowing above, spend a watch
          alongside the harbour's traffic or VTS operator, if the harbour has one
        artefact: The same signed note, with a line on the traffic watch observed
        effort: one watch (about 8–12 hours), within the same visit
    candidate_facts:
      - "Built an AIS receiver and logger on a Raspberry Pi and produced a monthly report of vessel traffic past Skerra Head ([month year])"
      - "Observed a traffic watch alongside the VTS operator at [harbour] ([month year])"
---

# Gap plan — Port Operations Officer, Port of Saltmere Harbour Authority

**The gap that changes the verdict:** working knowledge of a port management
system. It is the only `must` gap; closing it moves the match from *stretch*
towards *fit*. The two `nice` gaps would strengthen the application but do not
change the verdict on their own.

Constraints kept in view: the search is confidential (the Lights Board does not
know, and the island is small), so nothing below goes through the Board or asks
the Board for a reference; the station is on a rota with one relief keeper, so
anything longer than a few days needs leave; the posting's salary (£36–40k)
clears the £34k floor, so the effort is worth sizing for this role.

## 1. Working knowledge of a port management system (berth planning, vessel scheduling) — must

**What Robin already has.** No port management software, and nothing that
shows it — this is a real gap, not a presentation problem. What is adjacent:

- `exp-skerra.f05` — four supply landings a year planned end to end, the
  landing plan agreed with the supply vessel's master: the same problem (fit a
  vessel into a window and a place), by hand, at a far lower volume.
- `prj-fogsignal.f01` — a Python telemetry logger built from nothing: evidence
  of learning a system and a tool without being taught.
- `prj-fogsignal.f02` — the Board plans its maintenance visits from that
  logger's export: scheduling others work from Robin's data, not in a port
  system.

**Closing path.** In order of value to this posting:

1. **The system itself.** Find out which port management system Saltmere runs
   and take that vendor's user training, or an assessed short course on port
   operations and berth planning. Availability, format and cost are not known
   yet and must be checked. *Artefact:* a dated certificate naming the system
   or course. *Effort:* about 20–40 hours over 2–4 weeks.
2. **Shadowing a harbour desk.** Three to five days at a working harbour's
   operations desk during a relief period, using its system under supervision,
   arranged directly and discreetly. *Artefact:* a dated note signed by the
   harbour master or duty officer, naming the system and the tasks. *Effort:*
   3–5 days plus travel.
3. **A berth-planning model.** A small Python model of a two-basin port
   (berths by length and depth, vessels by length, draught and windows;
   allocation, conflict flags, a daily schedule; ten sample days). It shows the
   reasoning, **not** working knowledge of a commercial system — it supports
   steps 1–2, it does not replace them. *Artefact:* a public repository with a
   tagged release. *Effort:* about 30–40 hours.

**Candidate facts** — future claims, to be written only after the artefact
exists, extracted by stage 03 and verified by Robin:

- Completed [system or course name] user training on berth planning and vessel
  scheduling ([month year]), certificate held.
- Shadowed the operations desk at [harbour] for [n] days ([month year]),
  planning berths and scheduling vessel movements in [system] under supervision.
- Built a berth-allocation and vessel-scheduling model for a two-basin port in
  Python, with conflict detection ([year]).

## 2. VTS operator certification — nice

**What Robin already has.** No VTS certification. Adjacent, and substantial:

- `exp-fairhaven.f03` — radio watch on a ferry bridge; GMDSS General
  Operator's Certificate (2014).
- `exp-skerra.f03` — 14 incidents coordinated with the coastguard by VHF since
  2019, three helicopter medical evacuations.
- `exp-skerra.f08` — guided a lifeboat to a stranded kayaker at night by VHF
  and searchlight (7 October 2023).

These show the radio and coordination side of VTS work; they are not VTS
operation and do not stand in for the certificate.

**Closing path.**

1. **A VTS operator course** to the IALA V-103/1 model course standard at an
   accredited centre, ending in its assessment. *Artefact:* a dated V-103/1
   certificate. *Effort:* several weeks full-time — duration, cost and entry
   requirements to be verified with a provider.

Honest sizing: for this posting, where the certificate is only `nice`, the
course costs more than it returns and needs leave the rota cannot easily give.
It pays off if the search turns towards the adjacent `vts-operator` role;
otherwise leave it until after a port role, where an employer may fund it.

**Candidate facts** — future claims:

- Obtained the VTS operator certificate (IALA V-103/1) at [training centre] in
  [year].

## 3. Experience with vessel traffic monitoring — nice

**What Robin already has.** None as an operator. Adjacent:

- `exp-fairhaven.f01` — nearly five years (2013–2018) of deck crew on a ro-ro ferry making six
  crossings a day: the monitored side of vessel traffic.
- `exp-fairhaven.f03` — the radio watch on the bridge: the other end of the
  traffic channel.

**Closing path.**

1. **An AIS traffic logger.** On personal equipment, not the station's systems,
   add an AIS receiver to a Raspberry Pi and log the traffic past Skerra Head
   for a month: under 24 hours of gaps, a monthly report by vessel type and
   hour, three passages annotated from the watch. It builds directly on the
   fog-signal logger. *Artefact:* a public repository and a dated monthly
   report. *Effort:* about 20 hours of build, then a month of logging.
2. **A traffic watch.** During the harbour visit in gap 1, a watch alongside
   the harbour's traffic or VTS operator, if it has one. *Artefact:* a line in
   the same signed note. *Effort:* one watch, within the same visit.

The logger shows monitoring as a practice, not as an operator's duty; the
watch alongside an operator is the closer evidence.

**Candidate facts** — future claims:

- Built an AIS receiver and logger on a Raspberry Pi and produced a monthly
  report of vessel traffic past Skerra Head ([month year]).
- Observed a traffic watch alongside the VTS operator at [harbour] ([month
  year]).
