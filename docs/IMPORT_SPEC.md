# IMPORT_SPEC.md — v1.0

How raw chat exports become engine input.

Authority: sits below COTRACE_PIPELINE_SPEC, beside PANEL_SPEC / INTERACTION_SPEC,
above ARCHITECTURE and the briefs. Read-only from the build side.

---

## 0. Scope

**v1 handles text only.** One human message, one AI message, both plain text.

Everything else is recognised, recorded and excluded from the pipeline input, never
silently dropped. The corpus entry always tells you what was lost.

Three tiers, built in order. Do not start a later tier until the previous one is closed.

| Tier | Covers | Status |
|---|---|---|
| **T1** | Plain text human turns and AI turns | **This spec. Build now.** |
| **T2** | Attachments: images, PDFs, files, and AI-produced artifacts | Reserved. Fields exist, unimplemented. |
| **T3** | Agentic transcripts: tool calls, tool results, sub-agents, thinking | Reserved. Needs its own pairing model. |

Rationale: the whole system rests on prompt-and-response attribution. Until that is
proven correct on clean text, adding modalities only multiplies the ways it can be
wrong.

---

## 1. Corpus entry layout

One folder per chat under `data/corpus/`.

```
data/corpus/<chat_id>/
  source.<ext>       raw export, byte-identical to what the exporter produced. Never edited.
  source.md          optional human-readable copy, for hand-labelling. Not parsed.
  dialogue.json      normalised engine input. Validates against dialogue.schema.json.
  source_meta.json   provenance and fidelity sidecar. NOT a contract artifact.
  meta.yaml          human-authored description of the chat. Written by the owner.
```

`<chat_id>` format: `c<NN>_<task_type>_<length>`, e.g. `c01_coding_short`,
`c07_writing_long`. Lowercase, underscores, no spaces.

### Why a sidecar rather than extra fields

`dialogue.schema.json` is a Phase 0 frozen contract with `additionalProperties: false`.
Provenance fields cannot be added to it without breaking the frozen fixture. The same
problem was solved the same way in SPEC_QUESTIONS Q3 with `run/pipeline_state.json`.

`source_meta.json` follows that precedent: engine-internal, not a contract, indexed by
turn so it can be joined to `dialogue.json` at any time.

---

## 2. dialogue.json, the normalised form

Exactly the frozen contract. No additions.

```json
[
  { "pair": 1, "speaker": "user", "text": "...", "attachments": [], "ts": "2026-05-18T13:27:25Z" },
  { "pair": 1, "speaker": "ai",   "text": "...", "attachments": [], "ts": "2026-05-18T13:27:52Z" }
]
```

Rules:

- `pair` starts at 1 and increments by 1 with no gaps.
- Every pair has exactly two turns, `user` then `ai`, in that order.
- `speaker` is `user` or `ai`. Never `human`, `assistant`, `U`, `A`.
- `text` is the full message. No truncation, no cleanup of typos, no normalisation of
  case or whitespace beyond stripping leading and trailing blank lines.
- `attachments` is `[]` in T1, always. The field exists in the frozen schema and is
  where T2 will live. Do not populate it yet.
- `ts` is ISO 8601. If the source has no timezone, assume the exporter's local time and
  append `Z`, and set `assumed_utc: true` in the sidecar.

---

## 3. source_meta.json, the sidecar

```json
{
  "chat_id": "c01_coding_short",
  "source_kind": "claude_web_json",
  "source_file": "source.json",
  "exporter": "Claude Exporter (ai-chat-exporter.net)",
  "source_title": "3D interactive portfolio website setup continuation",
  "source_link": "https://claude.ai/chat/...",
  "imported_at": "2026-09-17T09:00:00Z",
  "import_spec_version": "1.0",
  "pairs": 4,
  "turns": 8,
  "assumed_utc": true,
  "fidelity": {
    "images_dropped": 22,
    "attachments_dropped": 0,
    "tool_narration_turns": 17,
    "injected_turns": 3,
    "merged_turns": 0,
    "dropped_trailing_user_turn": false
  },
  "turn_meta": [
    {
      "pair": 1,
      "speaker": "user",
      "origin": "typed",
      "flags": [],
      "dropped_media": []
    },
    {
      "pair": 1,
      "speaker": "ai",
      "origin": "model",
      "flags": ["tool_narration"],
      "dropped_media": ["Screenshot 2026-05-18 at 1.26.01 PM.png"]
    }
  ]
}
```

`turn_meta` is parallel to `dialogue.json` and in the same order. Index `i` in one
corresponds to index `i` in the other. This is the join.

---

## 4. `origin`, and the injected-text decision

Every turn carries an `origin`.

| origin | Meaning |
|---|---|
| `typed` | The person typed it |
| `injected` | Text that arrived in the user slot but was produced by tooling: slash-command expansions, loaded skill text, system notices, auto-continue strings, task notifications |
| `model` | The AI produced it |

**Owner decision, v1: `injected` turns are treated exactly as user input.** If it is
text in the user slot, the engine sees it as user text. No filtering.

The importer therefore **tags but does not strip**. Two consequences worth stating
plainly:

1. It matches the decision. Nothing is removed and the pipeline receives every word.
2. It stays reversible. If a later measurement shows injected text materially inflating
   user mass, flipping to exclusion is a config change plus a re-run of Stage 4, not a
   re-import of the corpus.

A single config flag governs it:

```
IMPORT_INJECTED_AS_USER=true      # v1 default, per owner decision
```

The flag is read at pipeline time, not import time. The corpus is neutral about it.

### Recognising injected text

Heuristics, applied in order, tagged not removed. Each match adds `injected` as the
origin and the matched rule name to `flags`.

| Rule | Pattern |
|---|---|
| `slash_command` | Turn wrapped in `<command-message>` / `<command-name>` |
| `task_notification` | Turn contains `<task-notification>` with a `<task-id>` |
| `skill_preamble` | Turn contains `Skill /<name> is already loaded` |
| `auto_continue` | Turn is exactly one of: `Continue from where you left off.`, `Try again`, `continue` with no other content |
| `system_note` | Turn begins with `<system-` or `[system]` |

These rules are T3-relevant and almost never fire on web exports. Implement them now so
they are ready, and so the counts appear in `fidelity` even when zero.

---

## 5. Per-format normalisation

### 5.1 `claude_web_json`

Detect: top-level object with `metadata` and `messages`, each message having
`role`, `time`, `say`.

```
role "human"     -> speaker "user"
role "assistant" -> speaker "ai"
say              -> text
time             -> ts
```

Verified property of this format: messages alternate perfectly, so pairing is
positional. **Do not rely on it.** Run the pairing rules in section 6 regardless.

Two quirks this format has, both recorded, neither altering `text` in v1:

- **Tool narration is flattened into the AI's prose.** Occurrences of a `Used tool`
  block followed by a `Done` line are inside `say`. Tag the turn with
  `tool_narration`, count it in `fidelity.tool_narration_turns`, leave the text intact.
- **Images are placeholders.** `[Image: <filename>]` appears in `say` where an image
  was. Record each filename in that turn's `dropped_media`, increment
  `fidelity.images_dropped`, leave the placeholder text in place.

### 5.2 `claude_web_md`

Detect: `## User:` and `## Assistant:` headers.

Supported only as a fallback when no JSON export exists. Parsing is fragile because a
fenced code block containing a `## ` line will split a message. If both formats exist,
JSON wins and the Markdown is kept as `source.md` for reading only.

### 5.3 `claude_code`

Detect: `.jsonl` where lines carry `type`, `sessionId`, `message`.

**Out of scope in v1. The importer must refuse it with a clear message**, not attempt a
partial import.

Recorded here so the refusal is principled rather than an omission. Measured on a real
session, 2,006 lines and 11.6 MB:

| Entry | Count |
|---|---|
| assistant entries | 951 |
| user entries | 598 |
| of which `tool_result` blocks | 576 |
| genuine non-tool user turns | 22 |
| of those, actually typed | ~16 to 18 |
| assistant entries containing any text | 166 |
| assistant entries that are pure tool calls | 785 |
| `thinking` blocks | 209 |
| `image` blocks | 26 |

A naive import would produce 598 "user" turns, of which 96% are machine output, and
would burn a very large API budget generating meaningless attribution. T3 needs its own
pairing model before any of this is safe.

Files that are application state, never corpus content: `metadata.json`,
`local-session-state.json`, and any duplicate of the transcript under the CLI session id.

---

## 6. Pairing rules

Applied to every format, after role mapping.

1. **Leading AI turn.** If the conversation starts with an AI message, drop it and
   record `dropped_leading_ai_turn: true`. A pair must begin with a user turn.
2. **Consecutive same-role turns.** Merge them into one turn, joining with a blank
   line, in source order. Increment `fidelity.merged_turns`. Record the original count
   in that turn's `flags` as `merged:<n>`.
3. **Trailing user turn with no reply.** Drop it and record
   `dropped_trailing_user_turn: true`. A pair needs both halves.
4. **Empty turns.** A turn whose text is empty after stripping is not dropped. It is
   kept as an empty string so the pair structure survives, and flagged `empty`.
   The engine must handle it. This is a deliberate edge case, not an error.
5. **Numbering.** After the above, number pairs 1..N in order.

---

## 7. Validation, at import time

The importer fails loudly. It never writes a partial corpus entry.

1. `dialogue.json` validates against `dialogue.schema.json` before writing.
2. Pair numbers are contiguous from 1 with no gaps.
3. Every pair has exactly one `user` turn followed by exactly one `ai` turn.
4. `turn_meta` length equals `dialogue.json` length.
5. `source.<ext>` is byte-identical to the input file.

If any check fails, write nothing and exit non-zero with the failing check named.

---

## 8. meta.yaml, written by the owner

The importer generates a skeleton with the machine-known fields filled and the
judgement fields left blank. The owner completes it.

```yaml
id: c01_coding_short
source_kind: claude_web_json      # filled by importer
pairs: 4                          # filled by importer
language: en                      # owner
task_type: coding                 # coding | writing | planning | research | creative | debugging
prompt_style: specified           # specified | vague | mixed
length_band: short                # short (<=5) | medium (6-20) | long (21+)
contains: [code_blocks]           # code_blocks | non_english | long_message | lists | images
expected:
  mode_hint: centaur              # centaur | copilot | autopilot
  direction_hint: user_heavy      # user_heavy | balanced | ai_heavy
  min_requirements: 2
  max_requirements: 20
notes: >
  One paragraph in the owner's words: what this conversation was, who drove it,
  and anything that makes it an unusual test case.
```

`expected` is deliberately soft. It is never asserted as an exact value. It is asserted
as a direction of travel: a chat marked `user_heavy` that comes back 90% AI is a signal
worth investigating, not a failed assertion.

---

## 9. Forward compatibility

Written now so T2 and T3 do not require re-importing the corpus.

**T2, attachments.** The `attachments` array already exists in the frozen
`dialogue.schema.json`, so no schema change is needed for the field to be present.
When T2 arrives, `dropped_media` in the sidecar becomes the input list for
re-processing: every corpus entry already records exactly which media were lost and on
which turn. Open questions T2 must answer, listed here so they are not rediscovered:
how an image becomes text the pipeline can reason about, whether an AI-produced
artifact is an action or an outcome, and whether a user uploading a reference document
is a SHAPER act or context supply.

**T3, agentic.** Needs a pairing model that answers: is a tool call an EXECUTOR action,
and does one human turn plus all subsequent tool traffic constitute one pair. Until
answered, the importer refuses the format rather than guessing.

**Version marker.** Every `source_meta.json` records `import_spec_version`. When this
spec changes, entries can be selectively re-imported by version.

---

## 10. Open questions raised by this spec

To be logged in SPEC_QUESTIONS.md on first implementation.

- **Q4** Provenance sidecar outside the frozen contract. Same pattern as Q3.
  Status: REVISIT if the command centre wants `origin` inside `dialogue.schema.json`.
- **Q5** Injected text counted as user input. Owner decision, v1.
  Status: RESOLVED, revisit after the first stability measurement.
- **Q6** Tool narration left inside AI text. Step 1a will extract actions from it.
  Status: OPEN, decide after E1 shows what it actually extracts.
