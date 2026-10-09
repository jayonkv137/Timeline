# C_TRACK_BRIEF.md — The Corpus Programme

A parallel workstream. Runs alongside the engine track E1 to E5 and never blocks it.

**Tool:** Antigravity, Sonnet. Mechanical, well specified, no correctness-critical
arithmetic. Gemini is fine for the bulk conversion steps.
**Depends on:** `docs/IMPORT_SPEC.md` v1.0 plus the v1.1 amendment.
**Blocks:** nothing in E1 or E2. Its output is needed before E3 stability measurement.

---

## 1. What this programme is for

The engine track proves the engine works. This track builds the thing it works *on*.

Right now the corpus is 36 hand-exported Claude chats, of which 10 are clean and 2 are
substantial. That is enough to get E1 moving and not enough for anything after it.

This programme turns a personal archive across three platforms into a **classified,
reproducible, reusable test asset** that survives every future change to the engine. Built
once, properly, it serves:

- E1 extraction quality, on a handful of clean chats
- E3 stability bands, which need variety or the bands mean nothing
- E3 and E4 robustness, which need the long and ugly conversations
- every future tier: T2 attachments needs image-heavy chats, T3 agentic needs Claude Code
  sessions, and both are already in the archive waiting
- the thesis, which needs an honest description of what real usage actually looks like

The governing principle: **the archive is complete and private, the corpus is small and
classified.** Never confuse the two.

---

## 2. Phases

Five, each closing with the same ritual as the engine track: DoD run for real, BUILDLOG
entry with pasted output, commit and tag, self-review pass.

### C0 — Export and archive

**Owner first.** Request all three exports. They arrive by email, Gemini can take hours,
and download links expire within 24 hours.

Then the agent:

- Implement `scripts/archive_scan.py` per the v1.1 amendment: the three converters, the
  canonical archive record, `data/archive/` layout, and `registry.json`.
- Add `data/archive/` to `.gitignore` before writing a single file into it.
- Deduplicate on `(platform, conv_id)`.
- Refuse Claude Code `.jsonl` with the T3 reason, as v1.0 already does.

**DoD:** every export converted, zero crashes, `registry.json` totals reconcile against
the per-conversation files, `data/archive/` is gitignored and confirmed absent from
`git status`.

---

### C1 — Triage and metrics

Compute every mechanical metric from the v1.1 amendment section F. No LLM calls in this
phase, none.

- `pairs`, `total_chars`, `max_turn_chars`, `images_per_pair`
- `regenerations` and the full `branches` block for ChatGPT
- `language`, `has_code`
- `fidelity_grade`
- `sensitive`, by the keyword list in section 5 below
- `context_incomplete` where a Claude conversation clearly depended on a Project

Then produce `docs/ARCHIVE_REPORT.md`, generated not written, containing:

- totals per platform: conversations, pairs, characters, date range
- the distribution of `pairs`, so the length bands can be set from reality rather than guessed
- the distribution of `images_per_pair`, and the grade split
- regeneration ratios across the ChatGPT set, which answers **Q9**
- the top 30 conversations by pairs, and the 30 cleanest with 6 or more pairs
- counts by language and by `has_code`
- how many are flagged `sensitive`

**DoD:** the report generates from the registry with one command and reconciles. Q9
answered with a real number.

This report is also a thesis artifact. It is the first honest picture anyone has of what a
year of real multi-platform AI use actually looks like.

---

### C2 — Assisted classification

Two layers, and the line between them is the important part.

**Layer 1, machine-assignable.** An LLM may classify these, one cheap call per
conversation on the first two user turns:

- `task_type`: coding, writing, planning, research, creative, debugging, admin, learning
- `language`
- `domain`: a free-text one-liner

**Layer 2, never machine-assigned.** These stay blank until a human fills them, and only
on the selected set:

- `prompt_style`: specified, vague, mixed
- `mode_hint`: centaur, copilot, autopilot
- `direction_hint`: user_heavy, balanced, ai_heavy

**The rule, and it is not negotiable:**

> **Never let an LLM pre-label anything the engine is supposed to measure.**

`mode_hint` and `direction_hint` are the engine's own outputs. If a model assigns them and
the engine is then checked against them, you are measuring agreement between two language
models, not accuracy. `task_type` and `language` are descriptive facts about the
conversation and are safe.

`prompt_style` sits closest to the line. A model could guess it, and it correlates
directly with the COTRACE finding about underspecified prompts that E3 is meant to
reproduce. Keep it human.

**DoD:** every archive record carries layer 1 fields. Layer 2 fields are present and empty
everywhere. A sample of 20 layer-1 classifications reviewed by the owner, with the
disagreement rate recorded.

---

### C3 — Selection and promotion

Stratified selection, not "take the best 30".

**Target quotas**, adjusted once C1 shows what actually exists:

| Dimension | Target |
|---|---|
| Length | 10 short (≤5 pairs), 12 medium (6 to 20), 8 long (21+) |
| Task type | at least 3 per type across the eight types |
| Platform | at least 8 from each of the three |
| Grade | at least 20 `clean`, no `unusable` in the extraction set |
| Language | at least 4 non-English |
| Prompt style | roughly balanced specified against vague |
| Sensitive | zero |

Where a cell cannot be filled, **record the gap rather than substituting**. An honest
"no clean long chats exist in this archive" is a finding. Quietly promoting a degraded one
to fill the quota is how a corpus lies.

Promotion writes `data/corpus/selection_manifest.json`:

```json
{
  "selected_at": "...",
  "import_spec_version": "1.1",
  "quota_gaps": ["no clean chat above 20 pairs exists in the archive"],
  "entries": [
    { "chat_id": "c01_coding_medium", "conv_id": "claude_9f8e7d",
      "platform": "claude", "grade": "clean", "provenance": "owner" }
  ]
}
```

**This manifest is the committed artifact.** It makes the corpus reproducible from the
archive without the conversations themselves ever entering the repository.

Then the owner completes layer 2 fields for the selected set only, and folders are renamed
to `c<NN>_<task_type>_<length>`.

**DoD:** selection manifest exists and reconciles, every promoted entry has four files and
validates, quota gaps recorded, layer 2 complete, zero `sensitive` entries promoted.

---

### C4 — Public datasets

Only after C3. Per `CORPUS_SOURCES.md`.

1. Check `github.com/rladmstn1714/CoTrace` for published logs first. It is the only source
   that lets you compare your numbers against the paper's on the same data.
2. 10 to 15 WildChat conversations, filtered for 6 or more turns.
3. 5 to 10 DevGPT conversations, filtered for multi-turn.
4. `scripts/fetch_public_corpus.py` plus a manifest of selected ids. **Commit the script
   and the manifest, never the data.**
5. Every entry tagged `provenance: public`. Every entry of the owner's tagged
   `provenance: owner`.

**Standing rule:** extraction quality is measured on both. The product demonstration and
the golden chat only ever use `owner`.

**DoD:** public entries pass the same validation as owner entries, through the same
importer, with no special path.

---

## 3. The classification schema, complete

One `meta.yaml` shape for every entry regardless of platform or provenance.

```yaml
# ---- machine, by the importer ----
id: c07_debugging_medium
conv_id: claude_9f8e7d
platform: claude
source_kind: claude_official
provenance: owner            # owner | public
pairs: 12
total_chars: 115879
max_turn_chars: 18910
images_per_pair: 0.25
regenerations: 0
fidelity_grade: degraded     # clean | degraded | unusable
has_code: true
context_incomplete: false
sensitive: false

# ---- machine, layer 1, LLM-assisted ----
language: en
task_type: debugging
domain: "front-end animation performance"

# ---- human, layer 2, never machine-assigned ----
prompt_style:                # specified | vague | mixed
expected:
  mode_hint:                 # centaur | copilot | autopilot
  direction_hint:            # user_heavy | balanced | ai_heavy
  min_requirements:
  max_requirements:
notes: >
  One paragraph in the owner's words.
```

---

## 4. Uses, now and later

So the value is visible rather than assumed.

| Need | Which slice |
|---|---|
| E1 extraction quality | `grade: clean`, 4 to 15 pairs, `provenance: owner` |
| E3 stability bands | 3 chats spanning specified and vague prompt styles |
| E3 cost and timing curves | the longest entries, grade irrelevant |
| E3 robustness | `max_turn_chars` outliers, empty turns, `unusable` entries |
| E4 batch equals live | any single short clean chat |
| Reproducing COTRACE's prompt-style finding | matched pairs of specified and vague chats |
| T2 attachments, later | the `unusable` set, already indexed by dropped media |
| T3 agentic, later | the Claude Code sessions, already refused and logged |
| Thesis, what real usage looks like | `ARCHIVE_REPORT.md` |

Nothing here is throwaway. The `unusable` chats are not waste; they are the T2 test set,
already measured and waiting.

---

## 5. Privacy, and it is not optional

The archive contains a year of your own conversations across three platforms. The
repository is currently public.

**Hard rules for this programme:**

1. `data/archive/` is gitignored before the first write. Verify with `git status`, not by
   assumption.
2. `registry.json` is committed with `title` redacted for any `sensitive` record.
3. If the repository stays public, `data/corpus/` is gitignored too and only
   `selection_manifest.json` is committed. The corpus stays reproducible without being
   published.
4. Nothing flagged `sensitive` is ever promoted, demonstrated, screenshotted or quoted.

**Keyword flag for `sensitive`**, deliberately over-inclusive, reviewed by the owner:
health, medical, symptom, doctor, therapy, visa, immigration, residence permit, embassy,
salary, rent, bank, debt, tax, legal, lawyer, contract termination, personal names of
family and friends.

Your existing 36 already contain a visa extension, a room search and a health question.
A full three-platform archive will contain considerably more.

---

## 6. Standing rules

1. The archive is never edited by hand. Fix the converter and re-run.
2. The corpus is generated from the archive by manifest. Never hand-assembled.
3. Every metric in the registry is mechanical. If a number needs judgement, it belongs in
   layer 2.
4. No LLM assigns `mode_hint`, `direction_hint` or `prompt_style`. Ever.
5. Reports are generated by scripts. Prose is prose.
6. Every format reaches the engine through the same importer and the same three files.
7. Quota gaps are recorded, never filled by substitution.

---

## 7. Kickoff prompt

Fresh session, paste verbatim:

```
Read AGENTS.md fully first — its workflow gates apply to this session (one step per
response, a preamble before each step, wait for my "start task" and "Finish Step").
Then read docs/IMPORT_SPEC.md v1.0 in full, docs/IMPORT_SPEC_v1.1_AMENDMENT.md in full,
and docs/briefs/C_TRACK_BRIEF.md in full.

You are working the C-track only: phases C0 through C3. This is a parallel workstream.
Do not touch engine/, web/, server/, tests/invariants.py, the five schemas, or
data/chats/fixture_pair1/. The engine track is running separately and must not be
disturbed.

Raw export zips are at <path>. data/archive/ must be added to .gitignore BEFORE you write
anything into it — verify with git status and paste the output.

Hard rules: the archive is never hand-edited. No LLM assigns mode_hint, direction_hint or
prompt_style. Reports are generated by scripts, not written from memory. Every format
reaches the corpus through the same importer and produces the same three files.

Begin with your preamble for C0.
```

---

## 8. Sequencing against the engine track

| Engine track | C-track |
|---|---|
| E1 extraction, current 36 chats | C0 export and archive, C1 triage |
| E2 Stage 4a | C2 classification, C3 selection |
| **E3 stability** | **needs C3 complete** |
| E4 live adapter | C4 public datasets |
| E5 projections | corpus frozen for the thesis |

The only hard dependency is C3 before E3. Everything before that is parallel and
independent.
