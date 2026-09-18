# BUILD PLAYBOOK — the complete self-serve build guide (Phases 0–5)
### How to run the entire build without returning to the command center

This document replaces the command-center loop. It contains: the session sequence, the
exact kickoff prompt for every session, the gate rules between phases, and the protocols
that substitute for command-center judgment (verification, stuck-handling, spec
contradictions). The five phase briefs live beside it: PHASE1_BRIEF.md … PHASE5_BRIEF.md
(PHASE0_BRIEF.md already exists in docs/).

---

## 1. The session map (the engine-first rebuild, in order)

| # | Phase.Steps | Tool · Model | Brief | Gate to pass before next |
|---|---|---|---|---|
| 1 | E0.S1–S8 | Antigravity · Sonnet | E0_BRIEF | importer + corpus + invariants + harness |
| 2 | E1.S1–S? | Claude Code · Opus ONLY | E1_BRIEF | golden-chat grading + invariants 1–9 on corpus |
| 3 | E2.S1–S? | Claude Code · Opus ONLY | E2_BRIEF | canonical numbers EXACT from frozen ledger |
| 4 | E3.S1–S? | Claude Code · Opus, Antigravity for importers | E3_BRIEF | 10/10 chats complete + STABILITY.md written |
| 5 | E4.S1–S? | Claude Code · Opus | E4_BRIEF | invariant 20 (batch == live) + robustness green |
| 6 | E5.S1–S? | Claude Code · Opus | E5_BRIEF | panel_bundle byte-identical via projection |

Routing rule unchanged: wrong-number-is-worse-than-slow → Claude Code Opus;
your-eyes-are-the-test → Antigravity Sonnet/Gemini.

E0 is the exception to that rule's usual reading: it is mechanical, well specified,
and has no correctness-critical arithmetic, so Antigravity is correct for it.

---

## 2. The universal kickoff prompt (start of EVERY session)

```
Read AGENTS.md fully first — its workflow gates apply to this session (one step per
response, preamble before each step, wait for my "start task" and "Finish Step").
Then read docs/briefs/<PHASE_BRIEF>.md and the last two entries of BUILDLOG.md.

You are doing <PHASE.STEPS> only. Everything else in the brief is out of scope for
this session.

Begin with your preamble for the first step.
```

Fill in the brief name and step range from the session map. Each brief also contains a
phase-specific addendum to append to this prompt (data locations, hard rules).

**Mid-phase resume prompt** (new session, phase unfinished):
```
Read AGENTS.md, docs/briefs/<PHASE_BRIEF>.md, and the last BUILDLOG.md entry — it says
exactly where the previous session stopped. Continue from its "Next" line. Same gates.
```

---

## 3. The phase-close ritual and Architect Review Routine

A phase is closed ONLY when all six are done, in order:
1. **Programmatic phase report generated** — run `python3 scripts/phase_report.py`.
   All facts, test counts, invariant checks, and DoD status are generated strictly
   from the filesystem. Never write narrative prose from memory.
2. **BUILDLOG entry** appended (template in BUILDLOG.md), containing the exact output
   of `scripts/phase_report.py`.
3. **Architect Review Routine** — the Architect independently verifies the codebase,
   runs verification challenges, and audits claims. Any raised challenge items must
   be answered in the strict format: COMMAND RUN, OUTPUT, VERDICT, IF REFUTED, ACTION.
   Zero narrative evasion.
4. **Git:** commit + tag `eN-done` (only after all engineering DoD items pass and
   any owner-gate items are explicitly documented).
5. **AGENTS.md** "Current phase" line updated to reflect exact phase status, explicitly
   naming any owner prerequisites that gate starting the next phase.
6. **Self-review pass**: "Re-read the brief top to bottom. List anything specified that
   was not delivered, or delivered differently. If the list is non-empty, we are not
   done." — only an empty list closes the phase.

Never start phase N+1 with phase N's engineering DoD red. No exceptions, including
"it's probably fine."


---

## 4. The stuck protocol (replaces asking the command center)

When an agent hits a contradiction, gap, or repeated failure:
1. **Three attempts max** on any single failing thing, then stop looping.
2. Write the problem into **SPEC_QUESTIONS.md** (create at repo root on first use):
   what's ambiguous/broken, the options considered, which option was taken and why.
3. **Choose the most conservative interpretation** — the one that changes the least,
   adds the least, and stays closest to the spec's literal text. Mark it `REVISIT` in
   SPEC_QUESTIONS.md.
4. **Exception — correctness-critical numbers** (anything touching ledger scores,
   sums, the canonical fixture values): do NOT improvise. Stop the phase, log the
   blocker, move to a different step if one is independent, otherwise end the session
   with a clear BUILDLOG "blocked" entry. AGENTS.md rule 5 outranks momentum.
5. Spec authority order when documents disagree:
   **COTRACE_PIPELINE_SPEC > PANEL_SPEC / INTERACTION_SPEC / IMPORT_SPEC / TEST_STRATEGY > ARCHITECTURE > briefs.**

---

## 5. Standing quality rules (all phases)
- Prompts used by the engine are copied **verbatim** from COTRACE_PIPELINE_SPEC — never
  paraphrased, never "improved."
- Every artifact write is schema-validated at write time. A write that fails validation
  is a bug, not a warning.
- `llm_monitor.txt` logs every LLM call (full prompt + response) from Phase 2 onward.
- The fixture folder `data/chats/fixture_pair1/` is FROZEN after Phase 0 — later phases
  read it, never regenerate or "fix" it.
- No new dependencies beyond: pytest, jsonschema, fastapi, uvicorn, anthropic,
  json-repair, httpx/sse-starlette (server), react/vite/zustand (web). Anything else
  goes through SPEC_QUESTIONS.md first.
- Visual work: screenshot at every "Finish Step," compared against PANEL_SPEC's element
  tables by eye. Colors are law: blue #0057FF = you/left, orange #E85A0A = AI/right.
- Test tiers per TEST_STRATEGY §1. Unmarked tests fail review.
- engine/checks.py runs the invariants after every pipeline run in production, not
  only in tests (from E1 onward).
- Every run writes run/report.json per TEST_STRATEGY §6.
- Recorded LLM cassettes are committed. Re-record only when a prompt changes, and say
  so in the BUILDLOG entry.
- The corpus is generated. Never hand-edit an entry.
