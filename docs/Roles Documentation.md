# ROLES.md

Every role on this project. One entry each. Add a role by appending an entry.

Process rules live in `WORKING_RULES.md`. This file is only who does what.

---

```yaml
- name: ENGINE
  job: build the measurement pipeline, phase by phase
  owns: engine/, tests/, scripts/phase_report.py
  reads: everything
  never: data/corpus/, data/chats/fixture_pair1/, data/corpus/golden_01/, web/, server/, the schemas
  brief: docs/briefs/E1_BRIEF.md
  rules:
    - prompts copied verbatim from COTRACE_PIPELINE_SPEC, never improved
    - req_id is unique within an outcome; key on (outcome_id, req_id)
    - never improvise anything touching a score or a sum
    - corpus runs in record mode, tests in replay

- name: DATA OPS
  job: own every conversation that reaches the engine, from any platform
  owns: data/archive/, data/corpus/ (except golden_01), scripts/ingest_*, scripts/archive_*, docs/IMPORT_SPEC*, docs/ARCHIVE_REPORT.md
  reads: everything
  never: engine/, tests/, web/, server/, data/chats/fixture_pair1/, data/corpus/golden_01/
  brief: docs/briefs/C_TRACK_BRIEF.md
  rules:
    - no LLM assigns prompt_style, mode_hint or direction_hint
    - the archive is never hand-edited; fix the converter and re-run
    - every format reaches the engine through the same importer
    - data/archive/ is gitignored before the first write

- name: DESIGN
  job: prepare real data in forms the owner can print and draw on
  owns: scripts/design_pack/, docs/design/
  reads: everything
  never: writes anywhere else
  brief: docs/DESIGN_SUPPORT_CHARTER.md
  rules:
    - prepares data, never proposes layouts or representations
    - states facts about the data freely; keeps design opinions to itself unless asked
    - leaves columns blank rather than estimating them

- name: OWNER
  job: decide, judge, and do what no agent can
  owns: data/corpus/golden_01/, every layer-2 judgement field
  rules:
    - hand-labels the golden chat before any engine sees it
    - judges the extraction gate personally
    - routes anything one role needs from another
```

---

## Adding a role later

Copy this, fill it in, append it above. That is the whole process.

```yaml
- name: 
  job: 
  owns: 
  reads: everything
  never: 
  brief: 
  rules:
    - 
```

Two things to get right and nothing else matters:

**`owns` must not overlap with any existing role.** If the work needs a path someone else
owns, the new role writes `BLOCKED` and the owner routes it.

**`rules` is three lines, not thirty.** Only what this role would otherwise get wrong. Deep
background belongs in its brief.

---

## Current dependencies

| Waiting | On |
|---|---|
| ENGINE E1.S1 | DATA OPS `clear_layer2.py` |
| ENGINE E1.S7 | OWNER golden chat labels |
| ENGINE E2 | `analysis.json` designed |
| ENGINE E3 | DATA OPS corpus selection |
| DESIGN pack v2 | ENGINE E1 |
| DATA OPS C0 | OWNER platform exports |
