# Design System: COTRACE

## 1. Overview

**Creative North Star: "The Observatory of a Shared Mind"**

COTRACE shows how a person and an AI shaped work together: a quiet, dark instrument where conversations become a living map. The interface is a calm reading room around a precise instrument. Chrome is charcoal and recessive so the map and the words carry the colour. Two hues are reserved for the two parties and mean nothing else, anywhere.

It is a product register: one sans family, fixed sizes, dense where the work is dense. Motion appears only when something changed. Every mark on the map traces back to the exact exchange that caused it.

It rejects dashboard furniture (KPI tiles, gauges, red/green scores), decorative glow, ambient motion loops, and colour used for flavour.

**Key Characteristics:**
- Dark charcoal chrome on a 12-step neutral scale; the graph sits on its own deeper stage.
- Two party colours only: human `#38bdf8`, AI `#fb923c` (provisional pair, DDR-005).
- Geometry before typography: size, ring, orbit and line state carry meaning before any label.
- Stillness first: transitions 150–380ms; only the focus halo and open questions breathe.
- Every value comes from `web/src/design-system/tokens/tokens.json`.

The full rules are in `docs/design-system/` (foundations, agent guide, decisions).

## 2. Colors: The Charcoal and Two Lights palette

Neutral charcoal everywhere, with two lights that always mean the same two parties.

### Primary
- **Human Sky** (#38bdf8): the human party. Graph share-ring arcs, human decision beads, author markers, scrubber past notches. Text variant #7dd3fc on dark.
- **AI Ember** (#fb923c): the AI party. AI share-ring arcs, AI decision beads, open-question rings, the current scrubber notch. Text variant #fdba74 on dark.

### Neutral
- **Canvas** (#141619): the reading stage.
- **Graph Stage** (#141417): the map's own ground, always dark (`.theme-dark`).
- **App Chrome** (#1c1e20): activity rail, tab strip, workspace frame.
- **Panel** (#222426): sidebar, inspectors, composer.
- **Raised** (#2b2e30): message bubbles, inputs, cards. Also the subtle line colour.
- **Hover** (#333638): hover fills and default borders.
- **Primary Text** (#dedfdc), **Secondary Text** (#c5c9ca), **Muted Text** (#969c9f, the lowest contrast allowed for readable copy), **Faint** (#7f888d, hints only).

### Named Rules
**The One Voice Rule.** Human Sky and AI Ember are only ever the two parties. Never decoration, focus, selection, status or links.
**The Mirror Rule.** No red or green on anything a person or the AI did. Status colours are for system state only.
**The Stage Rule.** The graph and the brain are stages and stay dark in every theme.

## 3. Typography

**Display Font:** Inter (with -apple-system, Segoe UI, sans-serif)
**Body Font:** Inter
**Label/Mono Font:** JetBrains Mono for metrics (provisional)

**Character:** One quiet, legible sans carries everything. Hierarchy comes from size and weight, never from a second display face.

### Hierarchy
- **Display** (500, 27px, 1.2): rare; empty states and Brain headings.
- **Heading** (600, 20px, 1.2): panel and dialog titles.
- **Title** (450, 15px, 1.38): conversation titles, inspector headings.
- **Body** (400, 13px, 1.65): transcript and prose, 65–75ch.
- **UI** (400, 12px, 1.5): controls and lists.
- **Label** (500, 11px, 1.38): tabs, metadata, graph labels.
- **Caption** (500, 10px, 1.38): status bar and timestamps. 10px is the floor.
- **Overline** (700, 10px, 0.08em tracking, uppercase): sparing section markers only.

### Named Rules
**The 10px Floor.** Nothing renders below 10px.
**The Tabular Rule.** Pair numbers, masses and counts use tabular figures.

## 4. Elevation

Depth comes from tonal steps on the neutral scale, not shadows. Shadows exist only for things that float above content.

### Shadow Vocabulary
- **Elevation 1** (`box-shadow: 0 8px 24px rgba(0,0,0,0.13)`): subtle lift of the composer and hovered cards.
- **Elevation 2** (`box-shadow: 0 4px 12px rgba(0,0,0,0.27)`): menus and small popovers.
- **Elevation 3** (`box-shadow: 0 10px 30px rgba(0,0,0,0.33)`): dialogs and inspectors.
- **Elevation 4** (`box-shadow: 0 14px 38px rgba(0,0,0,0.75)`): controls floating over the graph (scrubber capsule, toast).

### Named Rules
**The Tonal-First Rule.** Before adding a shadow, try the next neutral step.

## 5. Components

### Buttons
- **Shape:** small radius (4px); icon buttons 28–32px square with at least 24px hit area.
- **Icon button:** transparent, muted text; hover fill #333638 with primary text.
- **Focus:** 2px ring in focus ice (#b7cbd7), 3px offset.

### Tabs (workspace)
- 44px strip on the panel tone; the active tab lifts to primary text. A permanent Brain tab sits first.

### Messages
- **User:** raised surface (#2b2e30), 8px radius, primary text. **Assistant:** no bubble; prose on the canvas.
- Author markers use the party colours.

### Conversation map (graph)
- **Sphere:** neutral frosted body; size = measured mass (√-scaled).
- **Share ring:** 3px ring; human arc then AI arc clockwise from 12 o'clock; dashed grey when nothing is measured.
- **Beads:** screen-size marks on one orbit, grouped human | AI | open questions. Dot 7px, open question 9px ring, answered 10px ring with a 5px core; 24px hit target.
- **Links:** parent tethers solid white 70% when active and slate 32% when dormant; related links dashed.
- **Focus halo:** white breathing ring. Never a party colour.

### Scrubber capsule
- Pill on the overlay surface (rgba(9,10,15,0.92)) with elevation 4. Notches: past = human sky, current = AI ember. Fill gradient sky → ember. Prev/next 28px round buttons.

### Tooltips and toasts
- Overlay surface, 8–12px radius, 1px white-16% border. Uppercase overline header in the party colour of the item.

## 6. Do's and Don'ts

**Do:**
- Use semantic CSS variables (`--color-text-muted`, `--color-surface-raised`); read `tokens.ts` in canvas code.
- Wrap any always-dark stage in `.theme-dark`.
- Give every interactive mark a 24px hit target.
- Keep motion to 150–380ms and only for state change; provide the reduced-motion path.
- Trace every visible mark to its source pair.

**Don't:**
- Write a hex, rgba, px font size or duration in component code. Add a token instead.
- Use the party colours for anything but the two parties.
- Use red or green for human or AI data.
- Add looping ambient animation, coloured glows for decoration, side-stripe accent borders or gradient text.
- Render text below 10px or readable copy below muted-text contrast.
