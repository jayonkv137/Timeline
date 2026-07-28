# BRAIN PAGE — FULL BUILD SPECIFICATION
### Jayon K Vinod Portfolio · Phase 2, Steps 4–6 · The "Lando Norris" chromatic head + hover-reveal

**Document version:** 1.0
**Date:** 2026-05-23
**For:** An AI coding agent (Claude Code Desktop, or AntiGravity) working inside the existing repo.
**Repo root:** `~/Documents/jayon-portfolio/site/`

---

## 0. HOW TO USE THIS DOCUMENT — READ THIS FIRST, AGENT

You are an AI coding agent. This document is a **complete, self-contained specification.** Everything you need to build the brain page is in here, including the full shader code. You do **NOT** need to search the internet for an approach, a tutorial, or a library. The approach is already decided and written below.

**Hard rules for this task:**

1. **Do not improvise the technique.** The technique is specified in §5–§9. If something in the spec seems wrong or impossible, **STOP and ask the user** — do not silently substitute a different approach.
2. **Do not pull in new dependencies.** The repo already has `three`, `@react-three/fiber`, and `@react-three/drei`. Use only those. Do not add `postprocessing`, `gsap`, `leva`, or anything else unless this document explicitly tells you to.
3. **Build in the three sub-steps defined in §10, in order.** Sub-step A must render and be visually verified before you start Sub-step B. Do not build all three at once.
4. **Match the exact numeric constants in §6.** They are deliberate (`0.02` UV cap, `120px` spotlight, `40px` feather). Do not "tune" them to values you think look better — the user will tune them.
5. **Touch only the files listed in §4.** Do not modify `colors_and_type.css`, do not restructure the project, do not touch the box page.
6. After each sub-step, **report what you did and run the verification checklist** at the end of that sub-step.

If you follow this document literally, the result is correct. The risk in this task is an agent "knowing a better way" — there is no better way for V1; there is the way in this document.

---

## 1. PROJECT CONTEXT — WHAT THIS WEBSITE IS

This is a 3D interactive portfolio for **Jayon K Vinod**, a creative technologist based in Bremen, Germany.

The site is built around one metaphor: **the human brain is a black box of infinite potential.** The visitor enters through a literal black box (landing page), passes through a funnel transition, and arrives at the **brain page** — the hero screen you are building.

The brain page centers on a **chromatic metallic head** — a smooth, faceless, iridescent rendering of a human head and shoulders. This head is the centerpiece and the future navigation hub of the whole site.

The single most important interaction on this page is the **hover-reveal**: when the visitor moves their cursor over the head, the chromatic surface "parts" under the cursor and the **real human face of Jayon** shows through underneath. Move the cursor away, the chromatic shell returns.

Conceptually: the chromatic head is the "black box." Hovering it reveals the actual person inside. *Open the head, see who's in there.* That gesture is the entire concept of the site compressed into one micro-interaction. It must feel intentional and refined, not gimmicky.

The visual reference is **landonorris.com** — that site uses the exact same technique (a flat photo + a depth map + a shader that reveals a second image under an organic moving mask). We are adapting it: where Lando's site reveals a *helmet over a face*, ours reveals the *real face under a chromatic shell*.

---

## 2. WHAT ALREADY EXISTS IN THE REPO

The repo is a **Vite + React** project. Already done and working:

- Vite + React project scaffolded at `~/Documents/jayon-portfolio/site/`.
- `three`, `@react-three/fiber`, `@react-three/drei` installed.
- Canonical design tokens at `src/styles/colors_and_type.css` — **read-only, do not edit.** This file defines every color, font, spacing, and motion value via CSS custom properties on `:root`.
- `src/index.css` imports the token file.
- A smoke-test `App.jsx` renders "JAYON K VINOD" on the paper background. This will be replaced by the brain page.
- `public/assets/head/head_diffuse.png` — the chromatic head image (see §3).
- Box page work is **not** in scope for this document. Do not touch it.

The dev server runs with `npm run dev` on port `5173`.

---

## 3. ASSETS — THE FOUR TEXTURES

The brain page hover-reveal needs **four image files**, all describing the *same head at the same position and scale*. They go in `public/assets/head/`.

| File | What it is | Status | Notes |
|---|---|---|---|
| `head_diffuse.png` | The chromatic metallic head — the default visible state. Transparent background. | ✅ In repo | This is the "shell." |
| `head_depth.png` | Grayscale depth map. White = near (nose, brow), black = far. Drives parallax. | ✅ Generated (Depth Anything V2) | If currently `.webp`, that's fine — match the real filename in code. |
| `face_real.jpg` | Jayon's real face photo, posed and cropped to overlay the chromatic head exactly. | ⚠️ Being prepared | The face revealed under the cursor. See §3.1. |
| `head_alpha.png` | Black & white silhouette mask. White = head pixels, black = background. | ❌ NOT YET CREATED | Defines where the hover-reveal is allowed to happen. See §3.2. |

> **AGENT:** Before writing any code, run `ls public/assets/head/` and report exactly which of these four files exist and their exact filenames/extensions. If `face_real.jpg` or `head_alpha.png` are missing, **build the code anyway** but use `head_diffuse.png` as a temporary stand-in for any missing texture so the scene still renders, and clearly tell the user which real assets still need to be dropped in. Do not block on missing assets.

### 3.1 — `face_real.jpg` alignment requirement (context for the agent)

The real face photo MUST be posed, scaled, and cropped so that the eyes, nose, and mouth land on the *same pixels* as the chromatic head's eyes, nose, and mouth. This alignment is done by the user outside of code (photo editing). Your shader just samples both textures at the same UV coordinate and trusts that they line up. If alignment is slightly off, that is a photo-prep problem, not a code problem — do not try to "correct" it in the shader.

### 3.2 — `head_alpha.png` (the silhouette mask)

This is a pure black-and-white image: every pixel that is part of the head/neck/shoulders is **white (1.0)**, every background pixel is **black (0.0)**. It is the same dimensions as `head_diffuse.png`. The shader uses it for two things: (a) to know whether the cursor is "on the head" so the reveal only triggers there, and (b) to cleanly cut the head out from its background. It can be generated from `head_diffuse.png` with a background-removal / threshold tool. If it does not exist yet, the agent uses the alpha channel of `head_diffuse.png` itself as a fallback (since that PNG already has a transparent background).

---

## 4. FILES YOU WILL CREATE OR MODIFY

Create exactly these. Do not create others.

```
src/
  pages/
    BrainPage.jsx          ← NEW — the brain page React component (full-screen)
  three/
    HeadPlane.jsx          ← NEW — the R3F mesh: a plane with the custom shader
    headShader.js          ← NEW — exports the vertex + fragment shader strings + uniforms
  components/
    CornerChrome.jsx       ← NEW — the 4-corner registration text + crosshair ticks
    BottomNav.jsx          ← NEW — ABOUT · CONTACT · SOCIALS
  pages/
    BrainPage.css          ← NEW — layout CSS for the brain page DOM overlay
  App.jsx                  ← MODIFY — render <BrainPage /> instead of the smoke test
```

**Do NOT modify:** `src/styles/colors_and_type.css`, `src/index.css`, `src/main.jsx`, anything related to the box page.

---

## 5. THE TECHNIQUE — HOW THE EFFECT WORKS (PLAIN ENGLISH)

Read this whole section before writing the shader. The shader in §7 will make sense only if you understand the model here.

The chromatic head is **not a 3D model.** It is a single flat rectangle (a `PlaneGeometry`) facing the camera, like a photo on a wall. All the "3D" feeling is faked by a **custom GLSL shader** on that plane.

The shader runs once per pixel, every frame. For each pixel it does five things:

1. **Parallax shift.** It reads the depth map at this pixel. Based on where the cursor is, it shifts the texture sample point by a tiny amount — pixels marked "near" (white in the depth map) shift more, "far" pixels shift less. This differential shift is what the eye reads as 3D volume. The shift is capped at a tiny maximum (`0.02` of the image, i.e. 2%).

2. **Sample the chromatic head.** Using the parallax-shifted coordinate, it samples `head_diffuse` — that's the default chromatic color for this pixel.

3. **Sample the real face.** It also samples `face_real` at the same coordinate — the hidden layer.

4. **Compute the spotlight.** It measures the distance from this pixel to the cursor. It adds a bit of moving **noise** to that distance so the boundary is ragged and organic, not a clean circle. If the pixel is inside the (noisy) spotlight radius, it computes a blend factor between 0 (fully chromatic) and 1 (fully real face).

5. **Mix and mask.** It mixes the chromatic color and the real-face color by that blend factor. Then it multiplies the whole result's opacity by the **alpha mask**, so nothing is ever drawn outside the head silhouette, and the reveal can never bleed onto the background.

The shader receives **uniforms** — live values that JavaScript updates every frame:

- `uMouse` — the cursor position in the plane's UV space (0–1, 0–1).
- `uHover` — a 0→1 value: 0 when the cursor is off the head, 1 when on it. Animated smoothly so the reveal fades in/out instead of snapping.
- `uTime` — seconds since start, used to animate the noise so the edge shimmers slightly even when the cursor holds still.
- The four textures.

That is the entire effect. It is medium difficulty: ~1 day of work. We are deliberately building **Tier 2** (depth parallax + noise-feathered spotlight). We are **NOT** building Tier 3 (a fully fluid, velocity-trailing dispersion shader). If you find yourself writing fluid-simulation code, you have overshot — stop.

---

## 6. EXACT CONSTANTS — DO NOT CHANGE THESE

These values are the locked spec. Put them in the shader / uniforms exactly as written. The user will tune them later via the dev panel (§9); your job is to start from these.

| Constant | Value | Meaning |
|---|---|---|
| Max parallax UV offset | `0.02` | The cap on how far the depth-driven shift can move the texture. 2% of image width. |
| Spotlight radius | `120px` | Radius of the reveal circle, in screen pixels. Convert to UV space in JS (see §7.3). |
| Spotlight feather | `40px` | Width of the soft gradient edge of the spotlight, in screen pixels. |
| Noise amount | `0.06` | How much the noise distorts the spotlight edge. UV-space units. |
| Noise scale | `8.0` | Frequency of the noise pattern. Higher = finer ripples. |
| Noise speed | `0.4` | How fast the noise edge animates over time. |
| Hover fade duration | `0.35s` | Time for `uHover` to ease 0→1 (cursor enters) or 1→0 (cursor leaves). |
| Revealed-face desaturation | `0.15` | Slight desaturation on the revealed real face so it sits in the chromatic universe. |
| Revealed-face chromatic aberration | `1.5px` | Faint RGB-split on the revealed face's edges. |

---

## 7. THE SHADER — FULL CODE

Create `src/three/headShader.js` with **exactly** this content. This is the complete, working shader. Do not rewrite it from scratch; use it as given.

```js
// src/three/headShader.js
// Custom GLSL shader for the chromatic head hover-reveal.
// Tier 2: depth parallax + noise-feathered spotlight mask.

export const vertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const fragmentShader = /* glsl */ `
  precision highp float;

  varying vec2 vUv;

  uniform sampler2D uDiffuse;   // chromatic head
  uniform sampler2D uFace;      // real face
  uniform sampler2D uDepth;     // depth map (grayscale)
  uniform sampler2D uAlpha;     // silhouette mask

  uniform vec2  uMouse;         // cursor in UV space (0..1)
  uniform float uHover;         // 0 = off head, 1 = on head (eased)
  uniform float uTime;          // seconds
  uniform vec2  uResolution;    // plane size in px, for aspect-correct distance
  uniform float uRadius;        // spotlight radius in UV units
  uniform float uFeather;       // spotlight feather in UV units
  uniform float uMaxParallax;   // max UV offset (0.02)
  uniform float uNoiseAmount;   // 0.06
  uniform float uNoiseScale;    // 8.0
  uniform float uNoiseSpeed;    // 0.4
  uniform float uDesat;         // 0.15
  uniform float uAberration;    // chromatic aberration on revealed face (UV units)

  // --- 2D simplex-ish value noise (cheap, good enough for an edge) ---
  vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
  }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(dot(hash2(i + vec2(0.0,0.0)), f - vec2(0.0,0.0)),
          dot(hash2(i + vec2(1.0,0.0)), f - vec2(1.0,0.0)), u.x),
      mix(dot(hash2(i + vec2(0.0,1.0)), f - vec2(0.0,1.0)),
          dot(hash2(i + vec2(1.0,1.0)), f - vec2(1.0,1.0)), u.x),
      u.y);
  }

  void main() {
    // 1. ----- DEPTH PARALLAX -----
    // Read depth, remap to -0.5..0.5 so near pushes one way, far the other.
    float depth = texture2D(uDepth, vUv).r - 0.5;
    // Cursor offset from screen center, scaled by depth and the cap.
    vec2 parallax = (uMouse - 0.5) * depth * uMaxParallax * 2.0;
    vec2 uv = vUv + parallax;

    // 2. ----- SAMPLE THE CHROMATIC HEAD -----
    vec4 chroma = texture2D(uDiffuse, uv);

    // 3. ----- SAMPLE THE REAL FACE (with faint chromatic aberration) -----
    float ab = uAberration;
    vec4 faceR = texture2D(uFace, uv + vec2( ab, 0.0));
    vec4 faceG = texture2D(uFace, uv);
    vec4 faceB = texture2D(uFace, uv + vec2(-ab, 0.0));
    vec3 face  = vec3(faceR.r, faceG.g, faceB.b);
    // Slight desaturation so the real face stays in the chromatic universe.
    float gray = dot(face, vec3(0.299, 0.587, 0.114));
    face = mix(face, vec3(gray), uDesat);

    // 4. ----- SPOTLIGHT MASK (noise-feathered) -----
    // Aspect-correct distance from this pixel to the cursor.
    vec2 aspect = vec2(uResolution.x / uResolution.y, 1.0);
    float dist = length((vUv - uMouse) * aspect);
    // Animated noise warps the edge so it parts organically, not as a circle.
    float n = noise(vUv * uNoiseScale + uTime * uNoiseSpeed) * uNoiseAmount;
    float edge = dist + n;
    // 1.0 inside the spotlight core, 0.0 outside, soft gradient across the feather.
    float spot = 1.0 - smoothstep(uRadius, uRadius + uFeather, edge);
    // Reveal only when the cursor is actually on the head.
    float reveal = spot * uHover;

    // 5. ----- MIX + MASK -----
    vec3 color = mix(chroma.rgb, face, reveal);
    float silhouette = texture2D(uAlpha, vUv).r;
    // Respect both the alpha mask AND the diffuse PNG's own alpha.
    float alpha = silhouette * chroma.a;

    gl_FragColor = vec4(color, alpha);
    #include <colorspace_fragment>
  }
`;

// Default uniform values. The numbers here are the locked spec from §6.
// uRadius / uFeather are placeholders here — JS recomputes them from px in §7.3.
export function makeUniforms() {
  return {
    uDiffuse:     { value: null },
    uFace:        { value: null },
    uDepth:       { value: null },
    uAlpha:       { value: null },
    uMouse:       { value: [0.5, 0.5] },
    uHover:       { value: 0.0 },
    uTime:        { value: 0.0 },
    uResolution:  { value: [1, 1] },
    uRadius:      { value: 0.12 },
    uFeather:     { value: 0.04 },
    uMaxParallax: { value: 0.02 },
    uNoiseAmount: { value: 0.06 },
    uNoiseScale:  { value: 8.0 },
    uNoiseSpeed:  { value: 0.4 },
    uDesat:       { value: 0.15 },
    uAberration:  { value: 0.0015 },
  };
}
```

### 7.1 Notes on the shader for the agent
- The `#include <colorspace_fragment>` line lets three.js apply correct sRGB output. Keep it.
- The noise function is intentionally cheap. Do not replace it with a heavier 3D noise.
- If `head_alpha.png` is missing and you fall back to the diffuse PNG's alpha, set `uAlpha` to the diffuse texture — `texture2D(uAlpha, vUv).r` will then read the red channel, which is wrong; in the fallback case, instead just use `chroma.a` alone for `alpha` and set `silhouette = 1.0`. Leave a clear `// FALLBACK:` comment when you do this.

### 7.2 Converting pixel constants to UV space
The spec gives radius/feather in **pixels** but the shader needs **UV units**. Compute in JS:
```
uRadius  = 120 / planeHeightInPixels   // ~0.12 if the head plane is ~1000px tall
uFeather =  40 / planeHeightInPixels
```
Recompute these on window resize. Use the *rendered* height of the head plane on screen.

### 7.3 Materials
On the `ShaderMaterial`: set `transparent: true`, `depthWrite: false`. Use `THREE.SRGBColorSpace` on the `uDiffuse` and `uFace` textures; leave `uDepth` and `uAlpha` as linear (`THREE.NoColorSpace` / default) since they are data, not color.

---

## 8. THE HEAD PLANE COMPONENT — `HeadPlane.jsx`

`src/three/HeadPlane.jsx` is a React Three Fiber component. Requirements:

- Use `useTexture` from `@react-three/drei` to load the four textures. Handle missing files per §3 (fallback to diffuse).
- Build a `<mesh>` with a `<planeGeometry>` and a `<shaderMaterial>` using `vertexShader`, `fragmentShader`, and `makeUniforms()` from `headShader.js`.
- Size the plane to the head image's aspect ratio. The head image is wide (it includes background). The plane should be sized so the head sits centered and occupies roughly 55–65% of the viewport height. Scale to viewport; recompute on resize.
- In `useFrame`, every frame: update `uTime` with the clock's elapsed time.
- Track the mouse: on `pointermove` over the canvas, convert the event to UV coordinates of the plane and write into `uMouse`. Use R3F's raycaster / the mesh's `onPointerMove` so you get UVs directly (`e.uv`).
- Track hover: `onPointerOver` / `onPointerOut` on the mesh set a target for `uHover` (1 or 0). Each frame, **ease** `uHover.value` toward the target with a 0.35s time constant (e.g. `uHover.value += (target - uHover.value) * (1 - exp(-delta / 0.35))`). Do not snap.
- Because the alpha-masked plane has transparent regions, R3F's pointer events fire on the *whole rectangle*, including transparent corners. That's acceptable for V1: the `uAlpha` mask in the shader still prevents any visual reveal off the silhouette. (A pixel-perfect hit test is a future polish item — do NOT build it now.)
- Update `uResolution` and the px→UV radius/feather on resize.

---

## 9. THE BRAIN PAGE COMPONENT — `BrainPage.jsx`

`src/pages/BrainPage.jsx` composes the whole screen. Layers, back to front:

1. **Background.** Full-viewport, `background: var(--bg-page)` (the paper neutral-50). Split visually into a LEFT half with a **dot grid** and a RIGHT half with a **graph grid**. The CSS classes `.dot-grid` and `.graph-grid` already exist in `colors_and_type.css` — use them. Two absolutely-positioned divs, each 50% width. **Cursor reactivity of these grids is Step 7, NOT in this document — build them static for now.**
2. **The R3F canvas** with `<HeadPlane />`, centered, transparent background (`gl={{ alpha: true }}`, and `<color>` not set / canvas `style background: transparent`). The canvas sits above the grids.
3. **DOM overlay** (plain HTML/CSS on top of the canvas, `pointer-events: none` on the wrapper so it doesn't steal hover from the head; re-enable `pointer-events: auto` only on the actual links):
   - `<CornerChrome />` — four corners. Top-left: `JAYON.PORTFOLIO / V0.1 / 2026`. Top-right: `BREMEN / 53.07°N`. Bottom-left: `[ CREATIVE ]` over `+ CREATIVE TECHNOLOGIST`. Bottom-right: `[ TECHNOLOGY ]` over `2026.05.18`. Each corner has a crosshair `.tick`. Use the `.label`, `.bracket-label`, `.tick` classes from the canonical CSS.
   - The display name **`JAYON K VINOD`** — `.h-display` class — but on the brain page it sits as a quiet element; per the design reference it can be centered behind/over the head. For this build: place it centered, behind the canvas (lower z-index than the canvas), so the head overlaps it. Color `var(--fg-primary)`.
   - `<BottomNav />` — centered at the bottom: `ABOUT · CONTACT · SOCIALS`, mid-dot separators, using the bottom-nav pattern from the canonical spec (`.label` styling, `--fg-muted` rest, `--fg-primary` hover).

All colors, fonts, spacing, motion: **only** from `colors_and_type.css` custom properties. Never hardcode a hex value.

### 9.1 Dev tuning panel (REQUIRED)
Add a small dev-only panel, toggled by pressing the `` ` `` (backtick) key, that exposes sliders for: `uRadius`, `uFeather`, `uMaxParallax`, `uNoiseAmount`, `uNoiseScale`, `uNoiseSpeed`, `uDesat`, `uAberration`. This lets the user tune the locked constants visually. Build it as a plain absolutely-positioned `<div>` with `<input type="range">` elements — **do NOT add the `leva` library.** The panel is hidden by default and must never show in a production build.

---

## 10. BUILD ORDER — THREE SUB-STEPS, IN SEQUENCE

Do these in order. Verify each before starting the next.

### SUB-STEP A — Static head on the page (no shader interactivity yet)
Build `BrainPage.jsx`, the R3F canvas, and `HeadPlane.jsx`, but with a **plain `MeshBasicMaterial`** showing only `head_diffuse.png` — no custom shader yet. Add the background grids, corner chrome, name, and bottom nav. Wire `App.jsx` to render `<BrainPage />`.
**Verify A:**
- [ ] `npm run dev` runs with no console errors.
- [ ] The chromatic head renders, centered, ~55–65% of viewport height, correct aspect ratio (not stretched).
- [ ] Paper background; dot grid visible left, graph grid visible right.
- [ ] All four corner-chrome blocks present with crosshair ticks.
- [ ] `JAYON K VINOD` visible; bottom nav visible and links change color on hover.
- [ ] Resizing the window keeps the head centered and correctly scaled.

### SUB-STEP B — Swap in the shader; depth parallax only
Replace `MeshBasicMaterial` with the `ShaderMaterial` from §7. Wire `uDiffuse`, `uDepth`, `uAlpha`, `uResolution`, `uTime`, `uMouse`. Leave `uHover` forced at `0.0` for now (so no face reveal yet). Implement the mouse→UV tracking and the per-frame `uTime` update.
**Verify B:**
- [ ] Head still renders correctly through the shader (looks the same as A when the mouse is still).
- [ ] Moving the cursor produces a *subtle* parallax shift of the head — visible but gentle, never "swimming." Near features (nose/brow) shift slightly more than the edges.
- [ ] The alpha mask cleanly cuts the head from the background — no rectangular edge, no halo.
- [ ] No console errors; framerate stays smooth (use the browser FPS meter).

### SUB-STEP C — The hover-reveal
Add `face_real.jpg` as `uFace`. Implement `onPointerOver`/`onPointerOut` setting the hover target, and the eased `uHover` per frame (0.35s). The spotlight + noise edge + real-face mix is already in the fragment shader — now it activates.
**Verify C:**
- [ ] Cursor off the head → fully chromatic, no reveal.
- [ ] Cursor on the head → a soft spotlight follows the cursor; inside it the real face shows through; the edge is ragged/organic and shimmers slightly (noise), NOT a clean circle.
- [ ] Moving the cursor off the head → the reveal fades out smoothly over ~0.35s, not instantly.
- [ ] The reveal never appears outside the head silhouette.
- [ ] The revealed face looks slightly desaturated with a faint edge color-split — it sits in the same world as the chromatic head, not pasted on.
- [ ] Pressing `` ` `` opens the dev panel; sliders visibly change the effect.
- [ ] Smooth framerate throughout.

When all three checklists pass, this document's scope is complete. Steps 7 (cursor-reactive grids) and 8 (funnel transition) are separate, later work.

---

## 11. WHAT NOT TO DO (GUARDRAILS)

- ❌ Do not build Tier 3 (fluid, velocity-trailing dispersion). Tier 2 only.
- ❌ Do not add libraries beyond `three` / `@react-three/fiber` / `@react-three/drei`.
- ❌ Do not modify `colors_and_type.css` or hardcode any color/font/spacing value.
- ❌ Do not build the cursor-reactive grid animations — grids are static here.
- ❌ Do not build a pixel-perfect alpha hit-test — the shader mask is sufficient for V1.
- ❌ Do not "improve" the locked constants in §6 — expose them in the dev panel and let the user tune.
- ❌ Do not touch the box page or the funnel transition.
- ❌ Do not build all three sub-steps in one pass — verify A, then B, then C.
- ❌ If anything in this spec seems wrong or blocked, STOP and ask the user. Do not substitute your own approach.

---

## 12. GLOSSARY (for quick reference)

- **Diffuse** — the plain color image of a surface (here: the chromatic head as you see it).
- **Depth map** — grayscale image encoding distance; white = close, black = far.
- **Alpha mask** — black/white image marking which pixels belong to the subject.
- **UV space** — a 0–1 × 0–1 coordinate system mapped across a texture/plane. `(0,0)` one corner, `(1,1)` the opposite.
- **Uniform** — a value passed from JavaScript into a shader, the same for every pixel that frame (e.g. cursor position).
- **Fragment shader** — code that runs once per pixel to decide its final color.
- **Parallax** — apparent shift of near vs. far things as the viewpoint moves; the cue that sells fake depth.
- **Feather** — the soft gradient width at the edge of a mask, so it fades instead of having a hard line.
- **R3F** — React Three Fiber, the React wrapper around Three.js.

---

*End of specification. Build Sub-step A first. Report back before B.*
