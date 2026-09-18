# PHASE 1 BRIEF — Panel Shell on Fixture
**Tool: Antigravity · Sonnet (switch to Gemini for pure styling passes). No backend, no
LLM calls, no server — a static React app rendering the verified fixture.**

## Goal
The first honest screenshot: the real pair-1 numbers rendered on the real design. Every
panel section built, fed only by `data/chats/fixture_pair1/panel_bundle.json` (+
`dialogue.json` for the chat column).

## Read first
PANEL_SPEC.md (all — it is this phase's blueprint, §6 maps every element to its bundle
field) · INTERACTION_SPEC.md §0–§2 · the fixture folder README (which fields are
verified vs. stubs).

## Steps
**S1 — App scaffold.** In `web/`: Vite + React + TypeScript + Zustand. A `npm run
sync-fixture` script copies `data/chats/fixture_pair1/` into `web/public/fixture/`;
the app fetches from there. Design tokens as CSS variables: `--you:#0057FF;
--ai:#E85A0A; --bg:#faf9f6; --panel:#f1efe9;` fonts: Inter (UI), DM Mono (labels).
**S2 — Layout shell.** Three regions (sidebar · chat · rail ~360px). Rail top status
strip (`LIVE` state, since fixture has one pair). Five section containers, each with its
heading + (i) popover. Popover copy, verbatim:
- GOAL: "Gives you an idea what you are currently working on, and a bit of context on
  the goal you are working towards. You can expand to see the full structure of your
  goals."
- DIRECTION: "Shows how much of this chat's direction has come from you versus the AI,
  added up so far. Updates as you keep talking."
- DECISIONS: "A count of who introduced what. Each time a new requirement or idea gets
  set for this chat, it's counted here under whoever introduced it first."
- TIMELINE: "The record of what actually happened — one row per exchange. Tap a row to
  see what was decided and why."
- HOW YOU'RE WORKING: "Shows how you and the AI worked together this exchange." +
  three mode lines: **You're driving** — you're setting the direction, AI helps when
  asked. / **Copiloting** — you and the AI are shaping the work together. /
  **Autopilot** — the AI is mostly deciding and doing.
Popovers: open on click AND keyboard focus+Enter; close on Escape/outside/X;
aria-expanded + aria-describedby; text contrast ≥ 4.5:1.
**S3 — Chat column.** Render dialogue.json turns (stub text is fine), P-badges on user
messages, input bar (non-functional this phase).
**S4 — GOAL section.** Thread-collapse per PANEL_SPEC §1: fixture is d≤2 so no chip —
but implement the chip logic anyway against a hardcoded DEV deep tree (5 levels) behind
a `?devtree=1` flag, so all depth cases exist and are testable now.
**S5 — DIRECTION + DECISIONS.** Split bar + readouts + `@ P1` badge; counter + latest-AI
example (truncate at clause boundary).
**S6 — TIMELINE.** Collapsed row (pair label · turn-delta micro-spine · summary ·
chevron). Drawer per §4.2: spine, one bar per requirement (per-turn Δ from the bundle),
R-chips colored by the bundle's chip field, slot rings with S-labels. Accordion (trivial
with 1 pair, build the mechanism anyway). Level-2: requirement rows are tappable but
open a "coming later" placeholder — reserve the target, ship nothing fake.
**S7 — HOW.** Mode line (fixture = Copilot sentence) + mode split bar (100% copilot).

## Definition of Done (both parts)
(a) **Render test** (Vitest + React Testing Library): asserts these exact strings/values
appear — `21.7`, `78.3`, `4 you`, `10 AI`, the triple-references example text, `P1`,
14 requirement rows in the opened drawer, 5 slot rings, the Copilot mode line.
(b) **Eyeball checklist walked and screenshotted:** chip colors = 13 grey + 1 orange
(o5/r2 only) · blue always left / orange always right · headings + 5 working popovers ·
three-second glance test on the default goal view · no invented labels anywhere
(no "MAIN GOAL"/"CURRENT" text).

## Out of scope
Server, live data, scrubbing across pairs (one pair exists), level-2 content, animations.

## Kickoff prompt addendum (append to the universal prompt)
```
Data: web app reads ONLY web/public/fixture/ (synced from data/chats/fixture_pair1/).
Hard rules: colors/vocabulary per PANEL_SPEC §0 are law; popover copy verbatim from
this brief; nothing rendered that is not in the bundle (no fake data, no placeholders
presented as real values).
```
