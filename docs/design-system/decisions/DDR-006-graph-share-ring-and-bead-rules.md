# DDR-006: Graph share ring, bead rules and click behaviour

- **Status:** Accepted for the workspace prototype; to be confirmed in D5 (visual grammar)
- **Date:** 2026-10-09
- **Decider:** Owner
- **Affects:** Right-panel graph (`web/src/workspace/LocalGraph.tsx`), `GRAPH_SYSTEM_SPEC.md` Steps 2.3, 4.3, 5.2 and Function 4, DDR-000d

## Owner's words

> "the organeg and blue beds of the rquiemtn are too small cirle and veyr hard"
> "the blue ornage colro mix is not wokring … right now it is nt making any sense at all … make it simple but pracical and like vlauble"
> "all th ebeads so much heavky apcked … what si beys rule to defin her for the bead sin all ssblite so it is wellbehaved"
> On click behaviour: "yeah adapt to plan b"

## What was wrong

1. **The colour mix carried no information.** Every child sphere used the same fixed gradient (light blue → white → light orange). The data only changed glow opacity by up to 25%, which can't be seen. In c05, "Expanded paper bank" is 21% human (66 of 318) and "Initial assignment plan" is 43% human (19 of 44), yet they looked identical. Worse, every sphere suggested a 50/50 split.
2. **Beads were specks.** 3.5 px radius in world space shrank further when zoomed out, well under the 24 px target-size floor (DDR-000e).
3. **Beads were clutter.** Every bead had its own spoke line, the spacing was fixed to one arc whatever the count, and there was no grouping. Busy outcomes became a sunburst.

## Decision

**Share ring.** The sphere becomes a neutral frosted body that shows identity and size (mass) only. A 3 px ring hugs it: blue arc = the human's share of measured influence, orange arc = the AI's share, clockwise from 12 o'clock. Arc length is read far more accurately than glow intensity (Cleveland & McGill). A soft halo leans toward whoever carried more. Outcomes with no measured influence get a dashed grey ring instead of a fake 50/50.

**Focus halo is white.** Focus is not a party, so it no longer borrows the human or AI colour (one colour, one meaning).

**Bead rules**
1. Screen-size marks at every zoom: core 7 px, open-question ring 9 px, answered question 10 px ring with a 5 px core. Hit target at least 24 px.
2. One orbit, no spokes: beads sit on a faint track 7 px outside the sphere.
3. Even spacing: a 5 px gap between beads, centred on 12 o'clock.
4. Grouped by who: the human's beads on the left, the AI's on the right, open questions last, with a wider gap between groups.
5. Bounded: one row up to about 200°, then a second orbit, then a "+N" count. Hover enlarges a bead; dormant outcomes dim theirs. Tethers stop at the outer orbit.

**Click behaviour (plan B).** Clicking a node or bead scrolls the chat to where it first appeared, but the graph stays on the pair being viewed. "Graph follows chat" resumes as soon as the user scrolls the chat themselves.

## Comparing with the original

Add `?mix=legacy` to the workspace URL to see the original dual-light spheres with the new bead layout, for side-by-side review in D5.

## Open for D5

- Whether the ring should show steering (SHAPER) and carrying the work (EXECUTOR) separately, which is Brain Vision's point that influence isn't word count.
- The final party colours (DDR-005). The ring works with any pair that passes the deficiency tests.
- Whether the glow survives at all (DDR-000d).
