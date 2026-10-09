# Validation record

8 October 2026 · Interactive study v0.1

Verified in headless Chromium using software WebGL/SwiftShader. No JavaScript page errors or console errors occurred during the smoke test.

## Passed

- First load renders the neutral 3D brain.
- Pointer click selects a visible outcome; selected details update.
- Front-facing nodes are available while back-facing nodes are excluded from visible picking candidates.
- Selecting a backside outcome through the native select rotates it into view.
- Pair 3 shows the AI question open; Pair 5 shows it resolved by the Human.
- Pair 3 contribution values match the sample incremental ledger: Human 5, AI 3 for Visual direction.
- Atom and outcome source events contain their expected identifiers and source turns.
- Pair 1 hides unborn outcomes and clears a selection that no longer exists.
- Invalid replacement data is rejected before replacing the existing graph.
- Reset restores neutral palette and base mode.
- Layout has no horizontal page overflow at 390px or 320px.
- Reduced-motion preference starts surface animation off.
- Dispose stops rendering.
- No overlap among visible HTML outcome labels in the inspected desktop selected state.
- Desktop and mobile screenshots inspected manually; mobile field of view adjusted to retain the silhouette.

`tests/smoke.cjs` reproduces the main behavioral checks and writes screenshot evidence. Test screenshots are `base.png`, `selected.png`, and `mobile.png`.

## Limits

This does not certify production performance, all label arrangements, color-vision accessibility, physical touch gestures, or Safari/Firefox/mobile GPU behavior. Surface motion and camera movement were observed in a browser renderer; this is not a usability study. The eight-node sample is not a large graph load test. There is no backend source-navigation integration to verify.

No real conversation data is included. Decorative material is not a functional brain scan or anatomical model.
