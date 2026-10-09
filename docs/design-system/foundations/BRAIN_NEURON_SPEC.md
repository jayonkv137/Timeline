# BRAIN_NEURON_SPEC: every chat is a neuron in one brain

Status: **v0, in design.** Sessions 1 and 2 decided (9 Oct 2026). The neuron template (§7) is in the Brain Lab for review. This is the rulebook we are building rule by rule, the same way `design_pack/GRAPH_SYSTEM_SPEC.md` was built for the 2D graph. If the owner approves the neuron direction, it supersedes the cell territories in [`BRAIN_SYSTEM_SPEC.md`](BRAIN_SYSTEM_SPEC.md) (DDR-008).

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
| 1 | Anatomy dictionary | Which neuron part means what? | see §3 | **decided** (§3.1) |
| AD | **Art direction** (look-dev) | What should it look and feel like, brain and interface together? | — | after 1 |
| 2 | 3D placement | How does a 3D neuron sit on the 3D cortex? | anchor per chat | **decided: B** (§6) · template in review (§7) |
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

### 3.1 Session 1 decisions (owner, 9 Oct 2026)
- **D1-1 Anatomy:** "anatomy good for now". Accepted as the working dictionary.
- **D1-2 Texture:** "yeah let's see what happens". Session 5 tests the continuous "who decides / who does" signals against mode-only.
- **D1-3 Footprint:** the question wasn't clear in words, so it is answered by looking: the Lab's *Surface footprint* switch (off · soft glow · cells). Decided in Session 2.
- **D1-4 Placement:** "let's start". Session 2 starts with B as the lead candidate, with A and C rendered for comparison.
- **D1-5 References:** "I have already given you some reference images … use those always". The owner's references (`owner-ref-4` … `-13`) are the standing moodboard for every session.

The original questions, for the record:
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

## 6. Session 2: 3D placement (variants ready)

**Brain Lab:** `npm run workspace` → `http://localhost:5180/brain-lab.html` (dev only; it doesn't change the workspace Brain). It shows the 10 real chats as neurons, a placement switch, a footprint switch, an axon-stub switch and the evidence inspector (click a neuron or one of its terminal heads).

| Variant | How it is built | Seen on real data | Screenshot |
|---|---|---|---|
| **A** Drawn on the surface | Soma, dendrites and heads are flat shapes pushed through `brainPoint` (no volume) | Reads like white stickers. It sticks to the brain, but loses the "neuron" feeling | `brain-neuron/session-2/a-closeup.jpg` |
| **B** Embedded in the cortex | Soma = a lumpy cell body with hillocks where branches leave, centred 0.35 r above the surface (≈ 2/3 visible, the rest seen faintly through the cortex). Dendrites = tapered tubes lying on the folds. Heads = small bulbs resting on the surface. An axon stub dives inward | Reads as a real object on the brain, at every angle. The title currently sits over the soma (Session 9) | `b-overview.jpg`, `b-closeup.jpg` |
| **C** Inside the glass | The whole neuron sits 0.16 below the surface; the cortex turns more transparent (veil 0.85 → 0.30) | Faint, and the title drifts away from its neuron when orbiting (depth parallax). Neurons on the far side show through and clutter | `c-closeup.jpg` |

**Footprint (D1-3), shown on B:**
- **Off:** neurons only.
- **Soft glow:** a faint patch of light on the surface under each neuron. Amber under the AI-led chats, blue under c10 (the only human-led chat); provisional colour (Session 4). `b-footprint-glow.jpg`
- **Cells:** last round's cell patch under each neuron. `b-footprint-cells.jpg`

**Provisional in this session** (not decided):
- sizes: soma `0.014 + 0.0021·√mass`, head `0.008 + 0.0015·√mass`, dendrite base `0.0045 + 0.0006·√mass` tapering to 35% (Session 3)
- the neutral pearl material (art direction)
- neuron positions, which come from the topic lobes + territory packing (Session 11)

**Claude's recommendation:** **B**, with footprint **soft glow** kept as a candidate for the far-zoom read (Session 13). C is only worth revisiting if the art direction goes "glass brain".

### 6.1 Session 2 decisions (owner, 9 Oct 2026)
- **Placement B.** "b is good".
- **Form:** the first B neuron "looks very distorted". The owner wants one uniform, proper 3D neuron form like `owner-ref-14` (smooth cell body flowing into tapered dendrites, fibrous texture, glowing points). → §7 template.
- **Glow from the neuron itself, not the surface:** "can it come from … the parts of the neurons emitting this glow". The surface soft-glow footprint is dropped; self-emission replaces it (§7.4). The cell footprint stays available for the far-zoom read (Session 13).
- **New references:** `owner-ref-14` (the neuron form and texture), `-15` (blue brain with glowing orange neurons and paths), `-16` (dark teal brain with one bright golden neuron).

## 7. The neuron template (how every neuron is defined)

**Rule:** every chat's neuron is built by the same construction from the same proportions. Data changes parameters only: size, number of branches, branch directions and lengths, glow colours. It never changes the construction. So every neuron looks like the same species, and two neurons differ only where their chats differ.

### 7.1 Construction (in order)
1. **Soma centre:** the chat's seed point on the cortex, raised 0.35 R along the normal (placement B: about two-thirds above the surface).
2. **Dendrite paths:** one per outcome, from its parent (the soma or a parent outcome's end) to the outcome's place in the territory. Each path is a smooth curve through 7 control points that rest on the folds, lifted by the local branch radius. The bow (sideways bend) is ±0.14, with the side taken from a stable hash of the outcome id.
3. **Body:** the soma sphere (radius R) **smoothly united** with a short cone along the first 2.1 R of every root trunk and of the axon (signed-distance union, blend 0.42 R; meshed with surface nets on a 38³ grid, normals from the distance gradient). The cell body therefore flows into its trunks with no seam and no random lumps.
4. **Dendrites:** tapered tubes along the paths. Radius `r(s) = r_tip + (r_base − r_tip)·(1 − s)^1.6`.
5. **Bouton** (the outcome end): a smooth bulb at each path end, stretched 1.3× along the dendrite.
6. **Axon:** one per neuron, leaving the soma and diving into the brain (radius 0.3 R, tapering). Reserved for links to other chats (Session 12).

### 7.2 Proportions (fixed; tokens to be minted when the rules close)

| Part | Size | Data in it |
|---|---|---|
| Soma radius R | `SIZE.soma(chat mass)`, provisional | chat mass (Session 3) |
| Trunk base radius | R × (0.20 + 0.16 × √(outcome mass ÷ largest outcome in the chat)); × 0.7 for nested branches | outcome mass |
| Trunk flare at the soma | 1.7 × trunk base | — |
| Tip radius | 0.55 × bouton radius (min 0.0022) | — |
| Bouton radius | R × (0.10 + 0.12 × √(outcome mass ÷ largest outcome)) | outcome mass |
| Axon | 0.3 R at the soma | — |

### 7.3 Membrane (texture)
- **Body colour:** neutral graphite-pearl (`component.brain.dendrite` × 0.4). It is never blue or amber: in our grammar colour means *who*, so the membrane stays neutral. We take `owner-ref-14`'s form, texture and rim light, not its blue body.
- **Lighting:** key light from upper left plus a soft fill (view-space, so a neuron reads the same from every orbit angle).
- **Texture:**
  - dendrites carry fine fibre striations along their length, as in `owner-ref-14`
  - the body carries fine grain
  - texture contrast is stronger on dendrites, which are thin
- **Rim:** a bright rim at grazing angles (glass-tissue look), lighter on thin dendrites so they don't burn white.

### 7.4 Self-glow (the owner's rule: light comes from the neuron's parts)
- **Soma** emits in the chat's glow colour. **Each dendrite and its bouton** emit in that outcome's glow colour. Where a trunk meets the soma, the colour blends from the soma's to the outcome's. So a neuron's light is the sum of its parts, and one neuron can be part blue and part amber.
- **Emission** sits mostly at the rim (`0.12 + 1.25 × rim`), plus a **halo**: the same geometry pushed outward and lit only where it wraps behind the silhouette, so the light bleeds out of the shape and fades.
- **Glow colour is provisional (Session 4):** white → party colour by how one-sided the share is (lean^0.6). Outcomes with no measured mass glow grey (missing, never 50/50).
- **Sparks (Session 7 preview):** one point of light per requirement or question on that outcome, placed along its dendrite, coloured by who made it (answered = white, open questions dimmer). On the 10 chats that is 120 sparks.
- **Brain surface:** dimmed in the Lab (art-direction preview) so emitted light can be judged, as in `owner-ref-15` and `-16`.

### 7.5 Seen on real data (screenshots in `brain-neuron/session-2b/`)
- `overview-self-glow.jpg`: the whole brain reads like `owner-ref-15`, with glowing neurons on a dark brain. Amber for the AI-led chats, blue for c10.
- `template-c05-closeup.jpg`: star-shaped soma flowing into 5 tapered trunks with boutons.
- `template-c20-nested.jpg`: the one nested outcome branches from a branch end.

### 7.6 Still open
- Real bloom (light bleeding into the dark around bright parts, as in every owner reference) needs a post-processing pass. It is the first art-direction item.
- Small chats are tiny next to c05 (Session 3, size).
- Texture by work mode (Session 5) will modulate §7.3; it never replaces the template.

## 8. Design review 1 (owner screenshot, 9 Oct 2026)

Owner: "why are some fully orange and fully blue … I don't like the texture colour … something is off … think like a world-best designer".

### 8.1 Why some neurons are fully orange or blue (not decided; the provisional §7.4 rule)
The glow colour is `white → party colour` by how one-sided the share is (lean^0.6). On the 10 chats:

| Chats | Real human share | What the rule paints |
|---|---|---|
| c05, c07, c03, c20, c30 | 21–30% | mostly orange |
| c10 | 72% | mostly blue |
| c04, c16, c17, c27 | 46–54% | near white, so **grey on the dark body: looks dead** |

**Verdict: the rule is wrong for this metaphor.**
1. It exaggerates: 25% of c05 is you, yet it reads as two-thirds orange.
2. It erases the minority: you can't see your 25% at all.
3. Co-created chats, the most "symbiotic", look the least alive.
4. Mixing white into amber over a grey body makes the brown and salmon "texture colour" the owner dislikes.

The 2D graph already rejected this kind of colour blend (DDR-006); proportion must be read from length or count, not from a blended hue.

### 8.2 Full scrutiny

| # | Area | What is off | Cause | Direction |
|---|---|---|---|---|
| 1 | Colour meaning | All-or-nothing hues; balanced = grey | §8.1 blend rule | **Never mix party colours.** Pure sky and pure amber light only, proportion shown by length and count (§8.3). Decide in Session 4 |
| 2 | Anatomy | Reads as starfish, octopus or tadpole, not a neuron: big body, short thick arms, bulbs like suckers | Soma too large against branch length; no fine branching | Real neurons are mostly "wire": the branch field is 10–30× the cell body. Smaller soma, longer and thinner dendrites, and fine twigs at the far ends (§8.3) |
| 3 | Material | Matte brown rubber body; candy-cane stripes on branches | Neutral body + blended glow = brown; sparks and fibre stripes alias into bands; no translucency | Translucent cool tissue **lit from within** (a glowing nucleus seen through the membrane, `owner-ref-14` and `-16`); stripes removed |
| 4 | Light | Flat, plastic; nothing actually glows | No bloom; halo too weak; one flat key light | Real bloom pass + tone mapping; emission drives the bloom, so light bleeds into the dark as in every owner reference |
| 5 | Integration | Neurons look stuck on top like toys | No light falls on the cortex; no contact | The neuron's light illuminates the cortex around it (local light in the surface shader). It comes from the neuron, as the owner asked |
| 6 | Brain surface | Grey rubber balloon with white topographic squiggles | The surface "ribbon" noise reads as contour lines, not folds; the dim preview just greys it | Art direction: dark glass, rim-lit fold edges, far quieter noise. Brain tint is an open question (§8.4) |
| 7 | Composition | Figma and Interactive overlap; a sharp V-bend on one branch; big empty areas; no focal point | Lobe placeholder packing; path through two close control points | Wider spacing between neurons; minimum bend radius on paths; one bright focus at a time (Sessions 9–11) |
| 8 | Text | Titles sit on top of somas and branches; no hierarchy | Label anchored at the soma, offset 19 px | Map-label rules: offset outside the dendritic field, size priority, halo (Session 9) |
| 9 | Scale | c05 dominates; small chats are tadpoles | Provisional √ scale | Session 3 (one universal scale + minimum readable size) |

### 8.3 Proposal for the next pass (to be rendered as variants, owner decides)
- **Colour, Session 4 options:**
  - **(a) Share collar:** every nucleus glows white (alive). A thin luminous ring at the soma base is split blue / amber by the exact share, clockwise from 12 o'clock, the same as the 2D share ring.
  - **(b) Counted light:** each requirement or question is one point of pure party light, so the neuron's mix of blue and amber points *is* the proportion (a unit chart).
  - **(a + b)** together.
  - In every option there is no blended colour anywhere.
- **Anatomy (merges Session 7's endings into the form):** requirements become **twigs** branching off the far half of their outcome's dendrite. Human-made twigs are organic (curved, tapering); AI-made twigs are synthetic (straight segments, a small pad at the end), the owner's original "nerves vs logic-gate wires" idea. This gives the fine branching of `owner-ref-14` and stays 100% data: 120 twigs across the 10 chats, 4–24 per neuron.
- **Craft fixes (no meaning change):**
  - bloom
  - translucent membrane with a glowing nucleus
  - cooler neutral body
  - no stripes
  - slimmer, longer proportions
  - light spill on the cortex
  - quieter brain surface

### 8.4 Open question for art direction
`owner-ref-15` and `-16` use blue or teal brains, but blue means "you" in our grammar. Two options:
- a neutral ink-slate brain
- deliberately reading the untouched brain as faintly "human" (it becomes amber "unit by unit"). This would tie back to the symbiotic-brain idea, but it adds a meaning to blue.

The owner decides.

## Sources
- [Obsidian graph view help](https://obsidian.md/help/plugins/graph); [forum: text fade threshold should consider node size](https://forum.obsidian.md/t/graph-text-fade-threshold-consider-node-size/6737)
- [Self Reflected, Greg Dunn and Brian Edwards (Penn)](https://blog.seas.upenn.edu/?p=777); [Scientific American on Self Reflected](https://www.scientificamerican.com/article/watch-the-human-brain-come-to-life-in-this-stunning-piece-of-art)
