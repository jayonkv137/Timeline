# ★ LOCKED: graph-view (v0)

- **Surface:** `graph-view`
- **Concept:** `obsidian-v0` (Authentic Obsidian Graph View Port)
- **Status:** `★ LOCKED`
- **Date:** 2026-10-08
- **Author:** DESIGN SYSTEM (Antigravity · Gemini)
- **Target Consumer:** APP role (`web/src/graph/`) for Phase G1.S6
- **Precedence:** This lock governs `web/src/graph/` for Phase G1 on fallback tokens (`tokens.fallback.css`). At D-track milestone M1 (end of D5), real tokens replace the fallback without changing canvas geometry.
- **Fixture Obligations:** Grounded in `mockups/captures/c05.json` (7 pairs, 6 outcomes, real engine data under DDR-000a).

---

## 1. Visual Elements & Geometry (`eye` terms)

- `LOCK:graph-view:1` **Root Goal Singularity Anchor:** The single root node (`parent === null`) sits fixed at origin `(0, 0)`. Renders with a solid white core (`r = 26px`), soft radial glow aura (`r = 2.4 * r_core`), and two concentric origin rings (`r_ring1 = 1.55 * r`, `r_ring2 = 2.1 * r`).
- `LOCK:graph-view:2` **Permanent Root Label Visibility:** The root node label renders wrapped strictly below the concentric rings (`y = y + r * 2.1 + 8px`, `max-width = 180px`, `12.5px font-weight: 600`). The root text is **permanently visible** across all zoom levels and never fades to zero opacity.
- `LOCK:graph-view:3` **Child Deliverable Spheres:** Child nodes render as translucent frosted spheres scaling with accumulated ledger mass ($R_{\text{child}} = R_{\text{base}} + \Delta \cdot \sqrt{\text{Mass}}$). Outer frosted rim has a delicate `1px` stroke.
- `LOCK:graph-view:4` **Dual Internal Photon Radiance:** Child spheres contain two internal light emission sources:
  - Cyan point light source on the left (`#38bdf8`, User mass).
  - Amber point light source on the right (`#fb923c`, AI mass).
  - Photons mix inside the frosted body gradient (`#7dd3fc` $\rightarrow$ `#ffffff` bright core $\rightarrow$ `#fdba74`).
- `LOCK:graph-view:5` **Clipped Connection Tethers (Zero Interior Penetration):**
  - Parent-child links are solid lines (`1.5px`, clipped to outer sphere circumferences). Active tethers render at `0.70` opacity; dormant tethers render at `0.32` neutral gray.
  - Cross-branch `outcome.related[]` links render as dashed lines (`5px dash, 5px gap`, `1.2px` stroke, `0.55` opacity).
- `LOCK:graph-view:6` **Satellite Crown Canopy (Zero Collision Guarantee):**
  - All satellite micro-atoms (requirements and open questions) are placed strictly within the upper crown canopy (angles $-150^\circ$ to $-30^\circ$ above the horizontal equator).
  - Outcome text labels are placed strictly below the lower hemisphere (`y = y + r + 11px`, `max-width = 165px`, `11.5px`).
  - Spatial clearance mathematically guarantees **0% collision** between satellite beads and label text.
- `LOCK:graph-view:7` **Satellite Micro-Atom Types:**
  - **Requirement Bead:** Solid glowing bead (`r = 3.5px`), colored User Cyan or AI Amber based on creator provenance.
  - **Open Question Ring:** Hollow pulsing ring (`r = 4.5px`, stroke `1.6px`), amber color, breathing pulse animation while open.
  - **Resolved Question Bullseye:** Transitioned state when resolved (provenance amber outer ring + solid resolution core).
- `LOCK:graph-view:8` **Terminal Active Focus Beacon:** The terminal deliverable node radiating active work displays a delicate breathing dual-color halo (`r + 4px` to `r + 10px`) pulsing at `2000ms` period.
- `LOCK:graph-view:9` **Obsidian Tooltip:** Black card (`#090a0f`), `1px` translucent border, uppercase tracked category tag (`USER REQUIREMENT` in cyan or `AI OPEN QUESTION` in amber, `9.5px`), with verbatim entity text in `#f1f5f9`.

---

## 2. Technical & Behavioral Gates (`gate` terms)

- `LOCK:graph-view:10` **Zero Data Inventions (G1 D6):** Every node, tether, requirement bead, and open question traces 100% to backend records in `graph_bundle.json`. No invented nodes, no mock fallbacks. Missing data displays as absent.
- `LOCK:graph-view:11` **Deterministic Layout Stability (G1 D5):** Node coordinates are seeded and fixed for the conversation's terminal outcome set. Nodes **never jump or shift positions** when the user scrubs across pairs P1 through P7.
- `LOCK:graph-view:12` **Open Question Persistence (G1 D3):** Open questions appear in the pair they were created and persist across all subsequent pairs until resolved or abandoned.
- `LOCK:graph-view:13` **Fitts's Law Hit Target Floor:** While visual beads are `3.5px` and `4.5px`, interactive hover/click hit areas enforce a minimum of **24 × 24 px** invisible bounding box (`radius + 8px` collision threshold).
- `LOCK:graph-view:14` **Zero Color/Pixel Literals in Graph Code:** All colors, sizes, and opacities must reference the G1 token names defined in `G1 Brief` §6 (`web/src/graph/tokens.fallback.css`). Zero hardcoded hex codes or pixel literals in canvas drawing code.
- `LOCK:graph-view:15` **Composited Performance:** No CSS layout transitions (`transition: width/height`). Canvas render loop idles when stationary (dirty-flagged during pan/zoom/scrub/pulse).
