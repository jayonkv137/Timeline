# COTRACE brain study

Open `cotrace-brain-prototype.html` in a modern WebGL-capable browser. The page is self-contained and offline.

- Begin in **Base material** and drag the brain.
- Choose **Sample map**, then select an outcome or use **Find an outcome**.
- Select **Visual direction** and compare Pair 3 (open question) with Pair 5 (resolved).
- Compare contributor palettes without recoloring the brain.
- Read `COTRACE-BRAIN-HANDOFF.md` before integrating.

## Edit and rebuild

Edit `src/scene.html`, `src/styles.css`, `src/brain.js`, and `src/sample-data.js`.

```sh
python3 build.py
```

`vendor/three.min.js` is Three.js 0.160.1. Its MIT notice is in `vendor/THREE-LICENSE.txt`. No runtime network request is required.

## Verification

Install Playwright in your development environment and install its Chromium browser, then:

```sh
node tests/smoke.cjs
```

Alternatively set `CHROME_PATH` to a Chromium executable. The test writes three screenshots to `docs/` and checks the key state transitions. See `docs/validation.md` for the recorded scope and limits.

This is a procedural design prototype with sample data, not a finished anatomical model or full application.
