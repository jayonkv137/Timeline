# Design System State

**Programme:** The Human × AI Co-Creation Design System (D Track)
**Last Updated:** 2026-10-09
**System version:** v0.1.0, baseline from the workspace prototype (DDR-002)
**Current Phase:** Foundation built; programme paused for backend integration
**Next design phase:** UI/UX phase after integration (resumes D2.S3 directions → D4 → D5 → D6 on top of v0.1)

---

## What exists now

- [x] **Tokens:** `web/src/design-system/tokens/tokens.json`, 289 tokens (168 primitive, 53 semantic, 68 component), DTCG, three tiers, dark default + provisional light, `.theme-dark` stage scope.
- [x] **Build:** `build.mjs` → `tokens.css`, `tokens.ts`, `tokens.numeric.json`, `docs/DESIGN.md`. `npm run tokens` / `tokens:check`.
- [x] **Adoption:** workspace stylesheets migrated (545 values), graph canvas reads `tokens.ts`, `main.tsx` loads `tokens.css`. Visually near-identical (drift ≤ 1 scale step).
- [x] **Docs:** `DESIGN.md`, `AGENT_GUIDE.md`, foundations (architecture, colour, typography, layout, motion, dataviz, accessibility, voice), `components/INVENTORY.md`, `surfaces/README.md`, `DEBT.md`.
- [x] **Checks:** ui-craft `detect.mjs` reads `DESIGN.md`. Undocumented colours in our code went from 27 to 3.
- [x] **Graph grammar:** share ring, bead rules, plan-B click (DDR-006).
- [x] **Full application pass:** 3D Brain on tokens and party colours; spacing on the grid; side-stripes and width animations gone. Detector 48 → 8.
- [x] **Gallery:** `web/design-system.html`, a living reference generated from the tokens (dark/light, colours with contrast, type, space, shape, elevation, graph grammar, components). Run `cd web && npm run workspace`, open `/design-system.html`.

## Phase record

- [x] **D0** audit, scope, governance, scaffold, graph-view v0 lock
- [x] **D1** personality, principles, personas (DDR-001)
- [~] **D2** references and teardowns done; **D2.S3 directions deferred** (DDR-002); identity (D2.S5) open
- [x] **D3** architecture built (tokens, build, outputs, scopes, versioning policy)
- [ ] **D4** foundations: v0.1 baseline values documented; D4 decisions (face, ratio, light theme, high contrast, density) open
- [ ] **D5** grammar: chat level baseline (DDR-006); brain, project and pair levels reserved; size vs thickness open
- [ ] **D6** components: inventory done; extraction not started
- [ ] **D7** patterns: not started
- [ ] **D8** docs and release: v0.1 docs and gallery done; release test not done

## Open decisions

| Decision | Phase | Status |
|---|---|---|
| **DDR-007 Chats in the Brain** (lights) | pre-D5 | **Superseded** by DDR-008 (owner rejected floating lights) |
| **DDR-008 Symbiotic cortex** (cell territories, surface circuits; rulebook `foundations/BRAIN_SYSTEM_SPEC.md`) | pre-D5 | **Proposed, rendered**: owner to decide on open questions |
| DDR-003 Name and mark (head motif) | D2.S5 | Open |
| DDR-004 Token naming grammar | D3 | **Effectively settled by v0.1** (`foundations/architecture.md` §3); record formally when the owner confirms |
| DDR-005 Party colours | D4.S1 | Open. Current cyan/amber passes colour-vision tests; rose and cyan candidates fail deutan |
| Inter or another face; bundled font | D4.S2 | Open |
| Light theme values; high contrast; compact density | D4 | Open |
| Size = mass or thickness = contribution | D5.S1 | Open |
| The four extra looping animations | D7 | Open (DEBT #4) |

## Next immediate step

No design step is active. The owner chose to finish backend integration before resuming visual design. When it resumes: start from `DEBT.md`, then D2.S3 directions rendered on top of the v0.1 tokens.
