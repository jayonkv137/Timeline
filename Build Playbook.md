# BUILD PLAYBOOK — the complete self-serve build guide (Phases 0–5)
### How to run the entire build without returning to the command center

This document replaces the command-center loop. It contains: the session sequence, the
exact kickoff prompt for every session, the gate rules between phases, and the protocols
that substitute for command-center judgment (verification, stuck-handling, spec
contradictions). The five phase briefs live beside it: PHASE1_BRIEF.md … PHASE5_BRIEF.md
(PHASE0_BRIEF.md already exists in docs/).

---

## 1. The session map (the whole build, in order)

| # | Phase.Steps | Tool · Model | Brief | Gate to pass before next |
|---|---|---|---|---|
| 1 | P0.S1–S2 | Antigravity · Gemini→Sonnet | PHASE0_BRIEF | schemas reviewed by owner |
| 2 | P0.S3–S4 | Claude Code · Opus | PHASE0_BRIEF | pytest green (canonical numbers) |
| 3 | P1.S1–S7 | Antigravity · Sonnet (Gemini for styling) | PHASE1_BRIEF | value-checklist + render test green |
| 4 | P2.S1–S8 | Claude Code · Opus ONLY | PHASE2_BRIEF | fixture regression EXACT + checks green |
| 5 | P3.S1–S4 | Claude Code · Opus | PHASE3_BRIEF | server tests green |
| 6 | P3.S5–S7 | Antigravity · Sonnet | PHASE3_BRIEF | live 6-pair conversation checklist |
| 7 | P4.S1–S7 | Antigravity · Sonnet/Gemini (Claude Code for retry logic) | PHASE4_BRIEF | INTERACTION_SPEC state checklist |
| 8 | P5.S1–S5 | Claude Code · Opus | PHASE5_BRIEF | CALIBRATION.md complete |

Routing rule if ever unsure: **wrong-number-is-worse-than-slow → Claude Code Opus;
your-eyes-are-the-test → Antigravity Sonnet/Gemini.**

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

## 3. The phase-close ritual (replaces command-center verification)

A phase is closed ONLY when all five are done, in order:
1. **DoD executed** — the brief's Definition of Done run for real (pytest output / the
   checklist walked item by item), results pasted into the BUILDLOG entry.
2. **BUILDLOG entry** appended (template in BUILDLOG.md).
3. **Git:** commit + tag `phase-N-done`.
4. **AGENTS.md** "Current phase" line updated to the next phase + its DoD.
5. **Self-review pass** (one prompt, same session): "Re-read the brief top to bottom.
   List anything specified that was not delivered, or delivered differently. If the
   list is non-empty, we are not done." — only an empty list closes the phase.

Never start phase N+1 with phase N's DoD red. No exceptions, including "it's probably
fine."

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
   **COTRACE_PIPELINE_SPEC > PANEL_SPEC / INTERACTION_SPEC > ARCHITECTURE > briefs.**

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
