# PHASE 4 BRIEF — Instrument Quality
**Tool: Antigravity · Sonnet (Gemini for styling passes); Claude Code · Opus only for
S6 (failure/retry logic). Volume work; your eyes are the test.**

## Goal
Everything that makes it feel finished: the full interaction inventory, honest empty
states, recovery UX, and the complete goal-tree expansion — INTERACTION_SPEC v1 passing
end to end on a live chat.

## Read first
INTERACTION_SPEC (all — §7's state inventory is this phase's checklist) · PANEL_SPEC §1
(thread-collapse cases) + §4 · the popover a11y rules in PHASE1_BRIEF S2.

## Steps
**S1 — Viewed-pair & navigation polish.** Bubble highlight styling; Back-to-latest pill
(appears when scrolled away OR in history); smooth scroll on scrub; hover tooltip on
collapsed timeline rows = `Pn · <R-SUM line>`.
**S2 — Goal tree, all cases.** Full thread-collapse behavior against the dev deep tree
AND a live deep chat: d=0/1/2/≥3 default views, progressive chip reveal (segment by
segment, count decreasing), off-path sibling chips, "show less," internal scroll only
while expanded, node click = scrub to first-appearance pair (hover: "Pn · where this
started"; cursor + hover state signifiers).
**S3 — Decisions example tap** → scrub to creation pair. Popover a11y audit on all five
(keyboard, Escape, aria, contrast).
**S4 — Empty & zero states.** New chat: sections render quiet zero states (no fake
data, no skeleton pretending to be data); empty-exchange drawer line ("execution only —
no requirements touched"); per-chat viewedPair remembered across switches in-session.
**S5 — Level-2 v1 (minimal, honest).** Replace the placeholder with the data that
already exists in state.json: exact requirement text, creator, op history, and its
evidence quote(s). No design flourish — a plain, readable card. (Full level-2 design
remains deferred; this ships the data contract's minimum.)
**S6 — Failure UX (Claude Code).** `pipeline_status: failed` → rail shows a quiet
inline notice on that pair's row + "retry" affordance calling the rerun endpoint;
success clears it. Chat-switch mid-run: background-complete (per ARCHITECTURE §8 note).
**S7 — The full walkthrough.** Execute INTERACTION_SPEC §7's state inventory as a
manual QA matrix — every component × every state — screenshot each, log the matrix in
the BUILDLOG entry.

## Definition of Done
The S7 matrix complete with zero failing cells · P2/P3 test suites still green ·
render test updated for level-2 v1.

## Kickoff prompt addendum
```
No new visual language: every element you touch already has a definition in PANEL_SPEC
or INTERACTION_SPEC — polish means matching the spec better, not inventing. Anything
that feels missing → SPEC_QUESTIONS.md, conservative choice, REVISIT tag.
```
