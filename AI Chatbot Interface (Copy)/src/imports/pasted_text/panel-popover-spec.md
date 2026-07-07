# Panel Section Headers + Info Popups — Content Spec (v4)
### For Figma Make: add a heading + info (i) button to each of the panel's 5 sections

**v3 changes:** all popups cut down to plain, short, non-preachy text. Goal popup uses
the owner's own wording. Direction simplified — no explanation of "steering," just what
the bar shows. Timeline popup now matches the design goal defined in PANEL_SPEC.md §4
("what actually happened, and who made it happen"). HOW popup stripped of research-term
parentheticals and the "none of these is good or bad" line — the section stays neutral
by simply stating the facts, not by saying it's being neutral.
**v4 changes:** added a researched design-rationale section — correct pattern name
(popover, not tooltip), why on-demand disclosure is the right call here (progressive
disclosure principle), the consistency rule, content-length guidance, required
accessibility behavior, and a research-backed refinement to the optional first-time
walkthrough (kept as a separate one-time mechanism from the popovers).

---


---

## Design rationale & strategy (researched — the reasoning behind the pattern below)

**The pattern we're using is technically a POPOVER, not a tooltip — naming this
correctly matters.** Standard UX distinction (Red Hat / NN/g design systems): a
*tooltip* is hover-triggered, plain text only, and has no close button — it vanishes
when focus moves away. A *popover* is click/tap-triggered, can hold richer content, and
needs its own explicit dismissal (an X, or tapping outside). What we're building — click
the (i), a small panel opens, dismiss by tapping outside or an X — is a popover. Say
"popover" to whoever builds this, not "tooltip," so they reach for the right component
and the right accessibility behavior.

**Why an on-demand info button is the right call here (not permanent on-screen text):**
this is progressive disclosure, the foundational UX principle (Jakob Nielsen, 1995):
show only what's essential by default, let people reveal explanation on demand. Nielsen
Norman Group's own test for when this is the right pattern: *"is the information
necessary to complete a task? If no, a tooltip/popover is well suited — otherwise it
belongs on the screen permanently."* Our popups pass this test — the panel is fully
usable without ever opening one; they exist purely for orientation. That's exactly the
right use of the pattern, not an overuse of it.

**Why every section gets one, with no exceptions:** NN/g flags inconsistency as a
real failure mode — if only some icons get explanations, people stop trusting that the
absence of an (i) means "self-explanatory," and start second-guessing everything. Since
all 5 sections use custom visual language (colors, glyphs, bars) that isn't
self-evident, the "same pattern, 5 times, no exceptions" rule stands.

**Content length:** UX guidance converges around keeping this kind of text under ~150
characters — short enough to read in the time it takes to notice you opened it. The v3
copy below was already cut to this standard independently; the research confirms it was
the right instinct, not just a stylistic preference.

**Accessibility — non-negotiable, add to the brief for whoever builds this:**
- Must open on click/tap **and** on keyboard focus (Tab + Enter) — a mouse-only
  interaction excludes keyboard users entirely.
- Must close on Escape, on tapping outside, or via the X — never trap the user in it.
- Text contrast ≥ 4.5:1 against the popover's background (WCAG).
- Use `aria-expanded` on the (i) button and `aria-describedby` linking it to the
  popover content, so screen readers announce it correctly.

**On the optional first-time walkthrough (from v1's footnote) — now backed by
research, with a refinement:** a 2026 study (Anik & Bunt) found that revealing
explanations progressively — rather than all at once — measurably improved how much
people *felt* they understood the system, even when total information shown was the
same. That supports adding the sequence. The refinement: keep it as a **separate,
one-time mechanism** from the popovers themselves — a short "coach mark" style tour
(lightweight highlights, one section at a time, always skippable) that fires once, versus
the 5 popovers which stay available forever as the "look this up again" mechanism. Don't
merge the two into one system — a permanent tour that fires on every visit becomes
exactly the "feature firehose" onboarding research warns against.

---
## What to build (same pattern, 5 times)

For each of the 5 sections in the right rail:
1. Add a small section heading at the top of the section (label only — see exact text
   below for each).
2. Add a small circular **(i)** info button next to the heading, right-aligned.
3. Tapping/clicking the (i) — or focusing it with keyboard + Enter — opens a small
   **popover** near the button (not a full modal — should feel light). Dismiss by
   tapping/clicking outside, an X, or pressing Escape.
4. The popover contains ONLY the "Popup text" given below for that section — no extra
   commentary, no restating the heading.

Keep the heading style consistent across all 5: small, uppercase or label-style, quiet
(secondary text color, not competing with the section's own content). The (i) icon should
be small, subtle, same secondary color as the heading — it should not look like a
warning or an error indicator, just a neutral "learn more." Text inside the popover
should meet 4.5:1 contrast against its background.

---

## Section 1 — Goal (top section)

**Heading:** `GOAL`

**Popup text:**
> Gives you an idea what you are currently working on, and a bit of context on the goal
> you are working towards. You can expand to see the full structure of your goals.

---

## Section 2 — Direction

**Heading:** `DIRECTION`

**Popup text:**
> Shows how much of this chat's direction has come from you versus the AI, added up so
> far. Updates as you keep talking.

---

## Section 3 — Decisions

**Heading:** `DECISIONS`

**Popup text:**
> A count of who introduced what. Each time a new requirement or idea gets set for this
> chat, it's counted here under whoever introduced it first.

---

## Section 4 — Timeline

**Heading:** `TIMELINE`

**Popup text:**
> The record of what actually happened — one row per exchange. Tap a row to see what
> was decided and why.

---

## Section 5 — How (bottom section)

**Heading:** `HOW YOU'RE WORKING`

**Popup text:**
> Shows how you and the AI worked together this exchange.
>
> **You're driving** — you're setting the direction, AI helps when asked.
> **Copiloting** — you and the AI are shaping the work together.
> **Autopilot** — the AI is mostly deciding and doing.

---

## One extra thing worth adding while you're in there (optional, flag to Figma Make separately)

A first-time visit could show a brief one-time coach-mark sequence highlighting all 5
sections in order (not the popovers themselves — a lighter, separate highlight-and-caption
pattern), always skippable, "seen it" flag so it never fires again. See the research note
above for why this should stay a distinct mechanism from the popovers rather than reusing
them. Only build this if it's easy; the 5 individual info buttons are the must-have, this
is a nice-to-have.

---

## Copy rules followed (so future edits stay consistent)
- Plain words only — no backend/research terms anywhere in this copy. No parentheticals
  explaining "what researchers call this." Just state what the section shows.
- Not preachy. No lines telling the user how to feel about what they see (e.g. no "none
  of these is good or bad" framing) — showing the fact plainly IS the neutrality; it
  doesn't need to be said out loud.
- Every popup stays short and scannable — a few seconds to read, not a paragraph.