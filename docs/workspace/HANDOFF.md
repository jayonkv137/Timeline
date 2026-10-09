# COTRACE — workspace prototype, graph refinement v2

Updated 9 October 2026 after graph readability and motion review, against jayonkv137/Timeline. This is a working frontend prototype and integration starting point, not a connected chat service. The original app entry, engine, frozen fixtures and canonical specifications remain unchanged.

## Open it

Open `cotrace-workspace.html` in a desktop browser. Everything required for the preview is embedded, including the brain renderer and ten example conversations. There are no runtime CDN dependencies. WebGL is required for the interactive brain; the conversation list remains an alternative way to select chats.

Try this sequence:

1. Scroll the open conversation. The right map follows the visible exchange. The rail contains the graph and compact timeline only; redundant headings, legends, follow switch, outcome dropdown and duplicate navigation were removed.
2. Drag the notched timeline, use Previous/Next or arrow keys, press Play/Pause to replay evolution, or select an outcome. The transcript moves to the corresponding exchange; selecting an outcome goes to its first recorded appearance.
3. Expand the graph, then press Escape. It remains the same conversation and restores the normal layout.
4. Choose **Locate in Brain**. Orbit or zoom the brain, select a conversation, then use **Open conversation**. Previously opened chats preserve reading position, graph state and draft.
5. Create a conversation and send a draft. The preview records the user message and waits for a backend; it does not invent an assistant response or analysis.

## Product architecture

| Surface | Responsibility | Navigation rule |
| --- | --- | --- |
| Left history | Search, create and reopen conversations | One tab per conversation; no folders or tags in this first version |
| Central chat | Read and compose; keep multiple conversations open | Closing a tab does not delete its conversation or in-session state |
| Permanent Brain tab | Overview of all analyzed conversations | A brain point represents a conversation, not an individual requirement |
| Right conversation map | Inspect outcomes, requirements and questions for one chat | Expanding or zooming never silently changes the graph scope |
| Right Brain inspector | Preview a selected chat and its outcomes | Explicit Open conversation returns to its saved reading position |

The key decision is to keep local and global navigation distinct. A larger local graph remains local. Cross-chat exploration belongs in Brain, where there is enough space to communicate scope and evidence. This avoids accidentally turning a small context rail into an unreadable whole-workspace graph.

## State and interaction contract

`store.ts` owns active tab, open tabs, conversation data and per-chat view state: pair, scroll offset, selected outcome, draft, follow flag, graph zoom and pan. Brain is permanent. Existing chats initially open at their latest exchange. State survives tab switching and closing/reopening, but is not persisted through a browser reload.

The transcript determines the current pair during manual scrolling when Follow chat is on. The graph slider and source actions explicitly set the pair and initiate a smooth transcript jump. A temporary scroll ownership lock prevents the resulting scroll events from overwriting that selection. Wheel or touch input interrupts the lock. Reduced-motion preference disables smooth transcript movement. A production streaming implementation should replace timing assumptions with an explicit navigation transaction if content height changes during a jump.

This intentionally overrides the old interaction specification's rule that transcript scrolling does not scrub the graph. The user's current request explicitly requires scroll synchronization. Timeline playback temporarily owns the pair; stopping playback restores scroll following. There is no permanent Follow switch in the interface.

Expanded graph is a dialog with Escape, focus containment and an inert background. The right rail and history can be collapsed. Narrow screens use overlays rather than squeezing three panes into unreadable columns. Desktop pane widths are fixed/responsive, not draggable.

## Visual foundation

| Token / principle | Current value / decision |
| --- | --- |
| Workspace | Charcoal and neutral gray surfaces; restrained borders |
| Human | Cyan `#38bdf8` — restored from the graph specification |
| AI | Amber `#fb923c` — restored from the graph specification |
| Stage | `#151719` |
| Main text | `#dedfdc` |
| Muted text | `#8c9195` |
| Typeface | Inter when installed, then system sans-serif; no remote font requirement |
| Surface geometry | Small radii for controls and tabs; rounded composer; avoid card-heavy chrome |
| Color usage | Contributor information in nodes, atoms and author markers; no decorative full-screen gradients |
| Motion | Stable positions; short appearance/size transitions; restrained terminal pulse; reduced-motion support |

These are proposed product tokens, not psychological facts about human or AI identities. Color is reinforced by author labels, legends and atom shape. A production accessibility audit remains necessary, particularly at graph scale and for color-vision differences.

The brain's neutral surface is independent of contribution colors. Its silhouette, grooves, layered translucency, surface lines and particles supply depth. Contribution points sit above this base. Orbit, zoom and camera presets provide spatial inspection. The integrated view now enables layered ambient motion: a close-fitting pearl atmosphere, light traveling along surface fibers and sparse motes moving tangentially above the folds. Semantic nodes remain fixed. Selecting a node reduces ambient intensity and speed. Pause motion freezes the decorative material without disabling navigation; reduced-motion preference starts it paused. Brain placement is stable illustration, not a semantic embedding or a claim about neuroanatomy. Replace its procedural geometry with a reviewed mesh if anatomical precision becomes a requirement.

## Graph semantics preserved and approximated

Preserved in the normalized projection: outcome identity and root, parent and related relationships, first appearance, cumulative human/AI ledger mass, per-pair activity, latest assistant terminal outcome, requirements, question origins and resolved provenance. Solid edges represent parents and dashed edges represent related outcomes. Edges terminate at node boundaries. Open questions use rings; resolutions retain origin and resolver information.

The local graph uses a stable two-column 2D projection suited to the narrow rail, root at world origin and the specified radius formula: child R = 14 + 14 × M / Mmax, followed by a common camera scale. Root radius is 24 before camera scaling. Frosted node images use an analytic diffusion approximation with cyan and amber sources at ±0.2R, contribution-weighted intensity, a fused highlight and a single outer shell. Brain nodes use a 3D sphere shader with the corresponding two-source emission model. These are real-time visual approximations, not physically simulated photon transport. Zero contribution produces zero intensity for that contributor; the structural root uses a neutral balanced fallback when it has no ledger mass.

All available atoms are drawn in upper-canopy rows spanning 45–135 degrees. Their tethers stop at sphere/bead boundaries. All outcome labels remain visible beneath their spheres, with a 12 px screen-space floor and a 13 px root label. Hover or keyboard focus reveals verbatim requirement/question content in a black-and-accent tooltip; click or Enter jumps to the source turn. Backend choice options are shown when supplied, and are not fabricated when absent. Source navigation targets a turn/speaker, not a highlighted exact substring. Labels use an unobtrusive background mask so edges cannot interfere with their text.

No cross-chat relationships are fabricated from similar titles or topics. The supplied data has no verified cross-chat links, so Brain shows conversation points and an explicit empty relationship state. `ChatLink` is a future type, not an implemented relationship pipeline. A future link should carry source/target IDs, relation type and evidence; selection should expose that evidence before jumping between conversations.

## Data provenance and limits

The compiler combines ten supplied pipeline exports with their matching repository corpus transcripts: c05, c04, c03, c07, c20, c27, c30, c10, c16 and c17. They contain 28 matched conversation pairs with no pair-count mismatches. Text is rendered as transcript content, not instructions executed by the application.

The uploaded golden_01 export has seven pairs while the repository transcript has eight; it was deliberately excluded rather than joined incorrectly. fixture_pair1 and all frozen engine fixtures remain untouched.

The seven-pair c05 cumulative mass regression is `[62, 237, 412, 625, 919, 1049, 1137]`. These are projected ledger values; the frontend does not perform LLM scoring.

Historical mass and recorded atom lifecycle can be reconstructed from supplied exports, but final requirement wording is sometimes all that is supplied. Earlier views can therefore show later revised wording. For exact historical replay, the backend must provide versioned text or per-pair atom snapshots. Attachment names are shown as references; attachment binaries are not loaded.

## Development setup

Apply the source overlay to the root of an existing Timeline checkout. The package intentionally excludes node_modules, the full original corpus and the rest of the repository. Generated normalized data is included, so original uploads are not required to run the prototype.

```bash
cd web
npm ci
npx vite --config vite.workspace.config.ts
# Open /workspace.html on the URL Vite prints.
```

Build and package:

```bash
cd web
npx tsc -b
npx vite build --config vite.workspace.config.ts
python scripts/package-workspace.py
```

This produces `web/dist-workspace/` and the standalone `web/cotrace-workspace.html`. The original app keeps its existing index.html and build path. The standalone bundle intentionally embeds the renderer and data, resulting in an approximately 1.2 MB file and a Vite chunk-size advisory.

To regenerate normalized data from original exports, run from repository root:

```bash
python web/scripts/compile-workspace.py --exports /absolute/path/to/exports
```

## Implementation map

| File | Purpose |
| --- | --- |
| web/workspace.html | Separate workspace entry point |
| web/vite.workspace.config.ts | Isolated production build |
| web/src/workspace/main.tsx | React mount |
| web/src/workspace/Workspace.tsx | Shell, tabs, transcript, navigation and event handling |
| web/src/workspace/workspace.css | Tokens, component styles and responsive behavior |
| web/src/workspace/store.ts | Zustand workspace and per-chat state |
| web/src/workspace/types.ts | Normalized rendering contracts |
| web/src/workspace/LocalGraph.tsx | Local outcome map, temporal scrubber and inspector |
| web/src/workspace/Brain.tsx | React/3D message boundary and conversation aggregates |
| web/src/workspace/brain-frame.html | Embedded Three.js vendor, scene DOM and host bridge |
| web/src/workspace/brain-engine.js | Procedural brain geometry, living surface layers, two-source material and interaction |
| web/src/workspace/photon.ts | Cached analytic two-source frosted-sphere texture |
| web/src/workspace/adapter.ts | Atomic application of normalized backend updates |
| web/src/workspace/data.generated.json | Actual matched transcript and graph projections |
| web/scripts/compile-workspace.py | Read-only export/corpus adapter |
| web/scripts/package-workspace.py | Standalone HTML packager |
| scripts/workspace-tests/smoke.cjs | Browser interaction checks |
| docs/workspace/THREE-LICENSE.txt | Renderer attribution |

## Backend connection

The repository's current frontend is fixture-driven and `server/` does not contain a running chat API. No real model, authentication or database was added. Connect those behind the existing frontend boundary rather than placing scoring in UI components.

Sending dispatches this event on window:

```ts
window.addEventListener('cotrace:send-request', async (event) => {
  const { chatId, text } = (event as CustomEvent).detail;
  // Call your authenticated service. Keep credentials server-side.
  // Have the engine return the normalized Chat projection.
});
```

When analysis completes, supply a full normalized `Chat` from `types.ts`:

```ts
window.dispatchEvent(new CustomEvent('cotrace:chat-updated', {
  detail: normalizedChat
}));
```

Alternatively import `applyChatUpdate(chat)` from adapter.ts. The update replaces that conversation atomically and updates Brain aggregates. It advances the graph pair only if the user was following the previous latest pair; historical inspection stays in place. Transcript auto-scroll on streaming updates is not implemented.

The normalized Chat includes: stable id, title/rootTitle/category/summary, totalPairs, dialogue turns, outcomes with stable layout coordinates and birth/source pair, atoms with origin/resolution/lifetime/source evidence, and one cumulative mass/terminal snapshot per pair. Use the supplied generated JSON as a concrete example. Pair indices are one-based. The adapter only performs basic shape checks; add full runtime schema validation, ID integrity and monotonic revision handling in production.

Next integration work, in order:

1. Implement authenticated chat creation/send, explicit loading/failure/retry/cancel states and server-side model calls.
2. Return engine-generated projections without recomputing scores in React; reconcile pending messages by stable message IDs.
3. Add durable tab/draft/reading state and data migrations.
4. Add versioned atom wording, source spans, verified cross-chat evidence and confidence policy.
5. Replace timing-based navigation locks as streaming is added; test interruption and out-of-order updates.
6. Test large graphs, label collisions, keyboard navigation, contrast, WebGL loss and performance across devices before release.

## Verification

- TypeScript project build: passed.
- Vite workspace production build and standalone packaging: passed.
- Browser interaction checks: passed, no page errors. Covers unique tabs, drafts, scroll following, outcome source jump, scrub feedback prevention, expanded dialog/Escape, Brain return position, tab close/reopen, search, new conversation and send without fabricated replies or graph data.
- Width checks at 390 and 320 pixels: no horizontal page overflow.
- Existing Python suite: 52 tests passed; original engine and frozen fixtures unchanged.
- Screenshot review: chat, expanded map and Brain inspected. Browser checks used Chromium with software WebGL; this is not a cross-browser or assistive-technology certification.

No remote GitHub branch, commit, pull request or deployment was published. The source overlay and standalone file are the reviewable handoff.


## v2 research and implementation decisions

Reviewed both supplied recordings: the 8.47-second Obsidian graph recording for the minimal canvas treatment and the 13.87-second CosmoGraph recording for surface flow, depth layers and focusing. Reviewed the actual Obsidian plugin, not the similarly named standalone graph library: https://github.com/n1ghtmare-dev/obsidian-cosmograph at commit c455f466f7df9c23724ba291aa9f2463ca553aaa. Primary implementation reference: src/graph/SphericalGraph.ts.

The relevant source mechanisms are createAtmosphere/createOuterAura (separate contour light), createOrbitingMotes (local tangent-plane particle motion), focusNode/startCameraTween (eased focus), updateNodeVisuals (selection/hover scale and depth hierarchy), and updateLabels/label-budget machinery. The brain adapts these ideas to its own folded anatomy and neutral pearl material. No spherical terrain or pink/purple color treatment was copied into the brain. The accompanying MIT notice records the referenced/adapted implementation patterns.

Brain labels are screen-space, centered below nodes, softly masked against the surface and prioritized for selection. Occluded rear labels are hidden, and overlapping candidates are deferred. Visible labels are clickable and keyboard-focusable. Node picking uses a larger invisible hit target than the rendered sphere. Hover and selection scale smoothly; selecting rotates the camera to the local surface normal using shortest-angle easing. Empty-space clicks and Clear selection remove focus. Initial anchors are deliberately spread across both hemispheres; assignment is stable during the session and does not claim a semantic embedding. Backend-defined persistent anchors remain the production integration target.

Timeline: frosted bottom capsule, cyan-to-amber progress rail, one notch per pair, Pn/N indicator, Previous, Play/Pause and Next. Playback steps every 1.8 seconds, restarts at P1 when played from the end, stops at the last pair and restores scroll following. A single-pair chat has a centered notch and disabled playback/navigation. The user explicitly requested no extra metric pill or status dashboard, so those optional specification elements are omitted. The graph keeps stable framing through the full sequence; births, dormancy, reactivation, resolutions and abandonment are driven by the supplied snapshots/lifetimes. New marks fade in; this version replaces resolved/abandoned geometry rather than implementing a continuous geometric morph.

Additional verification: refinement.cjs passed for removal of rail clutter, pair stepping, play/pause, scroll ownership after playback, resolution geometry, expanded dialog, advancing material time, motion pause, node picking/focus, responsive shell and zero browser errors. The original workspace smoke suite also passed after updating its selectors for the simplified controls. Existing Python scoring code was not changed; its 52-test pass was established in the initial delivery.

Remaining limits: small or dense graphs can still require zoom/pan/expand; no claim of universal zero label collision across arbitrary datasets. Historical text versions and missing structured choices cannot be reconstructed perfectly from final-state exports. Surface motion is purely decorative and does not imply new messages, neural activity or inference.
