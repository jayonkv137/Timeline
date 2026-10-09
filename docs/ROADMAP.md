# ROADMAP.md — every track on one page

**Overall goal:** your real AI chats, mapped live as a node graph, in a product other
people can install and trust.

> **Current program (9 Oct 2026):** Track S, a standalone v1 that connects the engine to the
> workspace: upload your history, chat live, everything mapped. Plan:
> [`docs/plans/STANDALONE_V1_PLAN.md`](plans/STANDALONE_V1_PLAN.md). It absorbs G1 (S1–S2) and G2 (S5).

Written 8 October 2026. Dates are estimates at a steady part-time pace (about 4–5 focused
sessions a week) and should be re-dated at every milestone.

---

## 1. Milestones

| # | Milestone | What you can do then | Needs | Estimate |
|---|---|---|---|---|
| M1 | **Graph on real data** (G1) | Open any processed chat in the app, scrub it, watch it rebuild live from replay | G1 | ~3–4 weeks · early Nov |
| M2 | **Affordable engine** (X1) | Know the per-pair cost and model per step, with measured quality | Cost seam, bake-off, Jev replay test | ~4–5 weeks · mid Nov |
| M3 | **Graph speaks the design language** (D-track M1) | The graph in its final visual language, both themes | D0–D5 | ~6–8 weeks · late Nov |
| M4 | **Live chat in the app** (G2) | Chat in the app; the graph grows as you talk | M1, M2, E4 batch-equals-live | ~8–9 weeks · early Dec |
| M5 | **Your coding sessions mapped** (G3a) | Claude Code and Codex sessions graphed live on your machine | M4 | ~10 weeks · mid Dec |
| M6 | **Design system 1.0** (D8) | Every surface built from one system; any agent builds UI correctly | D0–D8 | ~12–14 weeks · Jan |
| M7 | **Extension alpha** (G3b) | Side panel on claude.ai and chatgpt.com for you and 5 testers | M4, M6 side-panel shell | ~16 weeks · late Jan / Feb |
| M8 | **Public beta** | Open source, privacy policy, store listing, legal review | M7, E5 calibration | ~20 weeks · Feb / Mar 2027 |
| M9 | **Brain v0 on your own archive** (B1 + G4a) | Your 313+ chats mapped in batch with cheap models, grouped into regions with evidence-backed links; a Brain tab in the web app | M2, D5 grammar, B1 brief | Feb–Mar 2027, in parallel with or instead of M7 (your call, §3) |
| M10 | **The head in 3D** (G4b) | The Brain as a navigable Human × AI head; project and chat levels in depth | M9, M6 | After M9 |

The first visible win is M1, about a month out. The public goal is M8; the vision is the
Brain (M9, M10), described in `docs/Brain Vision.md`.

---

## 2. Tracks

| Track | Role and tool | Now | Next | Brief |
|---|---|---|---|---|
| **E** Engine | ENGINE · Claude Code (Opus) | E2 closed (`e2-done`) | G1.S1–S4 (about 2 days), then E3 stability | E3: **to write** |
| **C** Corpus | DATA OPS · Antigravity | C0 and C3 done; c37–c55 promoted but uncommitted; `ARCHIVE_REPORT.md` missing; ChatGPT and Gemini exports pending | C1 report, commit c37–c55, C4 public datasets | `docs/C Track Brief.md` |
| **G** Graph and app | APP · Codex or Antigravity | Not started | G1.S5–S7 | `docs/briefs/G1 Brief.md` |
| **D** Design system | DESIGN SYSTEM · Claude Code with you | Not started | D0 (ends with the graph-view lock for G1) | `docs/briefs/D Track Brief.md` |
| **X** Cost and models | ENGINE · Claude Code | Research done (cost playbook, Jev analysis) | Cost seam, bake-off, Jev replay test | X1: **to write** |
| **B** Brain data layer | ENGINE · Claude Code | Not started. The engine works per chat only | B1: cross-chat links with evidence types (similar, continued, reused), regions, project grouping, beats for long chats | B1: **to write** |

Later briefs: G2 (live in app), G3 (outside sources, extension), G4 (Brain view and head),
E4, E5.

**One sequencing decision for you, around January:** after M5, the app lane can do the
extension first (M7, reaching other people) or the Brain first (M9, the vision, on your own
archive). Both need the same engine and design foundations. Batch-mapping all 2,759 pairs
costs roughly $5–15 with the cheap setups in the cost playbook, against about $780 at
today's settings.

---

## 3. What runs at the same time (next 4 weeks)

| Week | Claude Code: ENGINE | Codex or Antigravity: APP | Claude Code with you: DESIGN SYSTEM | Antigravity: DATA OPS | You |
|---|---|---|---|---|---|
| 1 | G1.S1 snapshots and churn report | — | D0.S1–S4 audit, setup, scaffold | C1 report | Pre-work for G1 and D; gate G1.S2 |
| 2 | G1.S3 graph projection | G1.S5 server | D0.S5 graph-view lock → HANDOFF; D1 interview | Commit c37–c55 | Approve the graph-view lock; D1 answers |
| 3 | G1.S4 invariants, replay → HANDOFF | G1.S6 `build graph-view` | D1 personas; D2 references | C4 public datasets | D1 decisions |
| 4 | G1.S9 close; X1 starts | G1.S7 live, S8 critique and polish | D2 three directions | — | Gate G1.S8; pick a D2 direction |

**Limits that keep this sane**

- **One writer per path.** ENGINE, APP, DESIGN SYSTEM and DATA OPS never write the same
  folder. Handoffs go through `BUILDLOG.md` (HANDOFF, BLOCKED, NOTICE).
- **Your attention is the bottleneck.** At most one co-creation conversation (the D track)
  plus two build agents at a time. Build agents work while you're in design.
- **Gates are yours:** G1.S2 and S8, every `Decide:` in the D track, the X1 model choice.

---

## 4. How you see progress

| What | Where |
|---|---|
| Design work, every step | `mockups/index.html` in the Claude Code browser pane (the `mockups` launch entry), with theme, state and colour-blindness toggles |
| Design decisions | `docs/design-system/decisions/INDEX.md` |
| Where each track stands | `docs/design-system/STATE.md`, `BUILDLOG.md`, `git log` and tags |
| The real product | `web/` dev server: the panel and graph on real chats (from G1) |
| Components and tokens | The gallery route in the web app (from D3) |
| On your phone | Any page published as a private Claude artifact |
