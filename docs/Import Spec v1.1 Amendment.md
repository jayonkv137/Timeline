# IMPORT_SPEC v1.1 — AMENDMENT

**Amends:** `docs/IMPORT_SPEC.md` v1.0
**Adds:** three official bulk-export formats, a two-stage archive model, triage mode,
and one new open question.
**Does not change:** the `dialogue.json` contract, the pairing rules, the origin model,
or anything about tiers T1/T2/T3. v1.0 stays in force everywhere it is not amended here.

---

## A. Why this amendment exists

v1.0 handles one format: the Claude Exporter browser extension. That is a per-chat tool.

All three platforms offer an **official account-wide export**, which is a better source in
every way: one request, complete history, stable schema, no extension, no manual repeating.
Each has a different shape, and one of them has a structural problem that touches the
engine's pair model rather than just its parser.

---

## B. The two-stage model

A full history is hundreds or thousands of conversations. Ingesting all of them as corpus
entries is wrong: too large to classify, too expensive to process, and too personal to
commit. So the pipeline splits.

```
raw export zips                      (never committed, never edited)
        │
        ▼  stage 1: ARCHIVE
data/archive/<platform>/<conv_id>.json      canonical record, one per conversation
data/archive/registry.json                  one row per conversation, all metrics
        │
        ▼  stage 2: SELECTION  (explicit, by id)
data/corpus/<chat_id>/                      full corpus entry, exactly as v1.0 defines
```

**Stage 1 is cheap, complete and automatic.** Every conversation from every platform gets
converted and measured. No LLM calls, no judgement.

**Stage 2 is deliberate and small.** Only chosen conversations become corpus entries.
Promotion is by id, recorded in a manifest, and reproducible.

### The canonical archive record

One file per conversation. Deliberately minimal: enough to triage, not a second contract.

```json
{
  "conv_id": "chatgpt_a1b2c3",
  "platform": "claude" | "chatgpt" | "gemini",
  "source_kind": "claude_official",
  "title": "Fixing stuttering box page animation",
  "created_at": "2026-05-18T13:27:25Z",
  "updated_at": "2026-05-18T14:02:11Z",
  "turns": [
    { "speaker": "user" | "ai", "text": "...", "ts": "...", "raw_role": "human" }
  ],
  "platform_meta": { "model": "...", "branch_count": 3 },
  "import_spec_version": "1.1"
}
```

`turns` is a flat alternating-ish list. Pairing rules from v1.0 §6 are applied at stage 2,
not stage 1, so the archive keeps whatever the platform gave.

### Storage and privacy

- `data/archive/` is **gitignored**. It is a personal archive, not repository content.
- `data/archive/registry.json` **is** committed, with `title` redacted for any record
  marked `sensitive`.
- `data/corpus/` follows whatever the repository's visibility decision is. If the repo is
  public, corpus entries are gitignored too and only the selection manifest is committed.

---

## C. Format C1: `claude_official`

**Obtain:** Settings → Privacy → Export data, on web or Desktop. Not available from iOS or
Android. Arrives by email as a zip. The link expires quickly, download immediately.

**Detect:** a `conversations.json` whose records contain a `chat_messages` array.

**Note this carefully:** the official export uses `chat_messages`, while the Claude
Exporter extension format from v1.0 §5.1 uses `messages`. They are different formats from
the same vendor. The detector must distinguish them and must not assume.

**Map:**

```
chat_messages[].sender "human"     -> speaker "user"
chat_messages[].sender "assistant" -> speaker "ai"
text or content blocks             -> text
created_at                         -> ts
name or summary                    -> title
uuid                               -> conv_id, prefixed "claude_"
```

Where a message carries content blocks rather than a plain string, concatenate the text
blocks in order and record any non-text block in `dropped_media`, as v1.0 already does for
placeholders.

**Known gaps, record them in the registry:** Projects are not included in the export, and
memory is not included either. Any conversation that depended on Project instructions is
missing that context, and the engine will read it as if the user supplied nothing. Mark
such records `context_incomplete: true` where detectable.

---

## D. Format C2: `chatgpt_official`

**Obtain:** Settings → Data Controls → Export data. Emails a zip containing
`conversations.json` and a `chat.html` viewer. Usually minutes, occasionally days. Link
expires in 24 hours.

**Detect:** records containing a `mapping` object whose values have `parent` and
`children` fields.

### The structural problem

ChatGPT does not store a conversation as a list. It stores a **tree**. Every message node
has one parent and any number of children. Regenerating a reply, or editing a prompt,
creates a sibling branch. The conversation you actually had is one path through that tree.

This is not only a parsing question. **It breaks the pair model.** A regenerated reply
means two AI messages answering one user message. v1.0 §2 requires exactly one `user` turn
followed by exactly one `ai` turn per pair.

### The rule

1. Find the current leaf, the node the platform marks as the active end of the
   conversation. If several candidates exist, take the one with the latest `create_time`.
2. Walk `parent` pointers from that leaf to the root.
3. Reverse. That path is the conversation.
4. Drop system and tool nodes, and nodes with empty content, recording counts.
5. Everything not on that path is a discarded branch.

**Rationale:** the leaf-to-root path reconstructs the conversation as the person actually
experienced it. Any other selection reconstructs a conversation that never happened, and
attributing agency in a conversation that never happened is meaningless.

**New fidelity fields:**

```json
"branches": {
  "total_nodes": 84,
  "nodes_on_path": 46,
  "discarded_branches": 7,
  "regenerations": 5,
  "user_edits": 2
}
```

A conversation with many regenerations is a weaker corpus entry, because the discarded
attempts were part of the person's real process and the engine will not see them. Grade
accordingly: `regenerations / pairs > 0.3` contributes toward `degraded`.

**Logged as Q9.** See section G.

---

## E. Format C3: `gemini_takeout`

**Obtain:** Google Takeout → Deselect all → **My Activity** → All activity data included →
Deselect all → **Gemini Apps** only → OK → Next step → choose **JSON** → Create export.

Two traps, both documented by users:

- The product entry named "Gemini" exports custom Gems, **not** chat history. Only the
  My Activity path yields conversations.
- If Gemini Apps Activity is switched off in the Google account, nothing was saved and the
  export will be empty. Several users report the option failing to appear even with
  activity enabled, so verify the zip actually contains conversations before planning
  around it.

**Detect:** a zip or folder containing a `Gemini Apps` directory.

**Three known layouts. The parser must sniff, not assume:**

| Layout | Shape |
|---|---|
| A | one JSON file with a top-level `conversations` array |
| B | one JSON file per conversation inside `Gemini Apps/` |
| C | HTML activity records, no JSON available |

**Role mapping:** `user` to user, `model` to ai, `system` to system and excluded.

**Layout C:** attempt a basic HTML-to-text extraction, mark every record
`fidelity_grade: degraded` regardless of image count, and set
`extraction_method: "html"`. HTML activity records lose structure, and a record whose
structure was inferred should never be trusted for attribution measurement.

If Takeout produces nothing usable, say so in the registry and stop. Do not fall back to a
browser extension silently; that is a different `source_kind` with different fidelity.

---

## F. Triage mode

New to `scripts/ingest_export.py`, or a sibling `scripts/archive_scan.py`.

```bash
# stage 1: convert every conversation in an export into the archive, no selection
python scripts/archive_scan.py --export path/to/claude_export.zip --platform claude

# print the triage table, newest first
python scripts/archive_scan.py --report

# stage 2: promote chosen conversations into the corpus
python scripts/ingest_export.py --from-archive chatgpt_a1b2c3,claude_9f8e7d --out data/corpus
```

**The triage table**, one row per conversation, computed with zero LLM calls:

```
conv_id            plat  pairs  chars   img/pair  regen  lang  code  grade     title
claude_9f8e7d      cl       14   50718      0.12      -   en    yes   clean     Portfolio about page redesign
chatgpt_a1b2c3     gpt      31  184220      0.00      6   en    yes   degraded  API design for booking service
gemini_5c4b3a      gem       6   22104      0.00      -   de    no    clean     Wohnungsbewerbung schreiben
```

**Computed metrics, all mechanical:**

| field | how |
|---|---|
| `pairs` | after v1.0 §6 pairing rules |
| `total_chars`, `max_turn_chars` | sum and max |
| `images_per_pair` | placeholder count over pairs |
| `regenerations` | ChatGPT only |
| `language` | heuristic on the first three user turns, stdlib only |
| `has_code` | fenced block present |
| `fidelity_grade` | clean ≤0.05, degraded ≤0.5, unusable >0.5 images per pair; ChatGPT regeneration ratio and Gemini HTML extraction also push toward degraded |
| `sensitive` | keyword flag, see the Programme brief |

**Deduplication.** The same conversation may appear in two exports taken at different
dates. Key on `(platform, conv_id)`. On collision keep the record with more turns and
record `superseded: <older updated_at>`.

---

## G. New open question

```markdown
## Q9 — ChatGPT conversation trees and the pair model (OPEN)
- **What:** ChatGPT's official export stores conversations as a `mapping` tree with parent
  and child pointers. Regenerated replies and edited prompts create sibling branches, so a
  single user message can have several AI replies. IMPORT_SPEC §2 requires exactly one
  user turn and one AI turn per pair.
- **Options considered:** (a) take the leaf-to-root path as the conversation and discard
  branches; (b) treat each branch as a separate conversation; (c) include all siblings as
  consecutive AI turns and let the merge rule collapse them.
- **Taken:** (a). The leaf-to-root path is the conversation the person actually
  experienced. (b) invents conversations that never happened. (c) attributes influence to
  text the person rejected, which is the opposite of what the engine is for.
- **Consequence:** the discarded attempts were part of the person's real process and the
  engine will not see them. Recorded in the `branches` fidelity block so the loss is
  visible, and conversations with a high regeneration ratio are graded down.
- **Status:** OPEN until C-track C1 reports real regeneration ratios across the archive.
  If regenerations are common, a future tier may need to model them as EXECUTOR retries.
```

---

## H. What does not change

Stated so nothing drifts:

- `dialogue.json` stays exactly as v1.0 §2 defines it. No new fields, no schema change.
- Pairing rules v1.0 §6 apply unchanged, at stage 2.
- Origin tagging and the injected-text decision, Q5, unchanged.
- `attachments` stays `[]`. Attachments are still T2.
- Agentic transcripts are still T3 and still refused.
- Every new format produces the same three corpus files. **No format gets a special path
  into the engine.** If one seems to need a bypass, the importer is wrong.
