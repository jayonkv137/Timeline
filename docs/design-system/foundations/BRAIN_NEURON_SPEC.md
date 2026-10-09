# BRAIN_NEURON_SPEC: every chat is a neuron in one brain

Status: **v0, in design (Session 1 open).** This is the rulebook we are building rule by rule, the same way `design_pack/GRAPH_SYSTEM_SPEC.md` was built for the 2D graph. If the owner approves the neuron direction, it supersedes the cell territories in [`BRAIN_SYSTEM_SPEC.md`](BRAIN_SYSTEM_SPEC.md) (DDR-008).

Lane: design track only. It touches `web/src/workspace/brain-*`, a dev-only Brain Lab page, `docs/design-system/` and tokens, and never `engine/`, `server/` or Track S files. The one shared file, `Brain.tsx`, is coordinated through BUILDLOG.

## Owner's vision (owner's words)

> "each chat would have a point on the brain's surface and the chat heading and then the rest of the networks or the nodes of that full chat will be represented … like a neuron … everything needs to be empirical"
> "the central node … is considered as the neuron centre … based on how much branches it has and also how many connections it has, it will have nerves coming out of it"
> "there are two types of nerve branches coming out from the neuron: one which leads to a sub-node … one which connects another neuron"
> "for the AI neural it should look synthetic, wires like a logic gate … the human like nerves"
> "related topic chats … clustered into close areas … film-making in one area, coding in another … see which areas are AI-dominated or human-dominated … a mapping of a person's entire brain"
> "the visual aesthetic … look and feel is very important … needs to look like it was designed by a proper artist who does this kind of work"

---

## 1. How we design (the process)

Two layers, decided separately so neither spoils the other:

| Layer | Question | Decided by |
|---|---|---|
| **Rules** | What does each part of a neuron *mean*, and which engine number drives it? | Engine data + perception tests + the owner |
| **Art direction** | How does it *look*: materials, light, colour, camera, motion, and the interface around it? | References + rendered look-dev frames + the owner |

### 1.1 Tools
- **Brain Lab** (dev-only page in the prototype). It shows the 10 real chats, plus:
  - a **variant switcher** for the rule under discussion (A, B, C rendered live)
  - an **evidence inspector:** click any part of a neuron to see the engine numbers, the formula and the resulting size or colour (e.g. "soma: mass 1,137 = Σ 157 ledger rows → r = … → 38 px at this zoom"). This proves every mark is empirical.
- **This file:** one section per rule, using the template in §1.3.
- **Screenshots** of every variant tried, in `docs/design-system/brain-neuron/` (committed) and `research/_local/` (third-party references, not committed).

### 1.2 One session = one rule family
1. Claude brings the engine data for that rule, its spread across the chats, and 2–3 variants rendered in the Lab.
2. The owner looks, picks or adjusts, and says what looks wrong.
3. The rule's perception test is run (§1.4).
4. Claude writes the rule (formula, tokens, edge cases) and its test.
5. The owner approves, and the session closes.

Nothing moves to the next session with an open question it depends on.

### 1.3 Rule template
```
### R-<n> <name>
Owner's words · Data source (engine field, file) · Spread on the 10 chats (and archive estimate)
Rule (formula + tokens) · Variants tried (screenshots) · Perception test + result
Decision (owner, date) · Edge cases · Open questions
```

### 1.4 Perception tests (every rule must pass one)
A rule that looks good but can't be read is rejected. Examples:
- 5-second test: "Which chat is the most AI-led?" "Which is the biggest?"
- Can two modes (e.g. Centaur vs Cyborg) be told apart at region zoom?
- Are titles readable at all three zoom levels with no overlaps?
- Colour-blind simulation: is every distinction still visible?
- Frame rate stays at 45 fps or more on the desktop with all chats shown.

---

## 2. Session map

| # | Session | Main question | Engine data (verified 9 Oct 2026) | Status |
|---|---|---|---|---|
| 1 | Anatomy dictionary | Which neuron part means what? | see §3 | **open** |
| AD | **Art direction** (look-dev) | What should it look and feel like, brain and interface together? | — | after 1 |
| 2 | 3D placement | How does a 3D neuron sit on the 3D cortex? | anchor per chat | — |
| 3 | Soma size | One universal scale across all chats | chat mass 25–1,137 (45×) | — |
| 4 | Soma glow | How does a 25 / 75 share actually look? | human share 21–72% | — |
| 5 | Soma texture | Work mode as texture, and is it effective? | mode per exchange; split (see §4 Q3) | — |
| 6 | Dendrites + terminal heads | Branch look, thickness, colour, history | outcomes 1–5 per chat; outcome mass 0–507; per-exchange deltas | — |
| 7 | Spine endings | Every human, AI, question and answered combination | 120 atoms (§3) | — |
| 8 | Signal | What the spiral or pulse means (activity? live?) | per-exchange deltas, live pipeline events | — |
| 9 | Titles | Placement, zoom fading, collisions, size priority | title; mass | — |
| 10 | Zoom levels | What appears at overview, region and neuron zoom | — | — |
| 11 | Clustering into areas | Which chats are related, and where they go | ❌ needs engine work (B1) | research |
| 12 | Axons between chats | Connection types and their look | ❌ needs 11 | — |
| 13 | Whole-brain read | Where you are human-led and where you are symbiotic | all of the above | — |
| AD-final | Polish + critique | Fresh-eye review of the finished brain and interface | — | — |

---

## 3. Session 1: the anatomy dictionary (proposed)

| Neuron part | Means | Engine source | Spread on the 10 chats |
|---|---|---|---|
| **Soma** (cell body) | The chat; its root goal | `state.outcomes[root]` | 10 chats |
| Soma size | How much happened | chat mass = Σ ledger scores | 25 … 1,137 |
| Soma glow | Who made it | human / AI share of mass | 21% … 72% human |
| Soma texture | How you worked together | work mode per exchange (`panel_bundle` HOW: Centaur / Cyborg (`COPILOT`) / Self-Automator (`AUTOPILOT`)) + its two inputs (who created requirements; who added the rest of the mass) | 8 chats 100% Cyborg, c10 Centaur, c27 50/50; Self-Automator never |
| **Dendrite** | One outcome branching from the goal | outcome tree (`parent`) | 1–5 per chat; depth > 1 only in c20 |
| **Terminal head** | The outcome itself | outcome mass and share | mass 0 … 507 |
| **Spines** at a head | Requirements and questions on that outcome | atoms: kind, origin, resolver | 53 your requirements · 36 AI requirements · 6 your open questions · 21 AI open questions · 4 answered |
| **Axon** | A link to another chat | ❌ none yet (B1) | — |
| **Position** | Related chats close together | ❌ only the provisional topic category | — |
| **Title** | The chat's name, the only text on the brain | chat title | — |

**Owner decisions needed:**
- **D1-1:** Is this dictionary right?
- **D1-2:** Should texture use the continuous "who decides / who does" signals behind the mode, or only the mode name? (§4 Q3)
- **D1-3:** Neurons replace the cell territories fully, or keep a soft surface trace under each neuron?
- **D1-4:** Placement option B (embedded in the cortex; axons run through the inside) as the starting point for Session 2?
- **D1-5:** Do art direction (AD) right after Session 1?

---

## 4. Owner questions, logged, with where they get answered

**Q1. Outcome branches: plain lines, or coloured or textured by data?** (Session 6)

Proposal to test:
- Dendrites stay. They are the graph's parent links; without them the neuron is loose dots.
- Each dendrite carries **at most one data channel at a time**:
  - **Overview and region zoom:** neutral tissue whose **thickness = outcome mass**, tapering to the head. Colour lives at the ends: head glow (that outcome's share) and spines (who made each requirement).
  - **Neuron zoom:** the dendrite reveals its **history**, one segment per exchange that grew that outcome. Segment length = how much it grew; segment material = who carried that growth (organic sheath = you, segmented synthetic sheath = AI). The data exists (per-exchange deltas in `snapshots`). Live growth then becomes natural: each new exchange adds a segment.
- Why not colour whole branches blue or amber at the overview: hundreds of coloured lines would drown the soma glow, which is the main read, and would show the same share twice.
- Variants to render: **A** neutral · **B** tinted by share · **C** history segments.

**Q2. Chat titles: always visible, or by size and zoom? Cluster headings?** (Sessions 9–11)

Known so far:
- Obsidian fades labels by zoom level only (its "text fade threshold"). Its users have asked for size-aware fading, "like a map where only large regions get labelled when zoomed out".
- The proposal to test is that map-label hierarchy:
  - **far:** cluster headings (once clusters exist)
  - **approaching:** chat titles appear in size order, with collision priority by mass
  - **near:** everything in view
  - **any zoom:** hover and selection always show the title
- "Every title always visible" works for 10 chats and fails at 300 (overlap), so the rule must scale. The cluster-heading part waits for Session 11.

**Q3. Is texture by mode (Centaur / Cyborg / Self-Automator) effective?** (Session 5)
- On today's data, no: 8 of 10 chats are 100% Cyborg, so texture-by-mode would draw 8 identical neurons. The mode thresholds are also still marked "proposed, until calibration" in the pipeline spec.
- Session 5 tests:
  - **(a)** mode only
  - **(b)** the continuous signals behind it: who created the requirements (c20: AI 11 of 14; c16: you 4 of 4) and who added the rest of the mass
  - **(c)** the per-exchange mode sequence as rings
- The perception test decides. Texture may end up subtle or dropped if it can't be read.

**Q4. Overall aesthetic: designed by a real artist, brain and interface together.** (Art direction track, §5)

---

## 5. Art direction track

Goal: the brain and the whole interface look like one piece, designed by someone who makes scientific-art visuals for a living. This is verified, not assumed.

| Step | What | Output |
|---|---|---|
| AD-1 Moodboard | Owner references (`owner-ref-4` … `-13`, saved in `research/_local/brain-neuron-moodboard/`) + researched references, each tagged with *what* we like (material, light, colour, line, motion, interface) | moodboard page |
| AD-2 Three directions | The same real data rendered in 3 looks (below), in the Lab, with the real interface around them | 3 look-dev frames + short clips |
| AD-3 Lock | The owner picks a direction. Claude writes the **visual bible**: materials, light and emission, palette (party colours from tokens), line quality, camera and lens, motion, post-processing, typography and panel styling | DDR + tokens |
| AD-final | Fresh-eye critique of the finished brain (design-critique / ui-craft critique), side by side with the moodboard; fixes | critique report |

**Candidate directions** (to render, not yet chosen):
1. **Bioluminescent:** dark stage, emissive neurons, soft bloom, glow carries the share (owner refs 5, 6, 8, 9, 10). Risk: neon cliché; glow overpowering the data.
2. **Specimen glass:** clear glass cortex, porcelain neurons, precise studio light, scientific restraint (owner ref 7). Risk: cold.
3. **Etched light:** fine linework neurons on a dark ground, light travelling along the fibres, like Greg Dunn and Brian Edwards' microetched brain *Self Reflected* (owner ref 4, the ink neurons). Risk: busy at the overview.

**Synthetic vs organic** (owner ref 11, the circuit head, against refs 4 and 7, nerve tissue; owner sketches 12–13): AI-made structure reads as circuitry (right angles, pads, segmented sheath); human-made reads as nerve tissue (curves, taper). This holds in every direction.

**Technical feasibility (three.js, same renderer):**
- bloom and tone mapping (post-processing)
- glass (physical material with transmission)
- instanced tubes for dendrites
- depth of field
- custom shaders for tissue and circuit textures

Budget: 45 fps or more on the desktop.

---

## Sources
- [Obsidian graph view help](https://obsidian.md/help/plugins/graph); [forum: text fade threshold should consider node size](https://forum.obsidian.md/t/graph-text-fade-threshold-consider-node-size/6737)
- [Self Reflected, Greg Dunn and Brian Edwards (Penn)](https://blog.seas.upenn.edu/?p=777); [Scientific American on Self Reflected](https://www.scientificamerican.com/article/watch-the-human-brain-come-to-life-in-this-stunning-piece-of-art)
