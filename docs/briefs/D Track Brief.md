# D_TRACK_BRIEF.md — The Design System Programme

A parallel workstream, run as co-creation between the owner and an AI, with the same
discipline as the engine track: phases, one step at a time, a gate at every decision,
everything written to the repo. It uses the `ui-craft` skill (`ui-craft/SKILL.md`) for
exploring, locking, building and checking anything that renders.

**Role:** DESIGN SYSTEM (section 13)
**Tools:** Claude Code is preferred for exploration and critique, because it can run
isolated sub-agents and show pages in its browser pane. Codex or Antigravity work well
for building, scaffolding and audits. Any of them can continue, because the repo carries
all context.
**Owner involvement:** high. The owner makes every decision. The AI researches, proposes,
renders, critiques and records.
**Depends on:** nothing. Starts now.
**Feeds:** G1 (the graph view lock, D0.S5, and graph tokens, milestone M1), every later UI
phase, and every future surface (section 11).

---

## 1. What this programme is for

The product currently has three unrelated visual worlds:

| Where | Look | Party colours | Type |
|---|---|---|---|
| `web/` panel (`web/src/index.css`) | Warm off-white paper, light | blue `#0057FF`, orange `#E85A0A` | Inter, DM Mono |
| `design_pack/` graph prototypes | Near-black "obsidian", dark | cyan `#38bdf8`, amber `#fb923c` | System sans |
| `AI Chatbot Interface (Copy)/` | Stock shadcn default theme | none | shadcn defaults |

And firm rules scattered across specs: blue is you and orange is the AI, left is yours and
right is the AI's, no third accent may take a side (`PANEL_SPEC.md`); colours are law
(`Build Playbook.md` §5); no textual state labels in the panel (`PANEL_SPEC.md` §0); every
encoding in the graph traces to data (`GRAPH_SYSTEM_SPEC.md`).

The `ui-craft` detector already flags three things in today's UI (run 8 Oct 2026): Inter
as an overused face (`web/src/index.css`), width animations that cause layout jank
(`TimelineSection.tsx`, the graph prototype), and a coloured glow on a dark page (the
graph prototype). That last one is the heart of the owner's graph design, so it is a real
question for D2 and D5, not an automatic fix.

This programme turns all of that into **one designed system**: a foundation of tokens, a
visual language for data, components, patterns and documentation. It must be good enough
to stand next to the best product teams, and built so that:

- any future surface (browser side panel, in-chat widget, 3D head, print, mobile) inherits
  it without a redesign
- any AI agent, in any new chat, can read it and build correct UI on the first try
- every decision is written down with its reasons, so nobody re-argues it later

### Design for the Brain, build for the graph

The destination is the **Human × AI Co-Creation Brain** (`docs/Brain Vision.md`): one
living map of all of a person's work with AI, zoomable from the whole history down to a
single exchange and its original words. The first thing built is far smaller: one chat's
node graph (G1). The order of work follows from that:

- **Designed now, for the whole Brain:** identity, mood, principles, the two party
  colours, the encoding grammar across every zoom level, the token architecture, motion
  language, and the workspace shell.
- **Built piece by piece:** components and surfaces, starting with the graph view.

Nothing decided for the graph may block the Brain. Every D1–D5 decision is tested
against the whole zoom ladder (section 7), not only against today's screen.

**What the foundation must be ready for** (each checked at the phase that settles it):

| # | Requirement | Settled in |
|---|---|---|
| F1 | Two party colours that mean human and AI at every level and on every surface, never anything else; distinguishable under colour-vision deficiency; no good-or-bad meaning; and readable when *mixed* in proportions (a region that is 60/40) | D4.S1 |
| F2 | One encoding grammar: each visual channel means one thing at every zoom level (resolves Brain Vision §4 against `GRAPH_SYSTEM_SPEC.md`) | D5.S1 |
| F3 | Semantic zoom: level-of-detail tiers saying what appears at each level, label density rules, and continuity, so zooming feels like moving through one object | D3, D5.S2 |
| F4 | Steering vs carrying the work shown as different things, not word count | D5.S1 |
| F5 | Geometry for change (bend, branch, merge) rather than labels | D5.S3 |
| F6 | A consistent "trace to source" affordance on every visible mark | D5, D6 |
| F7 | Visible evidence strength for links (similar < continued < reused) and for certainty (provisional < audited) | D5.S4 |
| F8 | Scale: 313 chats and 2,759 pairs today (median 2, max 242), thousands later. Calm when crowded, readable inside a 242-pair chat | D5.S2 |
| F9 | 2D and 3D from the same tokens: numeric export, light, material, depth | D3, D4.S4 |
| F10 | Every surface in Brain Vision §9 (web, side panel, in-chat widget, coding sessions, 3D, print), each showing its own levels | D3, D6.B4 |
| F11 | The workspace shell: Brain tab, chat tabs, left sidebar, right panel switching Map and Pair | D6.B4 |
| F12 | Identity: the Human × AI head as a motif, never anatomy, never implying a measured brain; calm, alive, traceable | D1, D2.S5 |

---

## 2. How we work: the co-creation loop

Every step runs the same eight moves. It is the design equivalent of "one step per
response, start task, Finish Step". The right column says which `ui-craft` mode does the
heavy lifting.

| Move | Who | What happens | ui-craft |
|---|---|---|---|
| **1 Frame** | AI | The question, the fixed constraints (laws), what depends on it, what "good" means. Written as the skill's design brief (job, audience and setting, direction, signature move, density, constraints, anti-references) | `design-rules.md` brief |
| **2 Gather** | AI, owner adds | 5–12 references, each with *what it teaches us*, plus the real data the decision touches | — |
| **3 Diverge** | AI | 2–4 genuinely different options, rendered on the same real content (section 7), each with rationale, the psychology behind it, risks and cost to future surfaces | `lock` steps 2–6: grounding kit, brief, shared scaffold, one sub-agent per concept (`variant-agent-prompt.md`), render |
| **4 React** | Owner | Likes, dislikes, sketches, questions. Paper first is always allowed; the AI works from a photo | — |
| **5 Converge** | AI | Honest critique of every option, including its own, then a refined option or merge. At most two rounds | `critique` (heuristics, cognitive load, persona walk, detector). `consensus` for a split between user situations (advisory) |
| **6 Decide** | Owner | `Decide: <option>` | — |
| **7 Encode** | AI | Decision record (DDR), tokens, specs. For a whole surface, the lock manifest too | `lock` step 9 for surfaces |
| **8 Verify** | AI | Contrast, colour deficiency, token lint, detector, render; screenshots | `audit`, `detect.mjs` |

Then `Finish Step`, a BUILDLOG entry, and an update to `STATE.md`.

**Rules of the loop**

1. **The owner decides; the AI proposes.** Nothing is recorded as accepted without the
   owner's own words, quoted in the DDR. `consensus` panels are advice, never a decision.
2. **Options must really differ** in concept: hierarchy, layout metaphor, interaction,
   density. Three colour variants of one layout count as one option (skill rule).
3. **Always render; never just describe.** Judged on real content in a browser.
4. **Honest critique.** The AI names real problems in any option, the owner's favourite
   included, and cites the principle or check.
5. **Real data, under the protocol in section 5.**
6. **Laws stay laws until the owner changes them** in a DDR.
7. **One decision per step.**

**Words that move the process:** `start task` · `Decide: <option>` · `Finish Step` ·
`Revisit DDR-NNN` (reopen a system decision) · `resettle <surface> <term>` (change a
locked surface term, skill mode).

---

## 3. Which ui-craft mode at which step

| Mode | What it gives us | Where it's used | Compulsory? |
|---|---|---|---|
| `init` | Interview in rounds of 2–3 questions → `PRODUCT.md` and 3 reviewer personas with a tie-break ranking | D1 | Yes, it is D1 |
| `lock` | Grounded variants on a shared scaffold, converge, then a ★ LOCKED mock and a checkable manifest | D2 directions; D6 and D7 for every surface; D0.S5 graph view v0 | Yes for surfaces |
| `critique` | Nielsen scores, cognitive load, AI-slop verdict, persona walkthroughs, detector, saved snapshot | Converge move; every phase gate | Yes at gates; optional between |
| `consensus` | 3 personas vote and negotiate a contested choice | Only when a decision splits user situations (e.g. party colours, density) | Optional |
| `audit` | Technical scores: a11y, performance, theming, responsive, anti-patterns | Verify move; D4, D6, D8 | Yes at D4, D6, D8 |
| `behavior-sweep` | Freezes what an interactive surface *does* (hover, scrub, keys) before building | After each interactive lock: graph view, timeline, scrubber | Yes for interactive surfaces |
| `build` | Implements a lock; finish line is evidence for every manifest term | D6; G1 S6 (APP) | Yes for locked surfaces |
| `polish` | Final pre-ship pass, aligned to the system | End of each D6 batch; G1 S8 | Yes before a release |
| `resettle` | The only way to change a locked term, with records | Whenever a lock must change, e.g. graph v0 → real tokens | When needed |
| `document` | Generates `DESIGN.md` (agent-readable summary with token frontmatter) | Seed after D2; generated from tokens after D4; final at D8 | Yes at D8 |
| `palette.mjs` | A mood-tagged colour seed | Optional input to D2's third direction and D4.S1 neutrals | Optional |
| `detect.mjs` | Deterministic anti-pattern scan of HTML and JSX | Every Verify move | Yes, it's cheap |

**DDRs vs locks.** A DDR records a *system* decision (a token, a principle, a rule). A
lock records a *surface* (a screen or component) as a checkable contract. A lock cites the
DDRs it depends on; a resettle cites the DDR that caused it.

---

## 4. Where things live

```
PRODUCT.md and DESIGN.md      in docs/ (the skill's context loader finds them there)
.claude/qa/personas/          the 3 reviewer personas and RANKING.md (from init)
.claude/skills/ui-craft       symlink to ui-craft/ so Claude Code discovers the skill
.impeccable/                  critique and consensus snapshots (committed: design history)

mockups/                      everything you look at, served by one local server
  INDEX.md                    surface ledger: Surface / Concept / Status / Issue / File
  index.html                  generated page linking every mock, with status
  _theme.css                  GENERATED from tokens.css once D3 exists ("extract, never
                              transcribe"); before that, a neutral placeholder
  _shell.js, SCAFFOLD.md      shared mock bar (theme, state, density) and capture loading
  captures/                   c05 and friends as JSON fixtures (section 5)
  foundations/                D4 specimens: color.html, type.html, motion.html …
  <surface>-<concept>.html    D2 directions and D6 surface variants
  <surface>.lock.md           lock manifests
  <surface>.behavior.md       frozen behavior ledgers

docs/design-system/
  README.md                   start here for any new chat
  STATE.md                    phase, step, open decisions, next step
  AGENT_GUIDE.md              rules for any AI building UI with the system
  decisions/                  DDR-NNN-<slug>.md and INDEX.md
  research/                   references (links + lesson), teardowns; _local/ gitignored
  foundations/                color.md, type.md, space.md, shape.md, motion.md,
                              icons.md, a11y.md, voice.md, dataviz.md, architecture.md
  surfaces/                   web, side panel, in-chat widget, 3D, print

web/src/design-system/
  tokens/tokens.json          single source of truth (DTCG format, section 8)
  tokens/build.mjs            → tokens.css, tokens.ts, tokens.numeric.json, DESIGN.md frontmatter
  components/                 built components (React + TypeScript, CSS custom properties)
  gallery/                    dev-only route: every token and component, both themes
```

**Public repo caution:** third-party screenshots go only in
`docs/design-system/research/_local/` (gitignored).

---

## 5. Adapting ui-craft to this repo (decided in D0, recorded as DDRs)

The skill has defaults that clash with this project. Each is settled once, up front:

| # | Skill default | This project | Settlement |
|---|---|---|---|
| A1 | Mocks use manufactured fixtures, never personal data, unless `AGENTS.md` declares a real-data protocol | Real chats are the main design constraint | **Owner adds a real-data protocol to `AGENTS.md`** (text below). Only the ten processed chats in `data/chats/`, all already committed and non-sensitive. Never `data/archive/`, `data/exports/`, or anything flagged `sensitive` |
| A2 | The shipped app is chrome ground truth for new mocks | Today's panel is a prototype that this programme replaces | DDR-000 states the system is pre-v1 and nothing has shipped. After `ds-1.0` lands in `web/`, the app becomes ground truth, as the skill expects |
| A3 | `DESIGN.md` has six fixed sections and holds the tokens | We need a three-tier DTCG token set and deeper foundations | `tokens.json` is the source. `DESIGN.md` is generated from it as the summary every agent reads. `foundations/` holds the depth |
| A4 | Coloured glow on dark is banned as an AI tell | The owner's graph uses dual-light glowing spheres | The detector reports it; the owner decides in D5 whether the glow stays, changes, or goes. Not auto-fixed |
| A5 | Touch targets 44 px (audit) | WCAG 2.2 AA requires 24 px | 24 px is the floor everywhere; 44 px for touch surfaces |
| A6 | Rendering via a `drive-local-webapp` skill (not installed) | Claude Code has a browser pane; others have Playwright | Use the browser pane, or a Playwright script in `scripts/design_system/` |
| A7 | `critique` needs two isolated sub-agents | Codex and Antigravity may not have them | Run `critique` in Claude Code. Elsewhere it runs with the skill's `⚠️ DEGRADED` banner, accepted only between gates |
| A8 | Skill files carry an Apache-2.0 attribution to a NOTICE that isn't in `ui-craft/` | Public repo | Add the upstream NOTICE and licence to `ui-craft/` before committing it |

**Real-data protocol text for `AGENTS.md` (owner adds, P2 below):**

```
## Real-data protocol for design work
Design mocks may use the owner's own processed chats in data/chats/ (the ten E1 corpus
chats and golden_01). Nothing from data/archive/, data/exports/, data/Takeout*, or any
entry flagged sensitive. Mocks link fixtures from mockups/captures/, generated by
scripts/design_system/capture.py, never hand-copied. Brain-level mocks may use the titles,
lengths and task types of data/corpus/ entries, and owner-asserted region and link
labels marked "design fixture, not engine output".
```

---

## 6. The science we design with

Every proposal names which of these it relies on.

| Principle | What it says | Where it bites here |
|---|---|---|
| **Pre-attentive attributes** (Treisman) | Hue, size, motion and enclosure are seen in under ~250 ms, before reading | Party is hue. Mass is size. Motion is reserved for *change*. No decoration may use these channels |
| **Ranking of visual channels** (Cleveland & McGill) | Position and length are judged far more accurately than area or colour intensity | The direction split stays a bar, not a pie or a glow. Node size is for gist, never exact comparison |
| **Area perception** (Stevens' power law) | People underestimate area differences | D5 chooses radius ∝ √mass (area-true) or another rule on purpose. The prototype uses √; the spec text says linear |
| **Gestalt grouping** | Proximity, common fate and enclosure group things without lines | Atoms orbit their node; things that change together animate together |
| **Colour vision deficiency** | About 8% of men and 0.5% of women; red and green are the classic confusion pair | Blue and orange is the classic deficiency-safe pair. Every palette is simulated |
| **Contrast** (WCAG 2.2) | 4.5:1 body text; 3:1 large text and meaningful non-text marks | Thin tethers and dormant states easily fail 3:1 |
| **Target size** (WCAG 2.2 §2.5.8, Fitts's law) | Targets at least 24 × 24 px | Beads are 3.5–5.8 px in the graph spec. They need invisible hit areas |
| **Choice overload** (Hick's law) | Decision time grows with options | One current goal in the side panel, not the tree |
| **Calm technology** (Weiser & Brown) | Peripheral information informs without demanding attention | The panel sits beside someone's work: glanceable, quiet when nothing changed |
| **Colour valence** | Red and green read as bad and good | You vs AI carry no good-or-bad meaning ("a mirror, not a judge") |
| **Calibrated uncertainty** | False precision destroys trust | Provisional values look provisional; no unsupported decimals; confidence is shown |
| **Autonomy** (self-determination theory) | People resist interfaces that take control | Nothing yanks the user out of HISTORY; motion never steals focus |

The skill adds its own craft rules (`ui-craft/reference/design-rules.md`): the absolute
bans, the slop test, motion durations by frequency, and "dark vs light is never a default".
They apply to every step.

---

## 7. The standard specimen: the zoom ladder

Every exploration renders the same real content at every level, so options compare like
for like and nothing is designed for one level alone:

1. **Brain:** the 59 corpus chats grouped into regions. Region labels and cross-chat links
   are a **design fixture asserted by the owner** (the engine has no cross-chat layer
   yet), marked as such on the page.
2. **Project:** one region opened (for example research), its chats and links.
3. **Chat, two views:** c05 as a trajectory through its 7 pairs, and c05's outcome map at
   pair 4 (root, five outcomes, beads, a ring, a bullseye, the focus halo).
4. **Pair:** c05 pair 2, where the user resolved the AI's question by bridging both angles.
5. **Source:** the original user and AI messages of that pair.
6. **Side panel:** 380 px with the chat map and pair views for the open chat.
7. **Stress:** the longest corpus chat, and a crowded brain at 313 chats with titles only.

Every page in both themes and under colour-deficiency simulation. A direction or
foundation choice that only works at one level fails.

**How you look at it, at every step:**

- **One local server for everything.** `.claude/launch.json` gets a `mockups` entry, so
  in Claude Code the page opens in the browser pane next to the conversation. Any other
  tool runs `python3 -m http.server 4178 --directory mockups`.
- **`mockups/index.html`** lists every mock with its step, status and DDR.
- **The mock bar** on every page switches theme, state, density, pair and the
  colour-deficiency filter.
- **Side by side.** Each Diverge move puts its options on one comparison page, so you
  react to them together.
- **From D3 on, the gallery route** in the web app shows the real tokens and components
  live.
- **Optional:** publish a page as a private Claude artifact to look at it on your phone,
  or push a locked mock to Figma for annotation. The repo stays the source of truth.

---

## 8. The foundation, built to last

These parts make the system work for surfaces that don't exist yet. D3 decides each one
with options. The defaults below are a starting recommendation, not decisions.

**Token tiers**

| Tier | Example | Who uses it |
|---|---|---|
| Primitive | `color.blue.600`, `space.4`, `duration.200` | Only the semantic tier |
| Semantic | `color.party.user`, `color.surface.raised`, `motion.change.birth` | Components and surfaces |
| Component | `graph.node.radius.max`, `scrubber.notch.current` | That component only |

**Single source, standard format.** `tokens.json` in the W3C Design Tokens Community
Group (DTCG) format generates: `tokens.css` (web, side panel, in-chat widget),
`tokens.ts` (typed access for React and canvas), `tokens.numeric.json` (WebGL and the 3D
head), the `DESIGN.md` frontmatter (for every skill-aware agent), and later Swift, Kotlin
and Figma variables.

**Themes as modes, not forks:** light, dark, high-contrast; comfortable and compact
density; print. All are modes of the same semantic tokens.

**Host adaptation:** inside ChatGPT or Claude (MCP Apps) and browser side panels, which
tokens follow the host (ground, text) and which never do (party colours).

**Versioning:** semantic versions. Renaming or removing a token is a breaking change with
a DDR and a major version. A release-diff script lists what broke.

**No literals** outside `tokens.json`. The token lint and the skill's `audit` theming
score enforce it.

---

## 9. Phases

Each phase closes with: DoD checked for real, `critique` on the phase's output, BUILDLOG
entry, `STATE.md` updated, tag. Durations are rough, in working sessions with the owner.

### D0 — Charter, audit and setup · 2 sessions

- **S1 Audit.** Inventory every visual decision in the repo (tokens, colours, fonts,
  spacing, components, visual rules in specs), plus `detect.mjs` and `audit` on `web/`
  and `design_pack/`. Output: `research/AUDIT.md` with a conflicts list. The first entry
  is the party colours.
- **S2 Scope.** Surfaces (section 11) and the components implied by `PANEL_SPEC`,
  `INTERACTION_SPEC` and `GRAPH_SYSTEM_SPEC`. A first inventory with priorities.
- **S3 Setup.** The section 4 folders; `README.md`, `STATE.md`, the DDR template,
  `decisions/INDEX.md`; DDR-000 (co-creation with an AI is the owner's deliberate choice;
  the system is pre-v1, settlement A2); the A1–A8 settlements as DDR-000a–h;
  `.gitignore` entries; the `mockups` entry in `.claude/launch.json`.
- **S4 Scaffold and captures.** `scripts/design_system/capture.py` turns `data/chats/c05`
  (and others) into `mockups/captures/*.json`. Build `mockups/_theme.css` (neutral
  placeholder), `_shell.js`, `SCAFFOLD.md` and `index.html` per the skill's `lock` step 4.
  Add the checks: contrast, colour-deficiency simulation, token lint.
- **S5 Graph view v0 lock (for G1).** No exploration: the owner already designed it.
  Run `lock` with a single concept, the owner's prototype with G1 Brief fixes D1–D8
  applied, on fallback tokens. Owner approves, then `behavior-sweep graph-view`.
  **HANDOFF** to APP for G1 S6.

**DoD:** audit and conflicts reviewed; captures and scaffold render c05; checks run;
`graph-view.lock.md` and `graph-view.behavior.md` frozen.

### D1 — People, moments and principles · 2–3 sessions · `init`

- **S1 Interview round 1:** register (product), users and moments (glancing at the side
  panel mid-work, reviewing a chat afterwards, showing someone, a student reflecting, a
  developer reviewing an agent's decisions), desired outcomes.
- **S2 Interview round 2:** personality on rendered scales (calm ↔ energetic, instrument ↔
  companion, technical ↔ humane, quiet ↔ expressive, organism ↔ machine, observatory ↔
  notebook), feelings to create and avoid at each zoom level, anti-references (Brain
  Vision §7 is the first list), accessibility needs.
- **S3 `PRODUCT.md`:** purpose, users, personality, anti-references, 5–7 principles each
  with a test that can fail, accessibility. Likely candidates from the vision: "A mirror,
  not a judge", "Every mark traces to its source", "Geometry, not labels", "One colour,
  one party, everywhere", "The engine is complex; the picture is simple".
- **S4 Personas:** 3 situations with lens, job and concrete red flags, plus `RANKING.md`.
  Likely: the mid-work glancer, the after-session reviewer, the agent-decision auditor.

**DoD:** `PRODUCT.md` and personas accepted; DDR-001 records the personality.

### D2 — References and directions · 3–4 sessions · `lock`, `critique`, `consensus`

- **S1 Reference hunt.** Knowledge graphs (Obsidian, Heptabase, Kumu), scientific
  instruments and observatories, editorial data visualisation, AI tools (Linear, Claude,
  ChatGPT, Cursor), calm and ambient interfaces, print and cartography. One line per
  reference on what it teaches.
- **S2 System teardowns.** Material 3, IBM Carbon (with its data-viz guidance), GitHub
  Primer, Vercel Geist, Atlassian, Apple HIG, Radix Colors: what to borrow, what to reject.
- **S3 Three directions** across the whole zoom ladder (section 7), one sub-agent each. A
  direction is a world that holds from the brain down to the transcript, not a style
  for one screen. A starting set
  the AI should challenge: **paper instrument** (today's light panel, taken further),
  **obsidian observatory** (today's dark graph, taken further), and **a third direction**
  neither world suggests (`palette.mjs` seed allowed).
- **S4 Converge.** `critique` on each, the owner reacts, `consensus` if the personas split,
  at most two rounds, then `Decide`. DDR-002 records the direction. `document --seed`
  writes a first `DESIGN.md`.
- **S5 Identity: name and mark.** The product's name is not settled: the README says
  "Agency Panel", the engine follows the COTRACE paper's name, and the vision says "Human ×
  AI Brain". Explore names and a mark built on the head motif (F12), in the chosen
  direction. DDR-003.

**DoD:** one direction accepted, rendered at every level of the ladder in light and dark;
name and mark decided; critique snapshots saved.

### D3 — Foundation architecture · 2 sessions

One step per section 8 decision: tiers and naming grammar; source format and outputs;
theme and density modes; host adaptation; versioning. Plus two for the Brain: **zoom
tiers** (level-of-detail names that every component can respond to: brain, project,
chat, pair, source) and **spatial tokens** (camera, depth, light and material values that
2D canvas and 3D share, F9). Each as options → decision → DDR.

Then build `tokens.json` (skeleton), `build.mjs`, the generated outputs, the release diff,
and switch `mockups/_theme.css` to be generated from `tokens.css`. A build dependency
(for example Style Dictionary) goes through `SPEC_QUESTIONS.md`; a small hand-written
`build.mjs` needs none.

**DoD:** one file generates every output; lint fails on a planted literal; the release
diff fails on a planted rename; mocks re-render from generated tokens.

### D4 — Foundations · 6–8 sessions, one per step · specimens in `mockups/foundations/`

| Step | Decides | Must pass |
|---|---|---|
| S1 Colour | Neutrals and their hue bias; party colours (**resolves the conflict** among three candidates: blue and orange from the Playbook, cyan and amber from the graph spec, cyan and violet from the Brain notes); semantic states; data scales | Contrast in all themes; parties distinct under all three deficiency simulations (cyan and violet are at risk for tritan); no red or green; **mix test**: 50/50, 70/30 and 90/10 regions stay legible as proportions, without a muddy midpoint |
| S2 Typography | Faces (UI, data, display), scale (1.125–1.2 for product UI), weights, tabular numbers | Legible at 11 px in the side panel; umlauts and long German words; not on the detector's overused list unless the owner overrides with reasons |
| S3 Space, size, layout | Spacing scale, grid, breakpoints including the 360–420 px side panel, z-index scale | No horizontal scroll in any specimen |
| S4 Shape and depth | Radius, borders, elevation, translucency | Graph spheres and UI surfaces don't compete; no nested cards |
| S5 Motion | Durations by frequency, easing, choreography for birth, dormancy, reactivation, resolution and scrub, reduced-motion versions | Motion only signals change; transforms and opacity, never width (today's detector finding) |
| S6 Icons | Style, grid, stroke, set | Recognisable at 16 px |
| S7 Accessibility | WCAG 2.2 AA floor, targets (A5), focus rings, keyboard model for the graph | `audit` a11y score ≥ 3 on the specimen |
| S8 Voice and UX writing | Tone, terms (goal, decision, open question, you, the AI), number formats, errors | No judgemental words; terms match the specs |

Then `document` regenerates `DESIGN.md` from the tokens.

**DoD:** every foundation has a page and a specimen; tokens filled in all themes; `audit`
theming score 4; checks green.

### D5 — The visual grammar across the zoom ladder · 4–6 sessions

The product's heart: how the engine's measurement becomes something a person sees,
consistently from the brain to the transcript. Run with the owner's chosen method (Brain
Vision §10): real pairs one at a time, starting with c05.

- **S1 One grammar (F2, F4).** A channel table that holds at every level: colour → who,
  and then position, size, thickness, geometry and proximity, each with exactly one
  meaning. Reconcile `GRAPH_SYSTEM_SPEC.md` (size = mass) with Brain Vision §4 (size =
  significance, thickness = contribution). Show steering and carrying the work as
  different things. Settles A4 (glow). Changes to the graph spec are DDRs the owner signs.
- **S2 Semantic zoom and scale (F3, F8).** What is visible at each level; when labels
  appear; how 313 chats stay calm; how a 242-pair chat compresses (beats); hit areas for
  small marks; how the camera moves between levels.
- **S3 Change as geometry (F5).** Continue, redirect, branch, merge, output, open
  question, return. Each drawn only once a real pair needs it.
- **S4 Honesty (F6, F7).** Trace-to-source affordance; link evidence strength; provisional
  vs audited; confidence; uncertainty never hidden.
- **S5 The head (F12).** Its role at the brain level, 2D and 3D, how it frames without
  implying anatomy.
- **S6 Graph token contract.** Every token in G1 Brief section 6, in all themes, consistent
  with S1. Then `resettle graph-view` moves the v0 lock to real tokens.

**Milestone M1:** HANDOFF to APP. G1 swaps its fallback file for the real tokens.

**DoD:** `foundations/dataviz.md` accepted; the whole zoom ladder specimen renders in the
grammar, in both themes; `critique` with all three personas at brain, chat and pair
levels; G1 token contract complete.

### D6 — Components and surfaces · 8–12 sessions, in batches

Per component: anatomy → variants → states (default, hover, focus, active, disabled,
loading, empty, error) → tokens → a11y → content rules → `build` into
`web/src/design-system/components/` → gallery → `audit`.

Per surface (a screen or panel): `lock` (variants only where options really differ) →
`behavior-sweep` if interactive → `build` → `polish`.

| Batch | Contents |
|---|---|
| B1 Primitives | Button, icon button, pill and chip, tooltip, popover, tabs, toggle, text input, kbd hint, divider, skeleton |
| B2 Chat and panel | Message bubble (user, AI, streaming, typing), status strip, back-to-latest pill, goal view, direction bar, decision counter, timeline row and drawer, mode indicator |
| B3 Graph | Node, bead, ring, bullseye, tether, label, graph tooltip, scrubber capsule, legend (absorbs the graph view v0 lock) |
| B4 Shells | The workspace (Brain tab, chat tabs, left sidebar, right panel switching Map and Pair), side-panel layout, in-chat widget frame, print sheet, empty, loading and halted states |

**DoD:** every component in the gallery in both themes and densities; every surface
locked with a manifest; B1–B3 keyboard and screen-reader checked; `polish` run per batch.

### D7 — Patterns · 3–4 sessions

Live update choreography (`Interaction Spec.md` §4); LIVE and HISTORY; provisional to
audited; showing confidence; empty, loading and halted states; first-run consent and
privacy (extension); cost display for own-key users; onboarding. Each pattern runs the
loop and is locked where it renders.

**DoD:** each pattern specified and demonstrated in the gallery.

### D8 — Documentation, governance and release · 2 sessions · `document`, `audit`

- `DESIGN.md` regenerated and final; `AGENT_GUIDE.md` (how any AI builds UI with this
  system, the do-nots, adding a component, proposing a token change).
- The gallery as the living reference; contribution and review rules; version 1.0.0;
  release diff; visual regression screenshots.
- Full `audit` on the gallery.

**DoD:** the release test (section 12) passes; tag `ds-1.0`.

---

## 10. The decisions this programme will make

| Phase | Decisions |
|---|---|
| D0 | DDR-000 and the A1–A8 settlements · graph view v0 lock |
| D1 | Personality · principles · personas and ranking |
| D2 | Visual direction · name and mark |
| D3 | Tiers and naming · format · theme and density model · host adaptation · versioning · zoom tiers · spatial tokens |
| D4 | Neutrals · party colours · semantic colours · data scales · faces · type scale · spacing · breakpoints · shape and depth · motion · icons · a11y floor · voice |
| D5 | Channel grammar · size vs thickness · glow (A4) · semantic zoom · change geometry · link evidence · uncertainty · the head |
| D6–D7 | One per component family or pattern where options really differ, plus one lock per surface |

About 30 decisions and 10–15 locks. Each decision takes the owner a few minutes once the
options are on screen.

---

## 11. Surfaces the system must survive

Which zoom levels each surface shows is in `docs/Brain Vision.md` §9.

| Surface | When | What the foundation must already handle |
|---|---|---|
| Web app (chat, panel, graph) | Now, G1 | Light and dark, comfortable density |
| Browser side panel | G3 | 360–420 px, compact density, host-independent party colours |
| In-chat widget (MCP Apps) | Later | Host theme following, sandboxed iframe, no external fonts |
| 3D head | G4 | Numeric tokens for WebGL, lighting, depth |
| Print and design pack (A3) | Now | Print mode, ink-safe colours |
| Obsidian export, slides, marketing site | Later | Same tokens, different density |
| Mobile | Someday | Swift and Kotlin outputs from the same source |

---

## 12. How a new chat continues, and the release test

The repo is the only memory. A new chat needs no history:

1. Paste the kickoff prompt (section 14).
2. The AI reads `STATE.md`, the latest DDRs, `mockups/INDEX.md`, `PRODUCT.md` and
   `DESIGN.md`, says where things stand, and proposes the next step.
3. At the end it updates `STATE.md` and `mockups/INDEX.md`, writes the BUILDLOG entry,
   and commits.

**Delegating a single job.** Any step's mechanical part can go to another agent with a
one-line order, because the skill modes are self-describing. For example: "Run `ui-craft
audit` on `mockups/foundations/color.html` and write the findings under D4.S1 in
`STATE.md`", or "`ui-craft build graph-view` against `mockups/graph-view.lock.md`".

**The release test (D8):** a fresh session given only `docs/DESIGN.md`,
`docs/design-system/AGENT_GUIDE.md` and the skill builds a "copy link" button with the
right tokens, states, focus ring and wording, with no correction. If it fails, the
documentation is what gets fixed.

---

## 13. Role entry (replaces any earlier DESIGN SYSTEM entry)

```yaml
- name: DESIGN SYSTEM
  job: co-create the product's design system with the owner, from principles to components
  owns: docs/design-system/, docs/PRODUCT.md, docs/DESIGN.md, mockups/, .claude/qa/personas/,
        .impeccable/, web/src/design-system/, scripts/design_system/
  reads: everything
  never: engine/, server/, web/src/graph/, data/, the specs (proposes changes, never edits them)
  brief: docs/briefs/D Track Brief.md
  rules:
    - propose options rendered on real data (section 5 protocol); record only what the owner decided
    - no literal values outside tokens.json; every decision a DDR, every surface a lock
    - one decision per step; update STATE.md and mockups/INDEX.md before ending
```

**Relationship to the existing DESIGN role.** The Design Support Charter says that role
prepares data and never proposes representations, because the owner designs by hand.
That role stays as it is. This programme is the owner's deliberate choice to co-create
with an AI (DDR-000). The graph design itself remains the owner's, changed only through
DDRs.

---

## 14. Owner pre-work (before D0)

- **P1** Add the upstream Apache-2.0 licence and NOTICE to `ui-craft/` (A8), then commit
  `ui-craft/` and the `.claude/skills/ui-craft` symlink.
- **P2** Add the real-data protocol (section 5) to `AGENTS.md`.
- **P3** Append the section 13 role to `docs/Roles Documentation.md`.
- **P4** For Codex, install the skill once:
  `ln -s "$PWD/ui-craft" ~/.codex/skills/ui-craft`. Antigravity and other tools are told
  to read `ui-craft/SKILL.md` by the kickoff prompt.

---

## 15. Kickoff prompt

Fresh session, any tool, paste verbatim:

```
Read AGENTS.md fully first. Its workflow gates apply: one step per response, a preamble
before each step, wait for my "start task", "Decide: <option>" and "Finish Step".
Then read docs/Working Rules.md, the DESIGN SYSTEM entry in docs/Roles Documentation.md,
docs/Brain Vision.md in full (the North Star every decision is tested against),
docs/briefs/D Track Brief.md in full, section 6 of docs/briefs/G1 Brief.md, and
ui-craft/SKILL.md plus ui-craft/reference/design-rules.md.
If they exist, read docs/PRODUCT.md, docs/DESIGN.md, docs/design-system/STATE.md,
docs/design-system/decisions/INDEX.md with the three newest DDRs, and mockups/INDEX.md.
Read the last two BUILDLOG entries.

You are the DESIGN SYSTEM role. We co-create the design system with the loop in section
2 of the brief, using the ui-craft mode named for each move (section 3). Read a mode's
reference file before running it. You propose, render options on real project data under
the section 5 protocol, critique honestly (including my favourite), and record only what
I decide. Never describe a visual option without rendering it.

Hard rules: write only inside the paths your role owns. Never edit engine/, server/,
web/src/graph/, data/ or the specs. The laws in section 1 hold until I change them in a
DDR. Third-party screenshots go only in docs/design-system/research/_local/.

Tell me where we stand from STATE.md (or that we are at D0.S1), then give your preamble
for the next step.
```
