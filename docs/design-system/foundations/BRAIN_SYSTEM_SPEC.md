# BRAIN_SYSTEM_SPEC: mapping chats onto the cortex

Status: **v0.1, proposed (DDR-008)**. Rendered in `web/src/workspace/brain-engine.js` (cortex module). Numbers live in tokens (`component.brain.cortex.*`, `component.brain.dendrite`), not in the engine.
Companion to [`design_pack/GRAPH_SYSTEM_SPEC.md`](../../../design_pack/GRAPH_SYSTEM_SPEC.md): the graph spec says how one chat becomes a 2D map; this spec says how every chat's final state becomes part of one brain.

## Owner's words

> "something that will stick with brain surface properly … not pointing out … something that is real or matches with the brain"
> "based on the chat's scale its size will be determined on the brain and then based on the final parameter on that chat the share data … human cells and symbiotic cells"
> "see the full overview … how much of this human brain in which all parts it is slowly being integrated into a symbiotic brain … the surface … is being changed unit by unit"
> "I don't need the other text items in the brain view because it is already there in the right panel"

## The idea in one paragraph

The cortex is made of **cells**. Untouched cells are the native brain: faint membranes only. Every chat **claims a territory** of cells, one cell per fixed unit of measured work, so a bigger chat takes more cortex. Inside a territory each cell is either a **human cell** (sky) or a **symbiotic cell** (ember), in exactly the proportion of the chat's final human/AI share. Across the whole brain you can see which parts have become symbiotic, unit by unit. On top of each territory, flat on the folds, the chat's outcome graph is drawn as a **neural circuit**: the goal is the root soma, outcomes are neurons, parent links are dendrites. The only text is the chat's title.

---

## Step 1. The cortex lattice (the units)

### 1.1 Rule
- The surface is a fixed **Fibonacci lattice** of `cortex.lattice` = 2,600 points per hemisphere sphere, each turned into an exact **spherical Voronoi cell**. Bisectors are straight lines in each cell's gnomonic tangent plane, so the cells tile the surface with no overlap.
- Only the **lateral cortex** carries cells. Removed: the medial wall (`dir.z < −0.1`), the base (`dir.y < −0.84`) and the area under the cerebellum (`dir.y < −0.48 && dir.x > 0.12`). Result: **1,189 cells per hemisphere, 2,378 in total.**
- Every cell is built in direction space and pushed through `brainPoint(dir, side, lift)`. It **bends with the folds**, sitting `cortex.lift` = 0.006 above the surface. Each cell is a fan with a middle ring, so it follows a groove instead of bridging it.
- Cells are drawn at `1 − cortex.cell-gap` (84%) of their size. The gap is the **membrane**.
- The lattice never changes. A cell has a stable id, so the same cortex position means the same cell across sessions and devices.

### 1.2 Why
- Real atlases (HCP-MMP1.0, 180 areas per hemisphere) draw parcels on the folded or inflated surface, with dark borders between areas and colour for membership. A territory here is a parcel, and a membrane is its border.
- Discrete units make "how much" countable. This is a **unit visualisation** (Park, Drucker, Fernandez & Elmqvist, *Atom: A Grammar for Unit Visualizations*, TVCG 2018): every mark is one unit of data.

### 1.3 Untouched cortex (substrate)
- Unclaimed cells draw **membrane only**, pearl, at `cortex.substrate-alpha` = 0.10. The whole brain reads as cells waiting to change, without competing with data.

---

## Step 2. Territory size (the chat's scale)

### 2.1 Data source
`mass(chat) = Σ outcomes (human + ai)` from the final snapshot (`chat.snapshots.at(-1).mass`), the same ledger mass the 2D graph uses for sphere size.

### 2.2 Rule
```
unit  = cortex.cell-unit (20), doubled until Σ cells ≤ capacity-fill (0.6) × lattice cells
cells(chat) = max( ceil(mass / unit),  outcomes + 1,  1 )
```
- **Area is linear in mass.** A chat with twice the work covers twice the cortex. Cells are counted, not estimated, so there is no √ compression here (unlike the 2D sphere radius).
- **Floor `outcomes + 1`.** A territory is never smaller than its circuit: each neuron needs its own cell. This is the only distortion. It fires only for chats with many outcomes and little mass, and the rendered cell count can be read back (`getTerritories()`).
- **The unit is global, not per-brain-max.** Adding a chat never shrinks the others. When the brain passes 60% full, the unit doubles for everyone at once (a declared scale step), so the brain never overflows.

### 2.3 Proof from the 10-chat corpus (`data.generated.json`)

| Chat | Category | Exchanges | Mass | Cells | Human share | Human cells | Symbiotic cells | Neurons |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| c05 AI creativity · paper research | Research | 7 | 1,137 | 57 | 25.1% | 14 | 43 | 5 |
| c04 Human–AI interaction design | Writing | 4 | 460 | 23 | 46.1% | 11 | 12 | 4 |
| c20 Figma migration | Coding | 3 | 389 | 20 | 29.6% | 6 | 14 | 3 |
| c07 Co-creation research | Research | 4 | 345 | 18 | 20.9% | 4 | 14 | 3 |
| c03 Interactive portfolio | Coding | 3 | 248 | 13 | 25.8% | 3 | 10 | 3 |
| c30 Language-learning videos | Creative | 2 | 230 | 12 | 24.8% | 3 | 9 | 2 |
| c27 Jellyfish motion study | Creative | 2 | 169 | 9 | 53.8% | 5 | 4 | 3 |
| c10 Project contribution | Research | 1 | 100 | 5 | 72.0% | 4 | 1 | 3 |
| c16 Co-creative panel | Research | 1 | 61 | 4 | 47.5% | 2 | 2 | 3 |
| c17 Datafied Society | Research | 1 | 25 | 2 | 52.0% | 1 | 1 | 1 |
| **Total** | | **28** | **3,164** | **163** | | **53** | **110** | |

- 163 of 2,378 cells claimed (**6.9% of the cortex**) at unit 20. **67% of claimed cells are symbiotic.**
- Median mass per exchange is **93**, so one cell ≈ one-fifth of a typical exchange.
- **Why not one cell per exchange?** The corpus has 1–7 exchanges per chat, 28 in total. At one cell per exchange the whole brain would show 28 cells and c17 would equal c10, though c10 did four times the work. Mass is the engine's measure of how much happened.
- **Archive scale.** 2,759 exchanges × 93 ≈ 257k mass. The unit steps 20 → 40 → 80 → 160 → 320, landing on about 800 cells (34% of the cortex) at 1 cell = 320 mass. The legend must state the current unit.

---

## Step 3. Placement (where the territory grows)

### 3.1 Rule
1. **Anchor.** For now, each chat's anchor is its topic lobe (`Brain.tsx` `LOBES`: Research, Coding, Creative, Writing, Planning, Learning) with a golden-angle offset per chat. This is **provisional** until cross-chat evidence exists (roadmap B1), and it must be labelled as such wherever it is explained.
2. **Claim order = first-seen order** (`since` = first turn timestamp, then id). Older chats claim first, so **a new chat never moves an existing territory**.
3. **Seed.** The nearest unclaimed cell to the anchor on the anchor's hemisphere that is not inside a moat.
4. **Growth.** A frontier expansion from the seed always takes the free frontier cell closest (by angle) to the seed. The result is a compact, disc-like territory that flows around older ones instead of overlapping them.
5. **Moat.** A cell touching another territory (its 6 nearest neighbours) is never claimed. **Territories never touch**: one row of untouched cortex keeps every chat a separate parcel (Gestalt common region).

### 3.2 Edge cases
- **Lobe full.** Growth flows into the nearest free cortex on the same hemisphere, so the territory stretches but stays connected.
- **Hemisphere full.** Not reachable before the unit steps (60% fill trigger).
- **Chat deleted.** Its cells return to the substrate. Other territories do not move (stability beats packing).

---

## Step 4. Share colouring (human cells vs symbiotic cells)

### 4.1 Data source
`share = Σ human / Σ (human + ai)` over the final snapshot: the chat's **final parameter**, the same number the right panel reports.

### 4.2 Rule: the share sector
```
order cells clockwise from 12 o'clock around the seed (ties: nearer the seed first)
first round(cells × share) cells → human cell (sky, party.human)
remaining cells               → symbiotic cell (ember, party.ai)
```
- The rule is the **share ring rolled out onto the cortex** (DDR-006): the human arc starts at 12 o'clock and runs clockwise, then the AI arc. Someone who reads a share ring in the chat panel reads a territory the same way.
- Counts are exact to one cell. The smallest territory (2 cells) can only show 0%, 50% or 100%. That is the resolution limit, and the tooltip gives the exact figure.
- "12 o'clock" is the projection of world up onto the territory's tangent plane, seen from outside the brain. Clockwise is clockwise as the viewer sees it on both hemispheres (the left hemisphere mirrors `w`).

### 4.3 Cell appearance (shader `cellFragment`)

| Part | Value |
|---|---|
| Body | Party colour × light (0.5–1.0, from the cell's real surface normal, so grooves are darker) × per-cell grain (0.78–1.12) |
| Membrane (outer 30% of the cell) | Party colour lifted toward white by 28%, opacity `membrane-alpha` 0.9 |
| Body opacity | `fill-alpha` 0.6 (the cortex shows through, so the cells read as tissue, not stickers) |
| Hover | Membrane +40% toward white, +8% glow |
| Open | +45% of the hover glow |

**Colour means who, and only that.** Sky = human, ember = AI. White and grey are never data at the territory level. Missing data never shows as an even split: a chat with 0 mass has no territory.

---

## Step 5. The circuit (the chat's graph as neurons)

The outcome graph from the right panel, **final state**, drawn flat on the territory.

### 5.1 Root soma (the centre)
- **Where:** on the seed cell, the territory's first cell and its centre of growth.
- **Looks like:** a white core at `0.62 × root-soma` plus two thin rings at 0.8–0.9 and 1.08–1.15. This is the same "white core + two orbits" the 2D root uses (GRAPH_SYSTEM_SPEC Step 1). `root-soma` = 0.6 cell spacings.
- **Means:** the chat's goal. It is the anchor for the camera, the title and the hit target.

### 5.2 Neurons (outcomes)
- **Position.** Take the outcome's 2D layout vector from the root `(x − root.x, −(y − root.y))` and normalise it by the farthest outcome. Then scale it to `layout-reach` (0.78) × the territory radius on the tangent plane. The neuron goes on the **nearest territory cell** to that target that keeps `neuron-spacing` (1.8 cell spacings) from every other neuron, and falls back to the nearest free cell when the territory is too small. Bigger outcomes choose first, so the panel's map and the brain's circuit share their orientation.
- **Soma radius:** `(soma-min 0.18 + soma-range 0.24 × √(mass / chat's largest outcome mass)) × spacing`. This is the √ scaling the 2D sphere uses.
- **Body:** neutral pearl disc (`dendrite` colour, 85%). Identity and size only.
- **Share ring:** an annulus at 1.2–1.48 × radius. The human arc goes from 12 o'clock clockwise, then the AI arc, with a small gap between them (the DDR-006 grammar). An outcome with zero mass gets a **grey ring** (missing, never 50/50).
- Share rings appear **only when the territory is open**. At the overview the cells carry the colour, and rings on top would double-encode it and add noise.

### 5.3 Dendrites (parent links)
- **Path.** It follows the surface, sampled 28 times along the arc between parent and child, with every sample pushed through `brainPoint`. It **never leaves the cortex**.
- **Clipping.** It starts at the parent soma's edge and ends at the child soma's edge (×1.15), following GRAPH_SYSTEM_SPEC's outer-circumference rule.
- **Shape.** A tapered ribbon from `dendrite-base` (0.3 spacing) at the parent to `dendrite-tip` (0.1) at the child. It bows sideways by `dendrite-bend` (16% of its length), with the side taken from a stable hash of the outcome id, so it looks grown, not ruled.
- **Colour:** `component.brain.dendrite`, neutral. Dendrites are structure, not party.
- **Related links** (`outcome.related`, engine data only): a thin dashed ribbon in `link-related`. They are never invented from list order.

### 5.4 Signal (motion)
- In an **open** territory, a soft packet travels root → tip along every dendrite, one per `pulse-period` (2.6 s), delayed 0.18 period per depth level. It says "this circuit is the one you are reading".
- Overview: no signal. Reduced motion or "Pause motion": no signal, and everything static.

### 5.5 Visibility by state

| Element | Overview | Hovered | Open | Others while one is open |
|---|---|---|---|---|
| Cells | 100% | 100% + membrane glow | 100% + light glow | `dim-alpha` 32% |
| Somas + dendrites | `circuit-rest` 42% | 42% | `circuit-open` 100% | `circuit-other` 10% |
| Share rings | hidden | hidden | shown | hidden |
| Signal | off | off | on | off |
| Title | top `label-max` 8 by mass | shown | shown, emphasised | hidden |

---

## Step 6. Text

1. **One text item per chat: its title**, centred under the root soma.
2. **Overview:** at most `label-max` (8), in mass order. A title is dropped if it collides with a higher-ranked one, is behind the brain (ray test against the cortex), or falls outside the safe area (top 128px, bottom 100px).
3. **Open:** only the open chat's title, emphasised. Everything else about the chat (outcomes, numbers, transcript) is in the right panel, which is already open.
4. **No outcome names on the brain.** Hovering a neuron in the open territory shows its name in a small tooltip, on demand only.
5. **No numbers on the brain.** Percentages appear only in tooltips and the panel (honesty rule 2).
6. The legend (standalone view) reads "Human cells · Symbiotic cells · Untouched cortex" and states the cell unit.

---

## Step 7. Interaction

| Input | Overview | Territory open |
|---|---|---|
| Hover a territory (any cell) | Cells glow; title appears even if not top 8 | Same for other territories |
| Click a territory (any cell, its title, or the panel list) | Open it: camera flies to the root (Step 7.1), others dim, right panel shows the chat | Switch to that territory |
| Hover a neuron | — | Tooltip with the outcome name |
| Click a neuron | — | Nothing yet (planned: focus that outcome in the panel graph) |
| Click empty space | — | Close: camera returns to the brain centre, radius ≥ 7.5 |
| Drag / pinch / wheel | Orbit / zoom 5.2–13 | Orbit / zoom 1.4–13 (closer, to read small circuits) |
| "Open conversation" (panel) | — | Opens the chat at its latest pair (unchanged) |

### 7.1 Focus camera
- **Direction:** the smooth cortex normal at the seed, not the local fold normal, which can give grazing views.
- **Target:** the root soma itself.
- **Distance:** `clamp(territory radius × 11, 1.6, 4.2)`, so the territory fills about half the view. Measured: c05 3.3, c20 1.9, c17 1.6.

### 7.2 Hit testing
- The ray is cast against the territory meshes and the cortex together. A cell counts only if no cortex surface lies more than 0.065 in front of it, so you can't click a territory through the brain.
- Territories own every pixel of their cells, so even a single-cell chat (c17) has a target. Its title is a second target at ≥ 24px.

### 7.3 Birth (motion vocabulary)
- When the brain loads, territories grow from their seed outward **cell by cell** over 1.4 s, in claim order. This is the "unit by unit" idea made visible. With reduced motion they appear complete.

---

## Step 8. Field-to-mark mapping matrix

| Engine field | Brain mark | Function |
|---|---|---|
| `snapshots.at(-1).mass[*].human + .ai` | Territory cell count | `max(ceil(m/unit), outcomes+1, 1)` |
| same, human ÷ total | Human vs symbiotic cells | sector, `round(cells × share)` human |
| `dialogue[0].ts` | Claim order (stability) | sort ascending |
| `category` (provisional) | Anchor lobe | `LOBES[category]` + golden angle |
| `nodes[root]` | Root soma on the seed cell | — |
| `nodes[!root].x, .y` | Neuron position | layout vector → nearest free cell |
| `mass[outcome]` | Soma radius | √ of share of largest outcome |
| `mass[outcome].human / total` | Soma share ring (open only) | arc length |
| `nodes[].parent` | Dendrite | surface ribbon, tapered |
| `nodes[].related` | Dashed dendrite | surface ribbon, dashed |
| `title` | The only label | collision-ranked by mass |

Not mapped at brain level (they live in the panel): atoms (requirements, questions, resolutions), per-pair deltas, dormancy, events. Pairs are not scrubbable in the Brain yet (Step 9).

---

## Step 9. Future rules (reserved now, so later work extends this grammar)

### 9.1 Cross-chat links (roadmap B1): "tracts"
- When the engine has **evidence** that two chats are related (similar < continued < reused), connect their **root somas**.
- Same hemisphere: a surface dendrite between the two territories (it crosses the moat).
- Different hemispheres or far apart: a **tract** that dips under the cortex as an arc through the translucent brain, like white-matter tractography in glass-brain renderings.
- Evidence strength maps to width and opacity: similar = thin dashed, continued = thin solid, reused = thick solid with signal. Colour stays neutral, because a link is not a party.
- **Never** draw a tract without an evidence row. No evidence, no line.
- Once tracts exist, **placement switches from topic lobes to evidence**: linked chats claim near each other.

### 9.2 Time (the whole brain over time)
- Each cell can carry the pair (and timestamp) at which its unit of mass arrived. A global time scrubber then replays the brain becoming symbiotic, cell by cell, with the share sector recomputed for the cells present at that moment.

### 9.3 Live chats
- A chat in progress grows its territory by whole cells as mass arrives. Provisional cells (live tier) draw hollow, membrane only, until the pair is settled (honesty rule 3).

### 9.4 Steering vs carrying (Brain Vision §3)
- If SHAPER/EXECUTOR roles are measured separately later, they go into the **cell body vs membrane**: who steered vs who carried. They never become a new hue.

---

## Step 10. Honesty rules (apply to every rule above)
1. Every cell traces to a chat. Every soma and dendrite traces to an outcome and its parent field.
2. Territory size and share come only from ledger mass. Nothing is hand-placed or hand-coloured.
3. The only distortions are the circuit floor (Step 2.2) and lobe placement (Step 3.1), and both are named here.
4. Missing data is grey or absent, never an even split.

## Sources
- Glasser et al. 2016, HCP multi-modal parcellation, shown on inflated and flattened surfaces with area borders: [PMC4990127 fig. 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC4990127/figure/F3); MNE-Python [parcellation plotting](https://mne.tools/1.6/auto_examples/visualization/parcellation.html).
- Park, Drucker, Fernandez, Elmqvist, *Atom: A Grammar for Unit Visualizations*, IEEE TVCG 24(12), 2018: [project page](https://crystal.uta.edu/~park/publication/atom).
- Cosmograph / cosmos: GPU graph rendering with node colour as a data function: [concept docs](https://cosmograph.app/docs-general/concept/). Used here as the reason to keep colour data-driven, not as a visual template.
- Tractography and glass-brain rendering for future tracts: [CIVILITY](https://nitrc.org/projects/civility), [Neuro Bureau brain-art 2018](https://realkm.com/go/the-neuro-bureau-brain-art-competition-2018/).

## Verify
- `cotraceBrain.getTerritories()` (inside the brain frame) returns, for every chat: cells, humanCells, share, mass, neurons, unit and side. The Step 2.3 table is a dump of it.
- `?brain=legacy` shows the old photon spheres for comparison.
