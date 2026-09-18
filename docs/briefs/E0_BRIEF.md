# E0_BRIEF.md — Corpus, Importer, Harness

**Phase:** E0, the first phase of the engine-first rebuild
**Tool:** Antigravity, Sonnet. Gemini acceptable for the mechanical steps.
**Gate before E1:** see Definition of Done at the bottom. All of it, run for real.

---

## Why this phase exists

The engine's remaining work cannot be tested without real data, and real data cannot be
trusted without an importer that says exactly what it kept and what it lost. E0 builds
the ground the rest of the rebuild stands on.

Nothing in this phase produces a number. That is expected. This phase feels
unproductive and is the reason the rest goes fast.

---

## Read before starting

- `AGENTS.md` in full. Its workflow gates apply to every step of this session.
- `docs/IMPORT_SPEC.md` in full. This phase implements it.
- `docs/TEST_STRATEGY.md` sections 1, 2 and 3.
- The last two entries of `BUILDLOG.md`.

Do not read the four main specs for this phase. They are not needed and reading them
wastes context.

---

## Scope

**In scope**
- The importer and the corpus it produces
- The invariant module
- The LLM caching and replay client
- Test markers and harness plumbing

**Out of scope, do not touch**
- `engine/pipeline.py`, `prompts.py`, `state.py`, `artifacts.py`, `config.py`
- Anything under `web/`
- The five frozen schemas
- `data/chats/fixture_pair1/`, which is frozen forever
- Steps 2 and 3, Stage 4, the server. Those are E1 onward.

If a step appears to require touching an out-of-scope file, stop and log it in
`SPEC_QUESTIONS.md` rather than proceeding.

---

## Steps

### S1 — Scaffold and markers

Create `data/corpus/` and `tests/cassettes/`, both with a `.gitkeep`.

Update `pytest.ini` to register the four markers and to exclude `tier2` and `tier3` by
default, exactly as in TEST_STRATEGY section 1.

Add to `requirements-dev.txt`: nothing new is strictly required. `jsonschema` is
already there. Do not add libraries.

**Verify:** `pytest` still runs green on the existing 22 tests. `pytest -m tier1`
returns "no tests ran" rather than an error.

**Commit:** `E0.S1: test markers + corpus scaffold — harness plumbing before data`

---

### S2 — The importer

Implement `scripts/ingest_export.py` per `IMPORT_SPEC.md` v1.0.

A reference implementation is supplied with this brief. Use it as the starting point.
Read IMPORT_SPEC first and check the implementation against it rather than trusting it;
where they disagree, the spec wins and you log the difference.

It must:
- detect `claude_web_json`, `claude_web_md`, `claude_code`, `unknown`
- refuse `claude_code` and `unknown` with a clear message and exit code 2
- apply the four pairing rules in IMPORT_SPEC section 6
- tag origin as `typed`, `injected` or `model`, never strip
- record dropped media and tool narration per turn
- run the five validation checks in section 7 and write nothing if any fails
- emit `dialogue.json`, `source_meta.json`, `meta.yaml` skeleton and a copy of the source
- support `--batch`, `--dry-run` and `--force`

**Verify:** run it on the exports in the testing folder with `--dry-run` first, then for
real. Every entry must pass validation.

**Commit:** `E0.S2: chat importer per IMPORT_SPEC v1 — normalise exports to corpus entries`

---

### S3 — Importer tests, tier 1

`tests/test_import.py`, all marked `tier1`.

Cover at minimum:
- role mapping, `human`/`assistant` to `user`/`ai`
- pairing rule 1, a conversation starting with an AI turn
- pairing rule 2, two consecutive user turns merged, `merged:2` flag present
- pairing rule 3, a trailing user turn with no reply dropped
- pairing rule 4, an empty turn kept and flagged `empty`, pair structure intact
- injected detection for all five rules in IMPORT_SPEC section 4, each tagged and each
  still present in `dialogue.json` with its text intact
- `[Image: x]` recorded in `dropped_media` and counted in fidelity, placeholder text
  left in place
- a `claude_code` file refused with exit code 2
- a malformed JSON file refused, nothing written
- re-import without `--force` refused
- timestamp parsing, including a source with no timezone setting `assumed_utc: true`

Build tiny synthetic fixtures under `tests/data/import/`. Do not use real corpus chats
for these, they are too large and too slow.

**Verify:** `pytest -m tier1 tests/test_import.py` green.

**Commit:** `E0.S3: importer test suite — pairing, origin tagging, fidelity, refusals`

---

### S4 — Ingest the corpus

Run the importer over every export in the testing folder.

Print the fidelity summary for each. Then produce `data/corpus/manifest.json`:

```json
{
  "import_spec_version": "1.0",
  "generated_at": "...",
  "chats": [
    { "id": "c01_unsorted", "source_kind": "claude_web_json", "pairs": 3,
      "images_dropped": 1, "injected_turns": 0, "tool_narration_turns": 1 }
  ]
}
```

Leave folder names as `cNN_unsorted`. The owner renames them after filling `meta.yaml`,
because the name encodes a judgement the importer cannot make.

**Verify:** every chat validates. The manifest totals match the sum of the individual
`source_meta.json` files.

**Commit:** `E0.S4: ingest corpus + manifest — N chats normalised`

**Then STOP for owner review.** This is the review-the-scaffold rule. The owner fills in
`meta.yaml` for each chat and renames the folders before S5 begins.

---

### S5 — The invariant module

`tests/invariants.py`. One function per invariant from TEST_STRATEGY section 2,
numbered `inv_01` through `inv_21`.

Each function takes the artifacts it needs and returns a list of violation strings,
empty when it passes. It never raises and never asserts, so the same function can be
used both by tests and by production code in E1.

```python
def inv_14_shaper_subset(analysis: dict) -> list[str]:
    """h_you <= delta_you and h_ai <= delta_ai for every pair."""
    ...
```

Invariants 10 to 21 reference artifacts that do not exist yet. Write them anyway, with
a guard that returns `["skipped: analysis.json absent"]` rather than failing. E1 and E2
turn them on by producing the data.

Add `tests/test_invariants.py`, marked `tier1`, which runs every implemented invariant
against `data/chats/fixture_pair1/`. Invariants 1 to 9 must pass on it today.

**Verify:** `pytest -m tier1` green. The fixture passes every applicable invariant.

**Commit:** `E0.S5: invariant module — 21 checks, fixture passes all applicable`

---

### S6 — The caching LLM client

`engine/llm_cache.py`, wrapping the existing `LLMClient` without modifying it.

Three modes, from `LLM_CACHE_MODE`:

| Mode | Behaviour |
|---|---|
| `off` | Pass through to the real client. Default. |
| `record` | Call the real API, write every prompt and response to `tests/cassettes/` |
| `replay` | Never touch the network. Serve from cassette. Miss is a hard error. |

Cache key: a hash of model name plus the exact prompt text. Cassette files are JSON,
one per key, committed to git.

Do not modify `engine/llm.py`. Wrap it.

**Verify:** a tiny script records one call then replays it with the network unavailable
and gets the identical response.

**Commit:** `E0.S6: record/replay LLM client — deterministic tier0 tests`

---

### S7 — SPEC_QUESTIONS entries

Append Q4, Q5 and Q6 exactly as written in `AGENTS_PATCH.md`.

**Commit:** `E0.S7: log Q4-Q6 — sidecar, injected text, tool narration`

---

### S8 — Phase close

Run the full close ritual from Build Playbook section 3:

1. Run the Definition of Done below for real. Paste the output into the BUILDLOG entry.
2. Append the BUILDLOG entry using its template.
3. Commit, then tag `e0-done`.
4. Update the `Current phase` line in `AGENTS.md` to E1 and its DoD.
5. Self-review pass: "Re-read this brief top to bottom. List anything specified that
   was not delivered, or delivered differently. If the list is non-empty, we are not
   done." Only an empty list closes the phase.

---

## Definition of Done

All of these, verified by running them, not by reading the code:

- [ ] `pytest` green, including the pre-existing 22 tests
- [ ] `pytest -m tier1` green, importer and invariant suites included
- [ ] Every export in the testing folder is either a valid corpus entry or was refused
      with a stated reason
- [ ] Every corpus entry has all four files, and `dialogue.json` validates against
      `dialogue.schema.json`
- [ ] `data/corpus/manifest.json` exists and its totals reconcile
- [ ] The owner has filled `meta.yaml` for every entry and renamed the folders
- [ ] `tests/invariants.py` implements all 21, and 1 to 9 pass on `fixture_pair1`
- [ ] Record and replay demonstrated working
- [ ] Q4, Q5, Q6 logged
- [ ] `data/chats/fixture_pair1/` is byte-identical to its state at the start of the
      phase. Verify with `git status` showing it untouched.

---

## Kickoff addendum

Append this to the universal kickoff prompt for this session:

> Data locations: raw exports are in the testing folder inside the project.
> Corpus output goes to `data/corpus/`. The frozen fixture at
> `data/chats/fixture_pair1/` is read-only for this entire phase, including its
> `dialogue.json`.
>
> Hard rules for E0: do not modify any file under `engine/` except by adding
> `engine/llm_cache.py`. Do not modify the five schemas. Do not modify anything under
> `web/`. Do not implement Steps 2, 3 or Stage 4 in this phase, even if it looks easy.
> Corpus entries are never hand-edited: if one is wrong, fix the importer and re-import
> with `--force`.
