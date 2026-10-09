# DDR-007: Chats in the Brain — lights, cortex glow and unfolding maps

- **Status:** Superseded by [DDR-008](DDR-008-symbiotic-cortex.md). The owner rejected the floating lights ("glowing globes … floating outside the brain"); the renderer no longer contains this code.
- **Date:** 2026-10-09
- **Decider:** Owner
- **Affects:** `web/src/workspace/brain-engine.js`, `Brain.tsx`, `brain-frame.html`, `foundations/dataviz.md` §7
- **Compare:** `/workspace.html?brain=legacy` shows the previous photon spheres

## Owner's words

> "if each of the chat … will be fully mapped into the brain how will it look … right now it's only the main node"
> "the color disparity … in the highest view very much visible … each chat point needs to emit a light based on that chat's total share … like CosmoGraph it should emit radiation … to showcase the brain in different parts … AI-dominated part or human-dominated"
> "what to show maybe the major nodes and the text, and if we click on it it is displaying, otherwise without the text … remember the KISS rule"

## What was wrong

Every chat was the same two-light photon sphere (the gradient DDR-006 already found unreadable), so a 21%-human chat and a 72%-human chat looked identical. Nothing showed what a chat contained. Labels competed with each other at the overview.

## Proposal: three zoom states, one grammar

| State | Shows | Hides |
|---|---|---|
| **Overview** (whole brain) | One light per chat. **Colour = who led**: amber AI-led, cyan human-led, white co-created; strength grows with how one-sided it is (lean^0.6). **Size and glow = how much happened** (√ of measured mass). A faint **pool of the same light on the cortex**, so regions read as human- or AI-led. Labels only for the **5 most active** chats; the rest on hover | Outcomes, numbers, all other text |
| **Open a chat** (click a light or list row) | Camera flies in. The chat shrinks into the anchor of its **final-state outcome map**: each outcome is a small light coloured by its own split, tethered to its parent, related outcomes dashed, outcome names shown. Other chats fade to 35% | Other chats' labels |
| **Transcript** | "Open conversation" in the inspector (unchanged) | — |

## Rules

1. **Colour means who, nowhere else.** The light colour is the human/AI split; white means balanced, never "no data". Unmeasured chats are dim.
2. **Light, not paint.** Glow and cortex pools use additive light so regions emerge from the chats inside them; nothing is coloured by hand.
3. **Text on demand.** Overview: at most 5 chat names. Focus: the open chat and its outcomes only (Hick's law, KISS).
4. **Same grammar as the 2D map.** An outcome in the Brain is the same object as a sphere in the graph: size = mass, colour = split, tether = parent, dashed = related.
5. **Closeness = relation.** Until cross-chat evidence exists (roadmap B1), chats gather in **topic lobes** from the corpus task type (Research, Coding, Creative, Writing, Planning, Learning). This is a provisional stand-in and must say so wherever it's explained.
6. **No invented links.** No chat-to-chat lines until the engine can show the evidence (similar < continued < reused). The brain's fibres stay neutral anatomy, never data.

## Measured on the current data

10 chats: 7 AI-led (21–30% human) glow amber, 3 near-even (46–54%) glow white, 1 human-led (72%) glows cyan. The research lobe reads as mostly AI-led at a glance.

## Open questions for the owner

- Keep the cortex pools, or lights only?
- Is 5 the right overview label count?
- Should lobes carry a faint name (Research, Coding…) at the overview?
- When an outcome in the Brain is clicked, should it open the conversation at that outcome's first exchange?
- Should colour show steering (SHAPER) and carrying (EXECUTOR) separately later (Brain Vision §3)?
