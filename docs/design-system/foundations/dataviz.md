# Foundation: The visual grammar (data visualisation)

Status: v0.1. The chat-level map is baseline (GRAPH_SYSTEM_SPEC as amended by DDR-006). Brain, project and pair levels are planned and reserved here, so they extend the same grammar instead of inventing a new one. Full reconciliation happens in D5.

## 1. Channel grammar: one channel, one meaning, every level

| Channel | Means | Chat map today | Brain / project (planned) |
|---|---|---|---|
| **Hue** | Who: human sky, AI ember | Share-ring arcs, beads, markers | Human vs symbiotic cells; soma share rings |
| **Arc length** | How much of the measured influence each party holds | Share ring around each sphere | Ring or strand split per region and chat |
| **Size** | Significance: accumulated mass, √-scaled | Sphere radius | Territory **area, linear** in mass (counted cells) |
| **Position** | Structure: hierarchy and relation | Force layout, parent tethers | Clustering by relation; stable anchors |
| **Proximity** | Relationship | Related outcomes drift close | Related chats and projects cluster |
| **Line style** | Kind of link | Solid parent, dashed related | Link evidence strength (planned: similar < continued < reused) |
| **Opacity** | Activity now | Dormant 0.55, active 1 | Dormant regions recede |
| **Shape** | Kind of atom | Dot = decision, ring = open question, ring with core = answered | — |
| **Motion** | Change just happened | Birth, reactivation, focus move | The same vocabulary at every level |

Open in D5: Brain Vision proposes thickness for contribution and size for significance. The chat map currently uses size for mass, which mixes the two. The share ring has already moved "who" off the sphere body (DDR-006), so D5 only has to decide whether mass stays size or becomes thickness.

## 2. The outcome sphere

- **Body:** neutral frosted gradient (white → `#e2e8f0` → slate-400 edge). It shows identity and size only.
- **Radius (world units):** `radius-min + radius-range × √(min(1, mass / mass-norm))` = 12 + 16√(m/500). Root is 17. A 10-mass floor keeps new outcomes visible.
- **Share ring:** 3px at 2.5px from the edge. Human arc from 12 o'clock clockwise, then the AI arc, with a 2.5px gap between them. Arc length is read far better than glow intensity (Cleveland & McGill). An outcome with no measured influence gets a dashed grey ring, never a fake 50/50.
- **Halo:** a soft tint toward whoever carried more, 10–32% alpha. Supportive, not a data channel.
- **Root:** a white core with two orbit rings. The goal anchor, pinned at the origin.
- **Dormant:** whole node at 0.55 opacity.

## 3. Beads: atoms on the orbit (DDR-006 rules)

| Rule | Token |
|---|---|
| Screen-size marks: dot 7px, open-question ring 9px, answered 10px ring with a 5px core | `graph.bead.core` 3.5, `ring` 4.5, `resolved-outer` 5, `resolved-core` 2.5 (radii) |
| Hit target at least 24px | `graph.bead.hit-min` |
| One faint orbit 7px outside the sphere; no spokes | `graph.bead.track`, `track-color` |
| 5px between beads, 9px between groups | `gap`, `group-gap` |
| Order: human group, AI group, open questions; answered after plain decisions; then by time | — |
| Up to 198° per row, a second row 12px out, then "+N" | `max-arc-deg`, `row-gap` |
| Hover enlarges ×1.4 | `hover-scale` |

Kinds: **decision** (filled dot, colour of whoever made it); **open question** (hollow ring in the asker's colour, slow breathe); **answered question** (amber provenance ring plus a core in the colour of whoever answered).

## 4. Links

| Kind | Active | Dormant |
|---|---|---|
| Parent tether (solid) | white 70%, 1.5px | slate 32%, 1px |
| Related (dashed 5/5) | slate-400 55%, 1.2px | slate 25%, 1px |

Lines stop at the outer bead orbit, so they never cross spheres or beads. Related links come only from the engine's `related` data, never from list order.

## 5. Focus and state

- **Focus halo:** white, breathing at the `breathe` tempo, around the outcome holding the newest open question (otherwise the largest delta). Never a party colour.
- **Events** (badge): Genesis, Born, Reactivated, Surge. Derived only, never invented.

## 6. Physics and camera (world units)

`spring 0.005 · repulsion 6500 · damping 0.86 · link 190 · related 200 · boundary 0.02`. Zoom 0.4–3.5. Compact panels use camera scale ≥ 0.72 plus a boundary force, so the graph uses height instead of overflowing width. Positions persist per chat across pairs and tabs. Labels fade in between zoom 0.45 and 0.85.

## 7. Semantic zoom tiers (`semantic.zoom-tier`, planned)

| Tier | Level | Grammar reuse |
|---|---|---|
| 0 brain | All chats | Regions with the party split, size = sustained activity, evidence-weighted links |
| 1 project | One goal or project | Chats as nodes with share rings |
| 2 chat | One conversation | **Today's map** (spheres, rings, beads) and the planned trajectory view |
| 3 pair | One exchange | State before → pair → state after; who steered vs who executed |
| 4 source | Transcript | Verbatim messages; party colours as author markers |

A component states the tiers it renders at. Every mark at every tier keeps a path to tier 4 (principle: every mark traces to its source).

### Brain level (DDR-008, proposed): full rules in [BRAIN_SYSTEM_SPEC](BRAIN_SYSTEM_SPEC.md)

The cortex is a fixed lattice of cells. Each chat claims a territory: cell count is linear in its mass (one cell = `brain.cortex.cell-unit` of mass). Inside it, cells are human (sky) or symbiotic (ember) in the chat's final share, laid out as a sector clockwise from 12 o'clock, like the share ring. The chat's outcome graph is drawn flat on the territory as a circuit: root soma, neurons, tapered surface dendrites. The only text is the chat title. Nothing floats above the surface. DDR-007's lights are superseded.

## 8. Honesty rules

1. No mark without a source pair.
2. No number without a ledger row. Percentages appear only in tooltips, never as big figures.
3. Provisional values (live tier) will look provisional: dashed ring, hollow body (planned token `graph.share-ring.provisional`).
4. Missing data is shown as missing (dashed grey ring), never as an even split.
