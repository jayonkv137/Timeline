# Design System Research: System Teardowns (`TEARDOWNS.md`)

**Phase:** D2 — References and Directions  
**Step:** D2.S2 — System Teardowns  
**Guiding Principle:** **KISS Rule (Keep It Simple, Stupid).** We analyze 7 proven enterprise design systems to extract exact, battle-tested mechanics for tokens, contrast, and data visualization. We borrow only what works mechanically and discard corporate bloat.

---

## 1. IBM Carbon Design System (IBM)

* **Core Strength:** Industry-leading data visualization guidelines, color-blind accessible palettes, and rigorous enterprise token architecture.
* **What to Borrow:**
  - **Data-Viz Color Palette Pairing:** Carbon divides colors into categorical palettes tested explicitly for Color Vision Deficiency (Deuteranopia, Protanopia, Tritanopia). Every adjacent color pair guarantees $\ge 3:1$ graphical contrast.
  - **Color Families by Functional Role:** Separate token spaces for UI chrome vs. data-viz marks, ensuring chrome adjustments never unintentionally shift chart semantics.
* **What to Reject:**
  - Rigid enterprise grid structures and heavy corporate layout padding that waste screen estate.
* **Direct Impact on Our System:** Directly feeds our Phase D4.S1 Party Color resolution and graph tether contrast floors.

---

## 2. Radix Colors (WorkOS)

* **Core Strength:** An intuitive, mathematically consistent 12-step functional color scale designed specifically for accessibility and dark/light symmetry.
* **What to Borrow:**
  - **The 12-Step Functional Scale:**
    - Steps 1–2: App backgrounds & subtle canvas layers.
    - Steps 3–5: Interactive component backgrounds (default, hover, active).
    - Steps 6–8: Borders and subtle dividers.
    - Steps 9–10: High-contrast solid fills (primary buttons, active node cores).
    - Steps 11–12: High-contrast text (secondary and primary labels).
  - **Dark Mode Symmetry:** Steps maintain identical contrast ratios when switching between light and dark modes, eliminating manual color tweaking.
* **What to Reject:**
  - Generic naming that lacks party semantics (e.g., `blue9` instead of `color.party.user.solid`).
* **Direct Impact on Our System:** Adopted as the structural backbone for our semantic token scales in Phase D3 (`tokens.json`).

---

## 3. Apple Human Interface Guidelines (HIG)

* **Core Strength:** Physical spatial depth, fluid camera spring physics, and natural gesture response.
* **What to Borrow:**
  - **Natural Spring & Damping Curves:** Fluid, organic camera orbits and zoom inertia with zero linear robotic easing.
  - **Subtle Layered Translucency:** Frosted specular reflections that provide depth cues without obstructing underlying data points.
* **What to Reject:**
  - Heavy, opaque frosted glass effects (skeuomorphic blur) that hide fine background lines or drop GPU frame rates below 60 FPS.
* **Direct Impact on Our System:** Directly guides the Three.js camera damping, zoom clamping, and tooltip transitions in both the 3D Brain and 2D Chat Graph.

---

## 4. GitHub Primer (GitHub)

* **Core Strength:** High-density, developer-first dark mode tokens and robust semantic token aliasing.
* **What to Borrow:**
  - **Crisp Dark Mode Contrast:** Near-black backgrounds (`#0d1117` / `#161b22`) paired with refined 1px translucent borders (`rgba(255,255,255,0.1)`) that maintain crisp edges without harsh white lines.
  - **Clean Primitive ➔ Semantic Aliasing:** Strict three-tier token separation where components never reference raw primitive hex codes.
* **What to Reject:**
  - Git-specific metaphors (commits, branches, pull request badges) that do not apply to spatial conversation trees.
* **Direct Impact on Our System:** Directly informs our dark stage background tokens (`#080b10` / `#121316`) and 1px border tokens.

---

## 5. Vercel Geist (Vercel)

* **Core Strength:** Minimalist typography, high information density, and razor-sharp monospace tabular alignment.
* **What to Borrow:**
  - **Tabular Numeral & Monospace Discipline:** Strict alignment of numerical metrics, timestamps, and metadata using tabular figures (`font-variant-numeric: tabular-nums`).
  - **Restrained Monochrome Base:** Letting content and real data provide 95% of the visual richness, with zero decorative background illustrations.
* **What to Reject:**
  - Extremely faint sub-3:1 low-contrast gray text on dark backgrounds that fails WCAG accessibility audits.
* **Direct Impact on Our System:** Informs our typography stack (Geist Mono / DM Mono for metrics, Inter / SF Pro for labels) with guaranteed 4.5:1 contrast floors.

---

## 6. Google Material Design 3 (Google)

* **Core Strength:** Systematic elevation surfaces and dynamic tonal palettes.
* **What to Borrow:**
  - **Surface Elevation Through Tonal Tinting:** Higher surfaces (like popups and inspector cards) gain a subtle lighter tint rather than relying entirely on heavy drop shadows.
  - **Touch Target Padding:** Built-in 48px / 44px invisible touch boundaries around small visual targets.
* **What to Reject:**
  - Overly soft pastel color tokens that feel like a consumer mobile app, and algorithmic dynamic theming that produces "muddy" brownish grays.
* **Direct Impact on Our System:** Informs our inspector card elevation tints and the 24px/44px invisible hit-area padding for micro satellite beads.

---

## 7. Atlassian Design System (Atlassian)

* **Core Strength:** Compact, glanceable status indicators, badges, and lozenges.
* **What to Borrow:**
  - **Subtle Pill & Chip Geometry:** Compact, rounded badges with uppercase micro-typography that communicate state (open, resolved, active) in under 16px of vertical height.
* **What to Reject:**
  - Enterprise card clutter, nested accordion panels, and redundant status tags.
* **Direct Impact on Our System:** Informs the compact turn chips and status indicators in the adjacent chat graph drawer.

---

## 8. Master Adoption Blueprint for Phase D3 & D4 (KISS)

| System Mechanic Borrowed | Source System | Applied To in Our System |
|---|---|---|
| **12-Step Functional Scale** | Radix Colors | DTCG Token scale in `tokens.json` (Phase D3) |
| **Data-Viz CVD Contrast Floors** | IBM Carbon | User vs. AI Party Colors (Blue/Orange vs. Cyan/Amber) in Phase D4.S1 |
| **Spring Damping & Zoom Inertia** | Apple HIG | 3D Brain Camera & 2D Graph Pan/Zoom interactions |
| **Dark Matte Stage & 1px Borders** | GitHub Primer | Stage grounds (`#080b10`) and node outlines |
| **Tabular Monospace Metrics** | Vercel Geist | Ledger numbers, pair indices, and turn metadata |
| **Tonal Elevation & Hit Targets** | Material 3 | Frosted inspector cards and 24px invisible bead click areas |
| **Compact Micro-Lozenges** | Atlassian | Requirement state chips (open question, resolved, active) |
