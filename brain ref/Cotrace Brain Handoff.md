# COTRACE · Interactive brain handoff

Version 0.1 · 8 October 2026

## What this is

A working, editable Three.js prototype for a neutral brain-shaped conversation landscape. It demonstrates the material, orbit/zoom behavior, optional contributor colors, outcome selection, labels, pair history, source events, and requirement/question states. Open `cotrace-brain-prototype.html` directly in a WebGL-capable browser; it bundles its renderer and needs no network connection.

This is a design and interaction foundation, not a finished application or anatomical asset. The brain is procedurally sculpted. Its folds are stylized, not anatomically validated. All eight outcomes, contribution values, anchors, and six conversation pairs are illustrative. No connection to the user's chat database is present.

The visual reference is the **brain organ**, including separated cerebral hemispheres, cerebellum, and a small brainstem. Do not substitute a human head, face, skull, or generic spherical network.

## Design decisions

1. **Neutral form first.** Pearl fibers and graphite shadows establish the brain. Human and AI colors belong to data marks. Both contributors can appear anywhere; hemispheres do not encode contributors.
2. **Stable meaning.** Camera movement changes the view. Material motion changes illumination. Neither changes an outcome's stored anchor or its relationships.
3. **Depth through layers.** Folded geometry, shadowed valleys, a glancing edge highlight, sparse fibers, and small surface particles provide detail at different scales. Do not make every layer equally bright.
4. **Readable information.** One selected neighborhood becomes prominent. Back-facing marks are excluded from pointer picking and label display. HTML text faces the screen and remains the same font size as the camera moves.
5. **Quiet color.** The initial mode is monochrome. Proposed contributor palettes are selectable experiments, not final brand decisions. These assignments are not psychological measurements of Human or AI identity.
6. **Source truth.** Labels use the supplied title verbatim. Contribution numbers come from the supplied ledger. Decorative fibers do not imply real relationships.

The supplied Obsidian reference is [n1ghtmare-dev/obsidian-cosmograph](https://github.com/n1ghtmare-dev/obsidian-cosmograph). The transferable direction is a layered material with restrained movement and stable graph information. This implementation is an original procedural study, not a port of that plugin. Three.js is bundled under its included MIT license.

## Scene layers and rendering contract

| Layer | Implemented appearance | Meaning and interaction |
| --- | --- | --- |
| Cerebrum | Two folded parametric hemisphere meshes; dark pearl shader | Stable visual scaffold; no anatomical localization claims |
| Cerebellum and stem | Smaller fine-ridged paired forms and curved stem | Anatomical silhouette only |
| Material light | Multiscale noise, slow ribbon drift, rim and specular terms | Decorative; never represents AI processing or new data |
| Surface fibers | 76 fine contour paths per cerebral hemisphere | Decorative paths; excluded from graph hit tests |
| Grain | Approximately 29,000 surface particles | Texture only; can be disabled |
| Outcomes | Translucent neutral shell with two small contributor cores | Persistent semantic objects; clickable |
| Relationships | Solid parent lines and dashed related lines | Data-derived, trimmed at endpoint sphere boundaries |
| Atoms | Solid requirement bead; hollow question ring; resolved core within origin ring | Visible for selected outcome; source-linked |
| Labels | Screen-space HTML with occlusion checks and collision suppression | Exact title text; full title in accessible outcome picker |
| Selection detail | Bottom detail strip with source action and atom buttons | Keyboard/touch alternative to tiny 3D targets |

The shader produces luminous-looking highlights without a bloom postprocessing pass. Core meshes approximate dual internal light; they are not physical volumetric photon scattering. That tradeoff keeps the study small and makes the contributor identities visible.

## Visual tokens

The stage intentionally uses a fixed dark theme as a material study. A light application shell can surround it; a light-stage material has not been designed here.

| Token | Value / role |
| --- | --- |
| Stage | `#080b10` |
| Inspector and detail surface | `#10141a` |
| Separators | `#252c34` |
| Primary text | `#e1e5ea` |
| Muted text | `#929da9` |
| Base shader pearl | RGB `(0.80, 0.84, 0.87)` before lighting |
| Controls | 7px radius, neutral selected fill |
| Text | System sans-serif; Inter if already available; no font download |
| Scene height | 650px desktop, 760px on wide desktop, 510px mobile |
| Responsive breakpoint | Inspector stacks below scene at 700px |
| Device pixel ratio | Capped at 1.7 |

| Palette key | Human | AI | Intended use |
| --- | --- | --- | --- |
| `neutral` | `#bcc5ce` | `#8b99a8` | Inspect form without committing to color |
| `clay` | `#d79a82` | `#7ca9d8` | Warm clay and restrained blue |
| `rose` | `#d98fa4` | `#55b9b0` | Rose and teal |
| `ochre` | `#c8ac65` | `#729fdc` | Muted ochre and blue |
| `cyan` | `#d5779c` | `#63bdd1` | Raspberry and cyan |

These are dark-stage mark colors. Do not reuse them automatically as small text on white. Keep textual contributor names and geometry cues, and test color-vision accessibility before choosing a final palette. Neutral mode intentionally has weak contributor differentiation.

## Interaction behavior

| Action / state | Implemented response |
| --- | --- |
| Initial load | Neutral material, three-quarter camera, no graph marks |
| Base material / Sample map | Switches semantic layers; preserves palette and pair |
| Drag empty space | Orbit with damped camera motion; no automatic rotation |
| Wheel / two-finger pinch | Zoom with clamped distance |
| Three-quarter / Side / Front / Top | Reproducible camera presets; keyboard-accessible buttons |
| Hover visible node or atom | Plain-text tooltip; no state mutation |
| Click visible outcome | Select, enlarge, turn camera toward it, reveal detail |
| Choose outcome from list | Same selection behavior, including hidden backside outcomes |
| Focus connected outcomes | Selected outcome and direct neighbors stay prominent; others dim |
| Clear selection / click empty space | Clear details; keep current camera |
| Select a requirement or question | Emit its source event; host app supplies transcript navigation |
| Open source turn | Emit the selected outcome's source event |
| Pair scrub | Reconstruct cumulative mass and atom resolution; hide unborn nodes |
| Selected node not yet born at new pair | Clear selection automatically |
| Palette change | Recolor semantic cores and atom provenance only |
| Reset | Neutral base, latest pair, initial view and material controls |
| Reduced-motion preference | Surface motion starts off; camera changes apply without easing |
| Hidden tab / offscreen study | Skip render work until visible again |
| Teardown | Cancel animation, disconnect observers, abort listeners, dispose GPU resources |

Surface motion slows to 30% and fiber brightness reduces while an outcome is selected. Positions do not wobble. There is no perpetual scene rotation. The surface motion toggle remains available in Base material mode.

### Pair and provenance semantics

For pair P, cumulative Human and AI mass are sums of their respective ledger entries whose pair is at most P. Radius is `0.055 + 0.065 * nodeMass / largestCurrentMass` world units, with 1.38× selected enlargement. Selection enlargement is emphasis, not additional mass. Because the denominator is the current maximum, older nodes can shrink proportionally as another node grows.

Positive mass added in P makes a node's core brighter. Parent tethers toward active outcomes use 0.68 opacity; dormant ones use 0.22. Unrelated nodes and edges dim further when neighborhood focus is active. Related lines remain quieter and dashed.

A requirement is a solid bead in its origin contributor's color. An open question is a hollow origin-colored ring. At `resolvedAt`, a resolver-colored solid core appears inside that ring. The origin remains visible. This follows the later provenance rule in the original specification; it does not erase the question's origin when resolved.

## Integration boundary

The prototype intentionally keeps backend transformation outside the renderer:

- Existing pipeline: `state.json`, `ledger.jsonl`, `operations_log`, dialogue/source records.
- Host adapter: resolve births, verbatim outcome text, contributor totals, related links, atom lifecycle, source turns, and persistent spatial anchors.
- Brain renderer: display the supplied normalized graph and emit interaction events.
- Host application: manage source navigation, persistence, loading/error state, filtering, and the rest of the product.

### Normalized data example

```js
const graph = {
  version: 1,
  maxPair: 3,
  nodes: [{
    id: 'outcome-1',
    title: 'The exact outcome.text string',
    description: 'Optional supporting context',
    root: true,
    born: 1,
    anchor: { side: 1, direction: [-0.4, 0.3, 0.85] },
    ledger: [
      { pair: 1, human: 4, ai: 1 },
      { pair: 3, human: 2, ai: 3 }
    ],
    source: { chatId: 'chat-123', turnId: 'turn-1' }
  }],
  links: [], // { source: nodeId, target: nodeId, kind: 'parent' | 'related' }
  atoms: [{
    id: 'question-1', nodeId: 'outcome-1', kind: 'question',
    text: 'The exact original question', origin: 'ai', born: 2,
    resolvedAt: 3, resolver: 'human', resolution: 'The exact decision',
    source: { chatId: 'chat-123', turnId: 'turn-3' }
  }]
};
```

`side` is hemisphere `1` or `-1`; `direction` is normalized internally. It is a placement coordinate, not a measure of brain function. Ledger values are incremental, finite, nonnegative units. Do not pass cumulative totals as incremental entries. `born` derives from actual first appearance, not a rendering guess. `source` is passed through; the host must validate and resolve it.

The validator catches malformed anchors, duplicate node/atom IDs, invalid ledger units, unknown links, and invalid pair ranges. It is not a complete production schema validator: it does not enforce tree acyclicity, root uniqueness, source existence, or backend-specific lifecycle invariants. Validate those in the adapter.

### Mount and connect

The standalone page automatically creates `window.cotraceBrain`. For a component integration, remove the final automatic mount in `src/brain.js`, retain the expected scoped markup, and call `CotraceBrain.create(element, graph)`. Use only one instance until DOM IDs and global exports are namespaced. A framework wrapper should dispose the instance on unmount.

```js
const root = document.getElementById('cotrace-brain');
const brain = window.cotraceBrain;
brain.loadGraph(graph);
brain.setMode('map');
brain.setPalette('clay');
brain.setPair(3);

root.addEventListener('cotrace:open-source', ({ detail }) => {
  // Supply your own transcript router; no network request happens here.
  if (detail.source) openConversationTurn(detail.source.chatId, detail.source.turnId);
});

const savedCamera = brain.getState().camera;
// Host decides when and where to persist this.
brain.restoreCamera(savedCamera);
// On component unmount:
// brain.dispose();
```

| Public method | Contract |
| --- | --- |
| `loadGraph(data)` | Validate a replacement before mutation; select latest pair; clear selection |
| `selectNode(id, {focus: true})` | Select and focus; `null` clears; unknown/unborn ID returns false |
| `setPair(number)` | Round and clamp to valid pair range |
| `setMode('base' \| 'map')` | Toggle semantic layer |
| `setPalette(key)` | Use one of the five palette keys |
| `setView(name)` | `home`, `side`, `front`, `top` |
| `getState()` | Current controls, selection, camera, node count and diagnostic frame count |
| `restoreCamera(camera)` | Restore valid theta, phi, radius and target; clamp range |
| `getProjectedNodes()` | Diagnostic positions, visibility and focus state; not persistent anchors |
| `dispose()` | Release scene resources and listeners |

Bubbling root events: `cotrace:modechange`, `selectionchange`, `pairchange`, `palettechange`, `graphchange`, and `open-source`, all with the `cotrace:` prefix. `open-source` supplies `{nodeId, atomId?, source, pair}`. No message is sent to another service.

## Relationship to your original graph specification

The original document is preserved as `docs/original-graph-spec.md`. Treat it as the source for conversation semantics. This prototype proposes a brain surface visualization and must not silently rewrite the existing per-chat graph.

| Original rule | Prototype status / integration instruction |
| --- | --- |
| Root fixed at `(0,0,0)` with permanent text | Surface study uses a surface anchor and keeps root title in the screen heading. Preserve origin rule in the per-chat graph; decide explicitly how global brain and per-chat view connect. |
| Exact outcome labels | Supported through `title`; adapter must copy `outcome.text` verbatim |
| Ledger-based radius and pair activity | Supported for supplied normalized ledger; no extraction pipeline supplied |
| Dual physical light in frosted glass | Approximated with two visible cores inside a transparent shell |
| Parent / related edges | Solid / dashed implemented; WebGL line width is renderer-limited, not exact CSS pixel width |
| Endpoint clipping | Implemented for node boundaries, including selected enlargement; curved routes are approximate |
| Upper atom canopy with no collisions | Small world-space upper offset implemented; this is not a screen-space collision guarantee under every rotation |
| Provenance ring with resolution core | Implemented with sample lifecycle |
| Full slot choices and alternate decision trace | Add `choices`, selected option and resulting requirement data in host detail UI |
| Direct click-to-chat navigation | Atoms emit source events directly. Outcome click currently selects; explicit source button emits. Host can also navigate on `selectionchange` if retaining original one-click behavior. |
| Terminal active conversation cursor | Not inferred from sample data; host must identify the final relevant AI action before adding a beacon |
| Unrelated tangents with repulsive motion | Not implemented; surface anchors are intentionally stable |
| Multi-chat global brain | Not implemented as aggregation; this dataset illustrates one conversation's mechanics |

## Replacing the procedural brain

1. Create or license a nonmedical-use anatomical GLB with separate left/right cerebrum, cerebellum, and stem. Keep recognizable large lobes and irregular branching sulci; avoid uniformly sinusoidal grooves and mirror-perfect anatomy.
2. Normalize it to this coordinate frame: Y up; anterior toward negative X; posterior toward positive X; hemisphere separation on Z. Current cerebrum spans approximately X ±2.1, Y ±1.4, Z ±1.3 world units.
3. Keep semantic anchors in a separate store. Introduce an `anchorToWorld(anchor)` adapter instead of calling `brainPoint` directly. For the final mesh, use stable surface IDs with triangle/barycentric coordinates and a small normal offset. Keep an anchor migration version when replacing topology.
4. Retarget particles and fibers to the real mesh. Use measured surface normals and density variation. Do not carry parametric hemisphere fibers onto a different mesh without resampling.
5. Replace coarse occlusion proxies with final-mesh BVH raycasts or a GPU depth test. Keep hidden-node picking excluded. Build collision-safe link routes or surface geodesics; do not let a semantic line tunnel through anatomy.
6. Separate low-frequency form from shader detail. Use subtle normal detail for secondary folds, sparse bright fibers, and a restrained Fresnel edge. Add selective bloom only after labels and contributor color remain clear at normal exposure.
7. Recheck side, top, front, back, and close views; test labeled graph states, not just a beautiful empty brain render.

A generated reference image can guide material and shape, but it does not supply a usable mesh, UVs, depth, topology, or stable anchors.

## Production work that remains

- Adapt actual pipeline outputs and source navigation; store anchors so reloads do not shuffle the map.
- Decide global brain aggregation and the transition into your existing per-chat graph.
- Finalize anatomical mesh and material art direction; this study is not final anatomy.
- Add terminal cursor from real backend action ordering, exact question choices, and complete provenance records.
- Replace approximate label sizing with measured bounds; resolve atom/label collisions and cross-brain link routing.
- Add clustering and zoom-level detail for realistic node counts. This eight-node scene does not validate thousand-node performance.
- Optimize materials, instancing, draw calls and raycasts against target hardware; add quality tiers and WebGL context recovery.
- Add a complete non-WebGL text view. Current fallback reports unavailable WebGL; it does not run the scene controls.
- Check keyboard flow, color vision and text contrast with the final palette; listen for runtime changes to reduced-motion preference.
- Bundle Three.js with the host build system. The pinned legacy UMD renderer here is for a portable offline preview, not a recommendation to freeze your production dependency.

## Suggested brief for the development agent

> Use this package as the working visual and interaction foundation for COTRACE's brain view. Start by opening the standalone prototype and reading this handoff plus the preserved original graph specification. Keep the neutral brain, contributor mapping, provenance geometry and stable anchors separate. Integrate the existing pipeline through a tested adapter; do not invent data or replace existing graph semantics. Connect source events to the transcript. Preserve the original per-chat root rule unless we explicitly approve a different spatial model. Replace the procedural anatomy through an anchor adapter, then improve occlusion, label placement and scale behavior. Retain keyboard access and reduced-motion support. Treat palettes and material controls as exploration settings, not final end-user settings. Report any conflict between the original specification and this study before changing meaning.
