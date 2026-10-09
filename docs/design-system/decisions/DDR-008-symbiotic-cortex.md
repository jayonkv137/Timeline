# DDR-008: The symbiotic cortex: chats as cell territories with surface circuits

- **Status:** Proposed (rendered in the workspace; owner to accept, change or reject)
- **Date:** 2026-10-09
- **Decider:** Owner
- **Supersedes:** DDR-007 (chat lights, cortex glow, unfold). The owner rejected its visual approach.
- **Affects:** `web/src/workspace/brain-engine.js` (cortex module), `Brain.tsx`, `brain-frame.html`, tokens `component.brain.cortex.*` and `component.brain.dendrite`, `foundations/dataviz.md` §7
- **Rulebook:** [`foundations/BRAIN_SYSTEM_SPEC.md`](../foundations/BRAIN_SYSTEM_SPEC.md)
- **Compare:** `/workspace.html?brain=legacy` (the older photon spheres)

## Owner's words

> "the current glowing stuff is not fitting well with the brain, it's floating outside the brain"
> "this sphere right now just glowing globes is not at all a good design choice … something better that would sync well with the brain surface and maps into it like neurons"
> "based on the chat's scale its size will be determined on the brain … human cells and symbiotic cells"
> "how much of this human brain in which all parts it is slowly being integrated into a symbiotic brain … the surface … is being changed unit by unit"
> "I don't need the other text items in the brain view because it is already there in the right panel"

## What was wrong with DDR-007

- Lights floated 0.15 above the cortex and glowed additively, so they read as orbs pinned onto a brain, not part of it.
- Its glow pools blurred together and a 25%-human chat read as "orange", which shows a lean but not a proportion.
- Outcome names cluttered the view, though the right panel already shows them.

## Decision (proposed)

1. **The cortex is a lattice of 2,378 cells** (exact spherical Voronoi on the lateral surface). The cells bend with the folds, and untouched cells show their membranes only.
2. **Every chat claims a territory.** One cell = a fixed unit of measured mass (20, doubling globally when the brain passes 60% full). Size is linear in the chat's mass. Territories never touch, and older ones never move.
3. **Human cells vs symbiotic cells.** The first `round(cells × human share)` cells clockwise from 12 o'clock are sky; the rest are ember. This is the share ring rolled out onto the cortex.
4. **The chat's outcome graph is a circuit drawn flat on its territory.** The root soma sits at the centre, outcomes are neurons on cells (placed from the panel's layout), and parents connect to children by tapered surface dendrites. A signal runs root → tip only in the open territory.
5. **Text = the chat title only.** Up to 8 titles at the overview, only the open chat's title when one is open; outcome names appear on hover only.
6. Topic-lobe placement and "no cross-chat links without evidence" carry over from DDR-007. Cross-chat links are reserved as evidence-weighted **tracts** (spec §9.1).

## Measured on the current data

- 163 of 2,378 cells are claimed (6.9% of the cortex), and **67% of claimed cells are symbiotic**.
- c05 is the largest territory at 57 cells (14 human, 43 symbiotic, 5 neurons).
- c10 is the only human-led chat (4 of 5 cells human).
- The c05 → c17 mass ratio of 45:1 shows as 57 cells vs 2.

## Open questions for the owner

- **Colour of symbiotic cells:** keep ember (AI party colour, consistent with the panel), or give "symbiotic" its own blended tone? A blend would mean a third colour and would break "colour = who".
- **Circuit at the overview:** keep it always visible at 42%, or hide it until a territory is opened?
- **Cell unit:** keep 20 mass per cell (about one-fifth of an exchange), or tie it to exchanges once chats are longer?
- **Clicking a neuron:** should it focus that outcome in the panel graph?
