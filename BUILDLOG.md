# BUILDLOG — append-only session journal
Every AI session on this repo ends by appending one entry below. Newest at the bottom.
This file is the context bridge to the command center (the planning chat): after each
session, the latest entry (+ test output, + screenshot if visual) is what gets reported
back. Never paste chat transcripts anywhere.

---
ENTRY TEMPLATE (copy, fill, append):

## [YYYY-MM-DD HH:MM] · <tool: Claude Code | Antigravity> · <model>
- **Phase/Step:** P0.S2 (example)
- **Did:** files created/changed, one line each
- **Decisions made:** anything not literally dictated by the specs (and why)
- **Spec contradictions/gaps flagged:** none | description (→ goes to command center)
- **Verification:** tests run + results, or "not applicable"
- **Next:** the exact next step
---

## 2026-07-08 01:00 · Antigravity · Claude Opus 4.6
- **Phase/Step:** P0.S1 — Scaffold
- **Did:**
  - Created directories: `engine/`, `engine/schemas/`, `server/`, `web/`, `data/chats/`, `data/fixtures/`, `tests/` (with `.gitkeep` files)
  - Created `.gitignore` (Python, Node, `.env`, `data/chats/*/run/`)
  - Created `.env.example` (`ANTHROPIC_API_KEY=`)
  - Created `README.md` (3 lines, pointing at `docs/`)
  - Created `requirements-dev.txt` (`pytest`, `jsonschema`)
  - Initialized git, committed as `P0.S1`
- **Decisions made:** Added `data/fixtures/` directory (referenced by brief but not yet populated). Added `.venv/`, `venv/`, `web/dist/` to `.gitignore` as standard practice.
- **Spec contradictions/gaps flagged:** none
- **Verification:** `git status` clean after commit; `find` tree matches brief's spec
- **Next:** P0.S2 — The five schemas

---

## 2026-07-08 01:03 · Antigravity · Claude Opus 4.6
- **Phase/Step:** P0.S2 — The five schemas
- **Did:**
  - `engine/schemas/dialogue.schema.json` — turns array: pair, speaker, text, attachments, ts
  - `engine/schemas/state.schema.json` — actions, outcomes tree, intentions, requirements (full lifecycle), slots (full lifecycle), operations_log
  - `engine/schemas/ledger_row.schema.json` — single JSONL row per Pipeline Spec §10.3
  - `engine/schemas/snapshots.schema.json` — per-pair t, delta_you, delta_ai, c_you, c_ai
  - `engine/schemas/panel_bundle.schema.json` — per pair: direction, decisions, timeline (drawer with per-req masses + chips + slots), goal (default_view + full_tree), how (mode + signals + split)
  - Committed as `P0.S2`
- **Decisions made:**
  - `dialogue.json` and `snapshots.json` schema as arrays; `state.json` and `panel_bundle.json` as objects; `ledger_row` validates one JSONL line (not array) — matches artifact semantics
  - `operations_log` items include `target_type` (requirement|slot) to disambiguate ops — not in spec but needed for unambiguous querying
  - Goal `default_view` and `full_tree` nodes include `depth` field — needed for thread-collapse display rules
  - All fields marked required; `additionalProperties: false` everywhere — strict contracts
- **Spec contradictions/gaps flagged:**
  - `operations_log` structure not specified anywhere in the four docs — Architecture §3 mentions it as a state.json field but no schema is given. Designed it as chronological op records with pair/outcome_id/op/target_id/target_type. → goes to command center for validation
- **Verification:** All 5 schemas pass `Draft202012Validator.check_schema()` — valid JSON Schema draft 2020-12
- **Next:** P0.S3 — Build the fixture (assigned to Claude Code)
---

## 2026-07-08 01:35 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P0.S3 — Build the fixture
- **Did:**
  - Created `engine/scripts/build_fixture.py` to parse raw input ledger/results and write fixture files.
  - Generated `data/chats/fixture_pair1/ledger.jsonl`, `snapshots.json`, `panel_bundle.json`, `state.json`, `dialogue.json`, and `README.md`.
  - Staged and committed changes as `P0.S3`.
- **Decisions made:**
  - Joined multi-line action_id patterns (e.g. `U(1,\n1)` to `U(1,1)`) caused by copy-paste table formatting artifacts.
  - Derived requirement creators using the rule that within a pair, U actions precede A actions in chronological order (user speaks first).
  - Hardcoded verified panel metrics from `Stage 4 Pair 1 Results.md` into `panel_bundle.json` while verifying the ledger-derived numbers match exactly.
  - Stubbed missing texts in `state.json` and `dialogue.json` with `"(not captured in fixture)"` to preserve validity against Step 2 schemas.
- **Spec contradictions/gaps flagged:** none (arithmetic discrepancy between source chat inline calculations and raw ledger rows resolved: source chat calculations had minor summation errors, but the raw ledger rows were correct and matched corrected values in `Stage 4 Pair 1 Results.md`).
- **Verification:** Custom diagnostic Python script checks that parsed ledger rows sum to Δ_you = 87.0, Δ_AI = 314.0 and yield 4 U / 10 A creator split. All generated files successfully validate against their respective JSON schemas via jsonschema validation.
- **Next:** P0.S4 — The DoD tests
---

## 2026-07-08 01:45 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S1 — App scaffold
- **Did:**
  - Initialized a new React + Vite + TypeScript project inside the `web/` directory.
  - Installed `zustand` (for state management) and `lucide-react` (for icons).
  - Created Node sync script `web/scripts/sync-fixture.js` and registered `"sync-fixture"` in `package.json` to mirror fixture data into `web/public/fixture/`.
  - Configured custom CSS properties for styling variables (`--you`, `--ai`, `--bg`, `--panel`, `--font-sans`, `--font-mono`) and Google Fonts imports in `web/src/index.css`.
  - Cleaned default template layout rules and successfully ran `npm run build`.
  - Staged and committed changes as `P1.S1`.
- **Decisions made:**
  - Handled the existing directory by using the `--overwrite` flag with `create-vite`.
  - Created a modular Node sync script `sync-fixture.js` to ensure the static fixture asset copying is cross-platform.
  - Cleared `web/src/App.css` to prevent default Vite styling styles from interfering with the custom layout.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Ran `npm run sync-fixture` to confirm successful replication of dialogue, state, snapshot, and panel_bundle JSON files. Verified clean production build using `npm run build`.
- **Next:** P1.S2 — Layout shell
---

## 2026-07-08 01:50 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S2 — Layout shell
- **Did:**
  - Designed the three-column layout: sidebar (240px width), main chat area (flexible), and right-rail agency panel (360px width) in `web/src/App.tsx`.
  - Built the `InfoPopover` and `SectionHeader` components in `web/src/components/InfoPopover.tsx` to handle popovers.
  - Implemented popover interaction logic matching the prototype: mouse-click outside dismissal, Escape-key dismissal, click / Enter/Space key toggling, and proper ARIA role attributes.
  - Created Zustand state store in `web/src/store.ts` mapping the exact interface properties from Step 2's JSON schemas.
  - Added visual headers for all five rail panels (Goal, Direction, Decisions, Timeline, How) using verbatim text descriptions from the brief.
  - Staged and committed changes as `P1.S2`.
- **Decisions made:**
  - Placed popover trigger buttons inline and styled them similarly to the prototype's clean circle-info elements to ensure aesthetic symmetry.
  - Wrote specific inline styles within `App.tsx` and `InfoPopover.tsx` as adapted from the prototype code to reproduce the Figma prototype presentation.
  - Commented out unused destructured variables (`selectedPairIdx`, `panelBundle`, `activePair`) in `App.tsx` to pass the strict TypeScript compilation checks (`TS6133`).
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built the project with `npm run build` to confirm zero compiler errors. Manually verified popovers open, focus, and close correctly.
- **Next:** P1.S3 — Chat column
---

## 2026-07-08 01:58 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S2 — Layout shell (Refactoring for empty starting page)
- **Did:**
  - Redesigned the main chat area to support a premium blank cover page for unstarted chats: Sparkles icon, prompt heading ("What do you want to co-create with AI today?"), suggestion cards, and a centered input box.
  - Added empty state behavior for the right-rail panel: "Idle" status strip with 0/0 page counter, "Start a new chat" reminder in Goal section, and clean headers in the rest.
  - Wrote interactive click bindings on suggestion cards and the sidebar items to dynamically transition into the active pair-1 fixture view.
  - Staged and committed changes as `P1.S2` empty state update.
- **Decisions made:**
  - Added activeChatId state to Zustand store to easily toggle between clean blank layout and live loaded fixture.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Verified clean dev compilation and confirmed cards click-to-load transitions work correctly in the browser.
- **Next:** P1.S3 — Chat column
---

## 2026-07-08 02:04 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S2 — Layout shell (Sidebar and suggestions cleanup)
- **Did:**
  - Removed all pre-populated chat history items in the sidebar to ensure a completely blank starting experience.
  - Updated the suggestion cards to ask custom co-creative options: "want to help you build a website", "want to help you plan a trip", and "wanna help you writing a fantasy story".
  - Configured state to add the conversation to the sidebar list and transition to the loaded pair-1 fixture chat session once a card is clicked.
  - Staged and committed changes as `P1.S2` empty sidebar update.
- **Decisions made:**
  - Placed the starting conversation entry in components state (`conversations` in store.ts) to display list items only after they are generated.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and runs dynamically in the browser.
- **Next:** P1.S3 — Chat column
---

## 2026-07-08 02:05 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S3 — Chat column
- **Did:**
  - Rendered dialogues turns from `dialogue.json` dynamically in the chat column.
  - Implemented the `P` + `pair` badge (e.g. `P1`) for user messages, styled with the active pair's accent color (blue).
  - Highlighted active assistant message bubbles with a `1.5px` border matching the active pair's accent color.
  - Formatted turn timestamps from ISO strings to localized HH:MM time strings.
  - Staged and committed changes as `P1.S3`.
- **Decisions made:**
  - Derived the active pair's accent color dynamically based on whether you_pct > ai_pct (yielding blue or orange) to ensure correct visual styling on transition.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and runs dynamically in the browser.
- **Next:** P1.S4 — GOAL section
---

## 2026-07-08 02:07 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S4 — GOAL section
- **Did:**
  - Created component `web/src/components/GoalSection.tsx` and integrated it in `web/src/App.tsx`.
  - Implemented the thread-collapse layout rules to display root, collapsed chip rows (for d >= 3), previous nodes, and the current emphasized node.
  - Implemented recursive subtree rendering in expanded view (showing indicators, alignment margins, and L-shaped connector lines).
  - Hardcoded the 5-level deep DEV tree behind the `?devtree=1` flag to check all depth cases.
  - Staged and committed changes as `P1.S4`.
- **Decisions made:**
  - Automatically evaluated the hidden-node count dynamically by checking index depth differences in the default_view node list.
  - Created type-only imports for StoreGoalNode in `GoalSection.tsx` to compile cleanly with `verbatimModuleSyntax` rules.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors. Tested `http://localhost:5174/?devtree=1` in dev to confirm the thread-collapse chip `⌄ 2 more` renders and expands/collapses properly.
- **Next:** P1.S5 — DIRECTION + DECISIONS
---

## 2026-07-08 02:12 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S5 — DIRECTION + DECISIONS
- **Did:**
  - Implemented the user-vs-AI split bar (proportionally sized to you_pct/ai_pct in `direction`) and `@ P1` badge in the DIRECTION section card.
  - Implemented the decisions counter showing count of requirements created (`4 you vs 10 AI`), styled with brand colors (blue for you, orange for AI) and without separating dots per user preferences.
  - Added visual presentation for the latest AI-created decision statement, styled with a left border block in orange with 25% opacity.
  - Staged and committed changes as `P1.S5`.
- **Decisions made:**
  - Wrote a custom string helper `truncateClause` inside `App.tsx` that searches for common punctuation split markers (comma, period, semicolon, em-dash) to cleanly slice long decision strings at clause boundaries.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and renders the numbers: 21.7% / 78.3% split, @ P1 badge, and 4 you vs 10 AI decisions dynamically.
- **Next:** P1.S6 — TIMELINE
---

## 2026-07-08 02:16 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S5 — DIRECTION + DECISIONS (Redesign Variations)
- **Did:**
  - Implemented a live interactive toggle switcher (`Var A`, `Var B`, `Var C`) in the Decisions section header.
  - Implemented **Variation A (Big Split Cards)**: High contrast dashboards blocks displaying `4` and `10` in large typography inside user-vs-AI styled boxes, with a separate highlighted block for the latest decision.
  - Implemented **Variation B (Visual Progress Bar)**: Linear split tick bar with numbers on the left and right sides and bulleted timeline notes below.
  - Implemented **Variation C (Checklist Ledger)**: Structured 2-row table listing counts and creator origins with a light gray documentation snippet callout.
  - Staged and committed changes as `P1.S5` variations update.
- **Decisions made:**
  - Added live toggle switchers directly in the page to allow the user to preview all three designs live in their browser.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and runs dynamically. Clicked through `Var A`, `Var B`, and `Var C` to confirm correct toggling.
- **Next:** P1.S6 — TIMELINE
---

## 2026-07-08 02:18 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S5 — DIRECTION + DECISIONS (Locked to Var A)
- **Did:**
  - Removed the visual switcher pill toggles (`Var A`, `Var B`, `Var C`) and cleaned up the `decisionsVar` React state.
  - Locked the DECISIONS card representation to **Variation A (Big Split Cards)**: side-by-side user and AI metric widgets displaying large numbers (`4` and `10`) inside low-opacity tinted cards, followed by a shaded card highlighting the latest AI requirement.
  - Staged and committed changes as `P1.S5` lock.
- **Decisions made:**
  - Standardized the decisions card layout based on the user's explicit preference for Variation A.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and displays only Variation A in the rail.
- **Next:** P1.S6 — TIMELINE
---

## 2026-07-08 02:20 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE
- **Did:**
  - Created component `web/src/components/TimelineSection.tsx` and integrated it in `web/src/App.tsx`.
  - Rendered the collapsed turn row with the `P1` label, turn-delta micro-spine (horizontal proportional bars), turn summary text, and open/close drawer chevrons.
  - Implemented the expanded drawer:
    - Requirements Changed: vertical timeline spine with absolute-positioned colored R-chips (13 grey, 1 orange `R11` for `o5/r2`) and inline proportional influence bars.
    - Open Questions: 5 dashed circles with `S1` through `S5` labels showing AI-origin open slots.
  - Wired row clicks to update the store `selectedPairIdx` state.
  - Staged and committed changes as `P1.S6`.
- **Decisions made:**
  - Standardized slot labels to sequential indices (`S1` to `S5`) to render distinct question nodes.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and runs dynamically. Confirmed expand/collapse chevrons toggle the drawer properly.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 02:38 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Chart Redesign)
- **Did:**
  - Redesigned the expanded Timeline drawer layout into a diverging bar chart matching the Spotify timeline SVG references.
  - Centered circular R-badges (R1 through R14) directly on the dashed vertical timeline axis.
  - Rendered blue user bars growing left, and orange AI bars growing right, proportional to each requirement's delta mass values.
  - Placed requirement name labels next to the bars: user-weighted labels on the left, and AI-only labels on the right.
  - Added a visual legend box in the top right outlining User-shaped, Straddling, AI-created, Open slot styles, and scale info.
  - Implemented Level-2 expansion details inline card below the SVG chart that dynamically loads requirement texts and extraction rationales upon clicking any requirement row.
  - Staged and committed changes as `P1.S6` chart update.
- **Decisions made:**
  - Statically mapped descriptive text labels (e.g. "squid anim", "workflow rules") to R1..R14 indices matching the user's Figma prototype mockups.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors. Tested clicks on requirements to confirm Level-2 details show/hide smoothly.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 02:43 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Color Scheme Refinement & Cleanup)
- **Did:**
  - Removed dark background colors (`#121212`) from the expanded Timeline drawer to match the rest of the application's light panel color scheme.
  - Removed extra header elements (`9 refs + whiteboard` pill and the `Exchange 1` banner) per user instructions.
  - Removed the visual legend block from the top right corner.
  - Removed the `OPEN QUESTIONS` slots (`S1` through `S5`) section.
  - Shifted the SVG viewport size to fit only the vertical spine line and the diverging bar rows (R1 to R14).
  - Staged and committed changes as `P1.S6` light theme update.
- **Decisions made:**
  - Conformed layout precisely to the user's annotated red-line corrections.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors. Renders perfectly in the light layout.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 02:45 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (HTML Accordions & Silent Chart Refactoring)
- **Did:**
  - Removed all text labels from the diverging bar chart to keep the visual representation clean and quiet.
  - Refactored the chart layout from SVG to HTML flex row blocks for better layout responsiveness and layout integrity.
  - Implemented an accordion dropdown mechanism on each requirement row: clicking a row toggles a details block right below it.
  - Re-positioned the dashed vertical timeline axis to run continuously through the center of all HTML rows.
  - Staged and committed changes as `P1.S6` accordion update.
- **Decisions made:**
  - Standardized on HTML flex columns instead of SVGs for diverging timeline rows to allow easy dropdown transitions.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors. Tested row clicks to ensure the details card slides open smoothly.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 02:49 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Layout Spacing & Spine Refinements)
- **Did:**
  - Removed empty visual gaps between the horizontal diverging bars and the central R-badge circles. Bars now extend directly to the center line (50%).
  - Enhanced the central vertical timeline spine to be a solid gray line (`rgba(0, 0, 0, 0.22)`) making it clearly visible in the light theme.
  - Sized circular R-badge masks with a matching panel outline border to sit cleanly on top of the vertical spine line.
  - Increased the maximum horizontal bar width scaling factor to 135px to fill the space cleanly and improve readability.
  - Staged and committed changes as `P1.S6` layout alignment update.
- **Decisions made:**
  - Standardized on absolute vertical spine line layouts behind center-aligned HTML flex containers to simulate a gap-free continuous timeline trace.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and renders the gap-free diverging chart cleanly.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 02:57 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Interaction Indicators & Sub-Header Info)
- **Did:**
  - Added a visual sub-heading `"Requirements"` at the top of the expanded timeline drawer.
  - Registered and integrated a new info popover key `"REQUIREMENTS"` in `InfoPopover.tsx` explaining bar directions, R-badges, and click-to-expand details.
  - Positioned tiny chevron indicators (`ChevronDown` / `ChevronUp`) on the far right of each requirement row to clarify that they are clickable and collapsible.
  - Staged and committed changes as `P1.S6` interaction affordance update.
- **Decisions made:**
  - Placed the chevrons on the absolute right margin (`right: 12px`) to prevent visual overlap with long horizontal bars.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and renders the popovers and indicator chevrons perfectly.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 02:59 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Spine Alignment & Popover Relocation)
- **Did:**
  - Standardized the horizontal coordinate of the vertical axis spine to exactly 71px.
  - Aligned the collapsed row micro-spine and the expanded drawer requirement spine on the same 71px line, creating a single continuous vertical axis line.
  - Removed borders and margins separating the header row and drawer to make the visual flow seamless.
  - Positioned the `"Requirements"` sub-heading to sit on the right of the spine (`left: 86px`) inside the drawer to prevent spine overlap.
  - Added an `align` prop to `InfoPopover.tsx` to force left-alignment (`align="left"`) for the Requirements popover so it opens to the right and stays inside the rail boundaries, preventing layout blockage.
  - Adjusted row-hover carets with lower default opacity.
  - Staged and committed changes as `P1.S6` spine alignment update.
- **Decisions made:**
  - Aligned spines at 71px calculated directly from the collapsed header left content widths to create a seamless vertical line.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and displays the continuous vertical spine cleanly.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 03:02 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Panel Centering Spine & Grid Alignment)
- **Did:**
  - Centered the vertical timeline spine line exactly at 50% width of the panel.
  - Positioned the collapsed row micro-spine canvas and the expanded drawer timeline spine at the center (50%), creating a perfect continuous vertical axis line down the exact middle of the panel.
  - Positioned the collapsed row summary text and the expanded drawer "Requirements" sub-header to start at the exact same horizontal coordinate (50% + 20px).
  - Staged and committed changes as `P1.S6` centering update.
- **Decisions made:**
  - Standardized on panel-relative percentage values (50%) for the spine coordinates to ensure grid alignment across all browser widths.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and displays a perfectly centered continuous spine.
- **Next:** P1.S7 — HOW
---

## 2026-07-08 03:04 · Antigravity · Gemini 3.5 Flash
- **Phase/Step:** P1.S6 — TIMELINE (Header Restoration & Sub-Header Alignment)
- **Did:**
  - Reverted the collapsed `P1` row layout to its original flex layout (left-aligned coordinate, offset micro-spine, next summary description).
  - Left-aligned the expanded `"Requirements"` sub-header in the drawer to `left: 16px` to keep it clean and offset from the centered timeline spine.
  - Kept the requirement rows' vertical spine centered at exactly 50% width of the panel.
  - Staged and committed changes as `P1.S6` header restore.
- **Decisions made:**
  - Standardized on restoring standard sidebar headers to maintain visual consistency across all panel sections.
- **Spec contradictions/gaps flagged:** none
- **Verification:** Built and verified the dev app compiles with zero errors, and displays the original collapsed header layout alongside the centered timeline chart.
- **Next:** P1.S7 — HOW
---



















