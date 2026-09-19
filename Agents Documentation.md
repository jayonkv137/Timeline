# AGENTS.md — Agency Panel (Idea 4)
(Canonical agent instructions. Read by every AI tool working on this repo — Antigravity,
Claude Code, anything else. CLAUDE.md imports this file.)

## What this project is
A live AI chat application with a right-rail "agency panel" that mirrors, turn by turn,
how the work is being shaped between the person and the AI — which goal is active, how
much steering came from each party, how many decisions each made, what happened each
exchange (with evidence), and the usage mode (You're driving / Copilot / Autopilot).
Every number is computed by a real pipeline (COTRACE-based) and traces to a verbatim
quote. It is a mirror, not a judge.

## The authoritative documents (read the sections the current brief names)
- `docs/ARCHITECTURE.md` — system design, decisions D1–D13, artifact contracts (§3),
  API surface (§4), live-turn sequence (§5), phase plan (§6), this protocol (§7)
- `docs/COTRACE_PIPELINE_SPEC.md` — v5, the backend bible: Steps 1a–3 prompts, E1/E2,
  iteration mechanism (§9), Stage 4 math (§10), cross-cutting rules (§11), honesty
  ledger (§12)
- `docs/PANEL_SPEC.md` — v2.0, what renders: five sections, element inventories,
  element→backend contract (§6)
- `docs/INTERACTION_SPEC.md` — v1, how it behaves: pair coordinate model, scrub sources,
  live-turn choreography, state inventory
- `docs/IMPORT_SPEC.md` — v1.0, how raw exports become engine input: corpus layout,
  normalisation per format, pairing rules, origin tagging, fidelity accounting
- `docs/TEST_STRATEGY.md` — v1.0, how the engine is proven: four test tiers, the
  21 invariants, corpus design, stability protocol, robustness scenarios

## Standing rules (non-negotiable)
1. The docs above are READ-ONLY from this side. If implementation reveals a
   contradiction or gap, STOP and report it — the spec gets amended at the command
   center (a separate planning chat), never here.
2. Workflow gates: ONE step per response. Before each step give a short preamble (why
   this step, decisions needed, high-level picture). Wait for "start task" before doing
   the step. Wait for "Finish Step" before advancing to the next.
3. When visual output changes, prompt the owner for a fresh screenshot check.
4. Never commit `.env`. Keep `.env.example` current.
5. Verified fixture numbers are sacred: Δ_you=87.0, Δ_AI=314.0 → You 21.7% / AI 78.3%;
   decisions 4 you · 10 AI; mode COPILOT (w 4/10, h 47.0/239.0). Any code producing
   different numbers from the fixture ledger is wrong, not the numbers.
   The same applies to analysis.json once E2 defines it: the fixture ledger is the
   source of truth and any code disagreeing with it is wrong.
6. Prefer boring, readable code. No framework beyond the decided stack (ARCHITECTURE §2):
   Python engine, FastAPI server, React+Vite+Zustand web. Files over databases.
7. Test tiers are mandatory. Every test carries exactly one marker: tier0 (replay),
   tier1 (exact, no network), tier2 (live API), tier3 (robustness). An unmarked test
   is a bug. Default `pytest` runs tier0 and tier1 only.
8. No phase closes with any invariant in tests/invariants.py red. Invariants are not
   advisory.
9. Corpus entries under data/corpus/ are generated, never hand-edited. If an entry is
   wrong, fix scripts/ingest_export.py and re-import with --force. The frozen fixture
   at data/chats/fixture_pair1/ is never regenerated, for any reason.


## Multi-tool protocol (this repo is worked on from several AI tools)
- **The repository is the only shared brain.** No tool sees another tool's chats. All
  context lives in: docs/ (specs), AGENTS.md (rules), BUILDLOG.md (history), the code,
  and git history. When handing work between tools, summarize the filesystem state,
  never the chat.
- **BUILDLOG ritual (mandatory):** before ending ANY session, append one entry to
  BUILDLOG.md using its template — tool+model, phase/step, files touched, decisions
  made, contradictions flagged, verification results, next step. If you cannot finish
  cleanly, the entry says exactly where things stand.
- **Commit discipline:** small commits per step; message = "P<phase>.S<step>: <what>
  — <why>" so git history mirrors the plan.
- **Tool routing (who does what):** Antigravity (Gemini/Sonnet) → scaffolding, UI
  iteration, styling, boilerplate, test writing. Claude Code (Opus) → the engine,
  pipeline prompts integration, Stage-4/ledger math, anything where a wrong number is
  worse than a slow answer, cross-cutting debugging. The phase brief assigns steps to
  tools; if unassigned, default by this rule.
- **One task group at a time.** Never one-shot a phase. After each step, update the
  phase brief's status checkbox and stop for the owner's gate.
- **Review-the-scaffold rule:** after any generation that creates structure (folders,
  schemas, configs), pause for owner review before building on top of it.

## Current phase
E0 — Corpus, Importer, Harness (CLOSED — Tagged `e0-done`). Ready for Phase E1.

All Phase E0 deliverables are 100% complete and verified via `scripts/phase_report.py`:
- Importer + fidelity accounting + fidelity grading (`clean`/`degraded`/`unusable`) across 36 chats (909 pairs).
- The 21 invariants module (`tests/invariants.py`), with verbatim evidence quote checking in `inv_21`.
- Caching LLM client (`engine/llm_cache.py`).
- 52 tests green across all suites in < 0.5s.
- Manifest 100% reconciled against individual sidecars.
- All 36 corpus folders populated with `meta.yaml` and renamed to `c<NN>_<task_type>_<length>`.
- Frozen fixture `fixture_pair1` byte-identical to origin.
- `golden_01` initialized from `c15_creative_medium` with `expected.md`.

**Corpus & Evaluation Strategy for E1:**
Per user directive, testing and extraction benchmarking will not be restricted to a single golden chat. E1 will evaluate extraction across the entire usable corpus in varying ways — leveraging all 17 usable chats (10 `clean`, 7 `degraded`) across diverse domains (Coding, Creative, Writing, Planning, Research, Debugging) to ensure pipeline generalization.

Next: **Phase E1 — Extraction Pipeline (Steps 1a–3)**.
