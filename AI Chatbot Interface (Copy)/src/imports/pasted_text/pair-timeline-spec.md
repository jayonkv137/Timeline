Here's the full build-ready spec for the labeled per-pair timeline — the middle section of your right rail. I've written it so you can paste it straight into Figma Make: what it is, every visual rule, the exact Chat 1 data, all interactions, and the edge cases.

# MIDDLE SECTION — "Pair Timeline" (v1 spec)

## What it is

A vertical list in the right rail, **one row per chat pair**, oldest at top → newest at bottom (same direction as the chat). Each row tells you three things at a glance: **how consequential** that exchange was, **who shaped** it, and **what it was about**. Clicking a row jumps the main chat to that pair. It replaces the abstract waveform with labeled, readable rows so it stays informative even on short or uniform chats.

## Row anatomy (left → right)

Each row has four parts on a single ~32px-tall line:

1. **Pair label** — `P1`, `P2`… — tiny muted grey text, ~24px wide column, left-aligned.
2. **Agency bar** — a fixed-width mini-canvas (~40px wide) with a faint vertical **center tick**. A colored bar grows **outward from the tick**:
   - shaped by **you** → grows **left**, blue (#1A8CFF)
   - shaped by **AI** → grows **right**, orange (#F2671D)
   - **both** → a blue piece left **and** an orange piece right, meeting at the tick
   - bar **length** = how consequential: `small` ≈ 8px, `medium` ≈ 16px, `large` ≈ 20px (per side)
   - bar **thickness** constant ~8px
3. **Topic** — 2–4 plain words describing what that pair did (e.g. "fixing the input bug"). ~15px regular text, dark grey, truncates with "…" if long.
4. **Mode dot** — a small 7px filled circle at the far right: blue = you-led, orange = AI-led, half/half = both. (Redundant with the bar on purpose — it's the fast-scan column; the eye can run straight down the dots.)

Row height ~32px, ~2px divider or just whitespace between. Rows flow **directly under the top section** — no floating, no big gaps.

## The exact data for Chat 1 (drop in directly)

```
P1  bar: LEFT/blue medium   topic: "fixing the input bug"           dot: you
P2  bar: LEFT/blue medium   topic: "redirecting the diagnosis"      dot: you
P3  bar: LEFT/blue medium   topic: "rejecting the spread approach"  dot: you
P4  bar: LEFT/blue medium   topic: "choosing the functional update" dot: you
P5  bar: LEFT/blue small    topic: "catching the AI's wrong call"   dot: you
P6  bar: LEFT/blue small    topic: "skipping debounce — my call"    dot: you
```

Result: a calm column of blue bars all on the left, topics varying down the rows, all dots blue. The all-left blue still reads "I drove" at a glance; the topics carry the story the agency bar alone can't.

## Interactions

1. **Hover a row** → the row background lightens (#000 at ~4%), and a small tooltip appears showing the full topic + "Shaped by: You" + the pair's one-line goal. Cursor = pointer.
2. **Click a row** → the main chat scrolls to that pair and briefly highlights those two messages (a ~1s soft flash). This is the core navigation.
3. **Scroll-sync (the "you are here" highlight)** → as the user scrolls the *main chat*, a translucent rounded rectangle (#000 at ~6%, 1px border) sits over the row(s) for the pairs currently visible on screen — exactly like the VS Code minimap slider. It slides as they scroll; the rows themselves don't move or recompute.
4. **Active row** → the pair nearest the center of the viewport gets a subtle left-edge accent (a 2px blue strip on the row's left border) so the current position is clear even at a glance.
5. **Default state on load** → the highlight sits at the **bottom** (newest pair), since that's where the live conversation is.

## Motion / feel

- Highlight slides **smoothly** (ease, ~150ms) as the chat scrolls — not snapping per row.
- Click-to-jump scrolls the chat smoothly, not instantly.
- Keep all motion quiet and minimal — this is a reference panel, not a focal animation. Nothing pulses or auto-animates on its own.

## Layout / sizing (concrete numbers for Figma Make)

- Rail width ~260px; this section uses the full width.
- Row: height 32px, padding 0 12px.
- Columns inside a row: pair-label 24px · agency-canvas 40px · gap 10px · topic flex (fills) · mode-dot 7px at far right.
- Agency canvas: center tick at its mid-x, 1px, grey #111 at 25%. Bars: radius 2px.
- Section sizes to its content — 6 pairs = 6 rows ≈ 200px tall. **Do not pad to fill height**; empty space below a short chat is fine.
- Section header (optional, tiny): "TIMELINE" in muted uppercase, matching your other section headers.

## Edge cases to handle (so it scales past Chat 1)

- **Two-tone pairs** (collaboration): bar shows blue-left AND orange-right in the same row; mode dot is half-blue/half-orange. Make sure a *long* two-tone row doesn't read like a long single-color one — the two colors must be clearly visible.
- **Quiet pairs** ("ok / thanks / next"): give them a **minimum bar length** (~4px) so they don't vanish, a muted/greyed topic like "ok, continue", and a small grey dot. In v1 keep them as individual rows; if a chat has long runs of them, a later version can collapse runs into one "quiet stretch" row — note this as a TODO, don't build it yet.
- **Long chats** (30+ pairs): the section becomes **scrollable** (its own vertical scroll), independent of the main chat. The scroll-sync highlight still maps to chat position. This is where the form earns its keep.
- **Empty/first load** (no pairs yet): show a one-line placeholder, "Your conversation map will build as you chat."

## Division of labor (so the rail doesn't repeat itself)

- **Top section** = who's steering + what we're working on (the DIRECTION bar + goals + the "AI's idea" count).
- **This middle section** = the per-pair *story* and navigation (the labeled rows).
- **Bottom section** = the single HOW analogy ("you're driving — the AI's reading you the map").

Each answers a different question. Because the rows already show the mode mix across the whole chat, **drop any separate "mode split" bar** — it would just restate what the row dots already show.

## The test once it's rendered

Build Chat 1 as above, then build Chat 3 (collaboration) with the same component. Chat 1 should be a **calm blue left-column of distinct topics**; Chat 3 should be a **jagged two-tone column** whose topics show the idea evolving. If the two look obviously different *and* every row teaches you something the top bar didn't, the middle is working. If the rows feel repetitive, the fix is sharper **topics**, not more visual encoding — the words are doing the work here, the bar is just the accent.

One honest note to keep in mind as you prototype: the whole value of this version rests on the **topic labels** being genuinely informative ("rejecting the spread approach," not "discussed code"). In the real tool those come from the analysis step; in your Figma Make mock you're writing them by hand, so write them as sharply as the analysis *should* — because if the labels are vague, this version collapses back into the same blandness as the waveform, just with more words. The topics are the feature.