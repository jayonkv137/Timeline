# EVIDENCE_SPEC: click a node, see exactly what was said, by whom, where

Status: **v1.0 implemented (10 Oct 2026)**, built on branch `s/evidence-linking` while Gemini ran S4. Build plan: Track S phase **SE** (`docs/plans/STANDALONE_V1_PLAN.md`).

**As built:**
- Engine: `engine/evidence.py`; `engine/projections/workspace.py` (truth fixes T1–T4; T5 = `evidence[]`); schema `$defs/evidence`.
- Audit: `scripts/evidence_audit.py` → `docs/plans/reports/SE_evidence_audit.md`.
- Tests: `tests/test_evidence.py` (21 tier1 tests, W7 on all 13 chats).
- UI: `web/src/workspace/evidence.ts`, `useEvidence.tsx`, `evidence.css`; LocalGraph `onAtom` / `activeAtom` plus a keyboard-reachable requirement list.
- E2E: `scripts/workspace-tests/evidence.cjs`, suite 3 of `npm run e2e`.

**Measured anchoring (final rules: exact → normalised → wrapping quote marks stripped → "…"-joined passages, any order):** 479 exact (11 repeated phrases, placed by reading order) · 106 normalised · 45 multi-part · **9 not in their message** = **630 / 639 (98.6%)** on exact words.

**Not yet built:** the Brain entry point (the Brain shows no requirement beads yet); the "wording changed" check (`textHash` is stored, but the browser does not compare it yet); the reverse selection ("show linked requirements").
Measured on the 13 processed chats with `scripts/evidence_audit.py`. Every number below is reproducible.

## Owner's words
> "if I click on a user requirement node or AI requirement then it should exactly map or highlight that specific thing in the original chat … if user raised this in a prompt, map to the exact place and highlight and show it; if AI did, map it to the exact place … this feature needs to be standard and built properly … it will work for all future upgrades, even when the extension comes"
> "it needs to be true and truthful … open questions have two parts, where the AI asks a question and the user replies … what is the part we need to show … user requirements and AI requirements all show the same colour coding and highlighting systems"

## 0. The feature in one sentence
**Click any requirement or question in the graph → the chat shows the exact words that support it, in the right speaker's message, highlighted in place → step through every source when there is more than one → one click returns you to where you were reading.**

The chat itself is the evidence viewer. There is no new panel and no proof dashboard.

---

## 1. What the engine already records (the foundation is there)

Every engine **action** is one act by one speaker in one exchange: `U(3,2)` = user, exchange 3, act 2. Each action carries a verbatim `evidence_quote` from that speaker's message (Step 1a/1b, checked by invariant 21). Requirements and questions point to actions by role:

| Engine record | Field | Count on 13 chats | Becomes evidence role |
|---|---|---|---|
| Requirement | `creation_action_ids` | 221 links on 173 requirements; **32 requirements have 2+ creating actions** | **Introduced** |
| Requirement | `revise_action_ids` (+ `revise` op with pair) | 15 links on 10 requirements | **Revised** |
| Requirement | `implementation_action_ids` | 523 links | **Carried out** (where the work was done) |
| Requirement | `contributing_action_ids` | 1,721 links (≈ 10 per requirement) | not shown in v1 (too broad to be evidence) |
| Question (slot) | `creation_action_ids`, `origin` | 41 questions | **Asked** |
| Question (slot) | `status` + `resolved_into` → that requirement's creating actions; `resolve` op pair | 9 answered | **Answered** |
| Question (slot) | `abandon` op pair | 12 dropped | **Dropped** (a state, no passage) |
| Question (slot) | still `open` | 20 open | **Still open** (a state) |

So "introduced, revised, answered" is already true data, but the workspace projection throws most of it away (§2).

## 2. Truth gaps in today's projection (`engine/projections/workspace.py`), fixed first

| # | Today | Effect | Fix |
|---|---|---|---|
| T1 | Uses only `creation_action_ids[0]` | 32 requirements lose their other source passages | Keep every creating action as evidence |
| T2 | Ignores `revise_action_ids` | 10 revised requirements always open their original wording | Add **Revised** evidence; the default source follows the version shown (§5.2) |
| T3 | Fallback `["U(1,1)"]` / `["A(1,1)"]` when no creating action exists | Invents an author and a place (latent: 0 cases today, but live data will hit it) | Missing → evidence state **Source not linked**, `origin: null`; never a fabricated speaker |
| T4 | "Answered" = any requirement whose `related_to` names a question | 12 requirements counted as answers, but the engine resolved only **9** questions (3 mislabelled) | Use `slot.resolved_into` + the `resolve` op (engine truth) |
| T5 | One `quote` + `sourcePair` + `sourceSpeaker` per atom | Can't represent "introduced in 8, revised in 12" | `evidence[]` list (§3) |

## 3. The evidence contract (additive: `workspace_bundle` 1.0 → 1.1)

Every atom (requirement, question, answered question) and every outcome gets `evidence[]`. Old fields stay for compatibility until the UI moves over.

```jsonc
"evidence": [{
  "id": "outcome 3:req 2#e1",
  "role": "introduced",           // introduced | revised | carried-out | asked | answered
  "actionId": "U(3,2)",           // engine action; null only when state is "missing"
  "pair": 3, "speaker": "human",  // from the action id, never inferred
  "messageId": "c05:3:user",      // platform message uuid when imported (extension-ready), else chat:pair:speaker
  "textHash": "sha256:…",         // of the message's normalised text: detects later edits
  "match": "exact",               // exact | normalized | multipart | ambiguous | message | missing (§4)
  "fragments": [{                 // one per highlighted span (several for multipart)
    "exact": "change the background to warm off-white",
    "prefix": "Keep the layout as it is, but ",   // W3C TextQuoteSelector context (≤ 32 chars each side)
    "suffix": ", and make the text easier to read",
    "start": 31, "end": 70        // W3C TextPositionSelector on the message's raw text
  }],
  "note": null                    // e.g. "quote found in exchange 12 (you)" for attribution flags
}],
"state": "open"                   // questions only: open | answered | dropped (+ "droppedAt": 4)
```

**Why this format:** `exact + prefix + suffix` plus `start/end` are the W3C Web Annotation Text Quote and Text Position selectors. Hypothesis uses the same pair to re-find passages in pages it doesn't control. The workspace transcript and the future browser extension therefore use **one anchoring algorithm on one record**.

## 4. Anchoring: from an engine quote to an exact place (deterministic, never invented)

Run at projection time in Python (engine), and again in the browser against the rendered text (the transcript strips markdown, so positions are re-found in what the user actually sees). Both sides share one test-vector file so they can never disagree.

| Step | Rule | Result `match` | Measured (639 actions) |
|---|---|---|---|
| 1 | Quote is an exact substring of its message | `exact` | **468 (73.2%)** unique |
| 2 | Exact after normalising: NFKC; curly → straight quotes; en/em dash → hyphen; markdown symbols removed; whitespace collapsed; case-folded (an index map turns hits back into raw offsets) | `normalized` | **101 (15.8%)** |
| 3 | Quote contains `...` or `…` and every fragment is verbatim, found in order | `multipart` (several fragments) | **50 (7.8%)** |
| 4 | The phrase occurs more than once: choose by prefix/suffix; else by action order (act *i* sits after act *i−1* in the same message); else ask the user to pick | `ambiguous` only if still tied | **11 (1.7%)** repeated phrases |
| 5 | Not found in its message → open the message, highlight nothing, say so. If the quote is found in **another** message, record that in `note` (an engine attribution issue to review, never silently redirected) | `message` | **9 (1.4%)** |
| 6 | No action linked at all | `missing` | 0 today |

**Result: 98.6% of quotes land on exact words; 1.4% open the right message with an honest "exact passage unavailable".**

The 9 misses are telling:
- the model paraphrased (e.g. `[script content]`)
- it corrected your typos
- it quoted the other speaker (c48 `A(13,3)` quotes your exchange 12)

Each becomes visible instead of hidden.

**Never:** fuzzy matching presented as exact; CSS selectors; scroll percentages; message ordinals alone.

**Invariant W7 (new):**
- every atom's evidence resolves to `exact | normalized | multipart`, or carries an explicit `match` state with a reason
- every evidence speaker equals its action's speaker
- every `answered` evidence comes from `resolved_into`

## 5. What the user sees

### 5.1 One colour grammar for every node type
- **Highlight tint = who said those words:** soft sky for you, soft amber for the AI. The same for requirements, questions and answers.
- **Relation chip** next to the highlight: *Introduced · Revised · Carried out · Asked · Answered*, plus the speaker in words ("by you", "by the AI"). Colour is never the only cue.
- **The message containing it** gets a faint outline, not a side stripe (the design system bans side stripes).
- **Selection** (which graph item is active) is a white outline on the bead. It is never a party colour, and it never changes the item's contribution light.

### 5.2 Which source opens first (the one that supports what you're looking at)
| Item | Default source at the viewed exchange *P* |
|---|---|
| Requirement, never revised | Introduced |
| Requirement revised at or before *P* | The latest revision ≤ *P* |
| Requirement revised after *P* | Introduced (the version shown at *P*) |
| Open question | Asked |
| Answered question | **Both together** (§5.3) |
| Dropped question | Asked + the state "Dropped at exchange *N*, no answer" |
| Requirement with 2+ creating actions | The first, with "Based on *N* passages" |

"Latest mention" is never the rule: a later message can merely repeat a requirement.

### 5.3 Questions have two parts
An answered question shows **Asked by the AI** (amber tint) and **Answered by you** (sky tint) as one linked pair:
- **Both visible in the reading area** (usually the next exchange): highlight both at once; the strip reads "Asked by AI · exchange 2 → Answered by you · exchange 3".
- **Far apart:** step 1 of 2 → 2 of 2. The question passage opens first.
- **Short answers** ("yes, that one"): the answer is primary, the asked option is the context. The chip says **"Confirmed by you"**, never "proposed by you".

### 5.4 The interaction (one click selects and reveals)
| Moment | Behaviour |
|---|---|
| Hover / focus a bead | Tooltip with the full label. No movement |
| Click (not drag: the existing 4 px threshold) | Bead selected; **the graph stays on its current exchange**; evidence resolves |
| Passage already comfortably visible | Highlight only, no scroll |
| Passage near | Short smooth scroll; the passage lands in the upper third |
| Passage far | Instant reposition (no long ride); a brief arrival pulse, then a steady highlight |
| Reduced motion | Instant, no pulse |
| Wheel, touch or key during the scroll | Stops it immediately |
| While inspecting | Highlight stays until you leave. No fade timers |
| Click the same bead again | Brings its passage back into view (doesn't deselect) |
| Click another bead | Switches evidence; **"Back to reading" still returns to where you started** |

**Evidence strip** (temporary, in the existing composer dock):

`[Revised] by you · exchange 12 · 2 of 3 ‹ ›   Back to reading   ✕`

- **Back to reading:** restores scroll position, viewed exchange, follow mode and graph camera from before the first click.
- **✕ / Escape:** clears the highlight and stays where you are.
- **Switching chats:** ends inspection.

**Graph and timeline stay separate.** Inspecting evidence never changes the viewed exchange; only the scrubber does. Chat-follows-graph syncing pauses while inspecting.

### 5.5 Honest states (every one has its own wording)
| Condition | What the user sees |
|---|---|
| exact / normalized / multipart | Highlight (multipart: each fragment, read as one source) |
| ambiguous | Highlight the best match + "This phrase appears 2× here" with ‹ › |
| message | Message outlined, no highlight; strip: "Exact passage unavailable · showing the message" + the saved quote in a tooltip |
| message + attribution note | as above + "The quote appears in exchange 12 (you)" |
| missing | "Source not linked yet" (no jump, no highlight) |
| Message edited since import (`textHash` differs) | "Wording changed since this was mapped" + the saved quote |
| Exchange still processing (live chat) | "Mapping exchange 9…" until `pair_ready` |
| Message not rendered (future virtualised transcript / extension) | Load it through the transcript's own route, then anchor; if impossible: "Original not loaded" + the saved quote |

## 6. Frontend mechanics
- **Text map:** for each rendered `.message-text`, walk its text nodes in order. Keep `(node, offset)` for every character, then apply the §4 normalisation with an index map. Search the quote (and prefix/suffix for ties) in that map, then build DOM `Range`s.
- **Highlighting:** the CSS Custom Highlight API (`CSS.highlights.set('evidence-human', new Highlight(...ranges))`, styled with `::highlight(evidence-human)`). It doesn't touch React's DOM, so no re-render conflicts and copy/select keep working. **Fallback** when `CSS.highlights` is missing: absolutely positioned tint boxes from `range.getClientRects()`.
- **State** (store, not exposed in the UI): `inspect = {atomId, evidenceIndex, returnTo:{scrollTop, pair, follow, camera}} | null`, separate from the outcome selection.
- **Entry points:**
  - graph bead (chat panel)
  - expanded graph dialog (closes, then inspects)
  - Brain (opens the chat tab, then inspects)
  - keyboard: the selected outcome's atom list as buttons
- **Later, the reverse:** select chat text → "Show linked requirements". No permanent underlines.

## 7. Extension compatibility (why this holds for every future upgrade)
- The same `evidence[]` records travel unchanged; only the anchoring target changes, from our transcript DOM to the host page DOM.
- `messageId` stores the platform's own message id when imported (Claude export uuid, ChatGPT message id). Anchoring finds the message by id first and never by title or ordinal.
- `textHash` detects edits and regenerated branches. The §5.5 states cover messages that are unmounted, edited, on another branch or deleted.
- **We promise exact highlights in our own transcript. In someone else's live UI we promise the honest state**, not 100% exactness.

## 8. Tests (added to the tiers)
| Tier | Test |
|---|---|
| tier1 | Projection keeps all creating actions, revisions and `resolved_into` answers; no fallback speakers (T1–T5) |
| tier1 | Anchor resolver against `tests/evidence_vectors.json` (generated from the 13 chats): match kinds and offsets fixed |
| tier1 | Invariant W7 on every chat |
| e2e | Click → highlight for each `match` kind; question pair; Back to reading; Escape; drag ≠ click; reduced motion; keyboard path |
| parity | The TypeScript resolver passes the same vectors as Python |

## 9. Build plan (Track S phase SE, zero LLM cost)
| Step | Builder | What | Done when |
|---|---|---|---|
| SE.1 | CC | Evidence builder in the projection: all creating actions, revisions, carried-out, asked, answered from `resolved_into`; T3 fallbacks removed; schema 1.1 (additive) | tier1 tests for T1–T5 green; 10 revised and 9 answered items carry the right evidence |
| SE.2 | CC | Python anchor resolver (§4) + W7 + `scripts/evidence_audit.py` report → `docs/plans/reports/SE_evidence_audit.md` + `tests/evidence_vectors.json` | the report reproduces 73.2 / 15.8 / 7.8 / 1.7 / 1.4 % on the 13 chats |
| SE.3 | AG+ | TypeScript resolver on rendered text + Highlight API + fallback | passes every vector (parity test) |
| SE.4 | AG | Inspection state, evidence strip, Back to reading, Escape, graph-stays rule | e2e: click → highlight → back restores scroll and exchange |
| SE.5 | AG | Question pair, multi-source stepping, relation chips, all §5.5 states | e2e per state, using real chats that contain each case |
| SE.6 | AG | Expanded-graph and Brain entry points; keyboard path; reduced motion | e2e + keyboard walkthrough |
| **SE.T** | You | Owner test: 10 nodes you remember, including a revised requirement, an answered question, a dropped one and an "unavailable" one. Are the highlighted words right? | log entry |

## 10. Real cases to test with (from the audit)
- **Revised requirements:** 10 in 8 chats (e.g. c05 `outcome 3:req 1` revised by you, `U(3,2)`; c20 `outcome 3:req 1` revised by the AI, `A(2,5)`; c48 `outcome 5:req 4_rev` revised by both, `U(20,2)` + `A(20,4)`)
- **Answered questions:** 9 (c05 `outcome 3:slot 1` asked `A(1,8)` → answered via `req 2`)
- **Multi-part quotes:** 50 (e.g. c05 `A(2,1)`, `A(4,10)`)
- **Not found:** 9 (c04 `U(4,1)`, c05 `U(1,2)`, c30 `A(1,5)`, c45 `A(6,2)`, c48 `A(3,2)`, `U(7,1)`, `A(13,3)`, `A(18,3)`, `U(20,1)`)

## 11. Decisions for the owner
1. Approve the evidence contract (§3) as an additive `workspace_bundle` 1.1 (a contract change after the S1 freeze).
2. Insert phase SE between S3 and S4 (recommended: uploads bring many new chats, and evidence must be right before that).
3. v1 shows Introduced, Revised, Carried out, Asked and Answered. "Contributing" stays out (1,721 links is noise).
4. Who builds SE.1–SE.2: Claude Code (engine truth), with Gemini on SE.3–SE.6.

## Sources
- [W3C Web Annotation: Text Quote / Text Position selectors (as used in web publication annotation)](https://www.w3.org/TR/wpub-ann/) · [Apache Annotator DOM anchoring](https://annotator.apache.org/docs/api/modules/dom.html) · [Hypothesis, Fuzzy Anchoring](https://web.hypothes.is/blog/fuzzy-anchoring/) · [Jon Udell, notes for an annotation SDK](https://blog.jonudell.net/2021/09/03/notes-for-an-annotation-sdk/)
- [MDN: CSS Custom Highlight API](https://developer.mozilla.org/en-US/docs/Web/API/CSS_Custom_Highlight_API) · [MDN: ::highlight()](https://developer.mozilla.org/en-US/docs/Web/CSS/::highlight)
