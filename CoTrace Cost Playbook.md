Contents

1. [Where the money goes](#where)
2. [Cheaper models, priced](#repriced)
3. [Every lever](#levers)
4. [Open source and local](#local)
5. [Free tiers and privacy](#privacy)
6. [How to choose](#bakeoff)
7. [Next for the nodes](#next)
8. [Sources](#sources)

Timeline repo · cost research · 8 October 2026

# How to make CoTrace 50–100× cheaper to run

Your engine already talks to models through a standard OpenAI-style connection, so changing the model or its settings is configuration, not a rebuild. Below, every option is priced on the tokens your 10 processed chats actually used, not on generic benchmarks.

## Short answer

1. **Most of today's bill is the model thinking, not your task.** 59% of the cost is hidden reasoning that nobody reads. The engine never sets a thinking level, so Gemini 3.5 Flash uses its default. Setting it to minimal is a one-line change, and on its own takes a pair from about $0.28 to about $0.13.
2. **You're mostly right that this is a simple task.** Steps 1a, 1c and 2 are extraction: find the actions, list the requirements, copy quotes. Step 3, influence scoring, is real judgment and drives your percentages. Small models will probably do fine on the first group. Step 3 has to be tested before you trust a cheap model with it.
3. **The cheapest serious models cost $0.002–0.007 per pair** for the full pipeline on your token counts. That's 40–100× less than today. DeepSeek V4-Flash, gpt-oss-120b, GPT-5 nano and Qwen3.5 9B all work through the same connection your engine already uses.
4. **Then stack the structural savings.** The node graph needs only 3 of the 6 steps (about 3× cheaper). Anything that isn't live can use batch pricing (2×). Prompt caching and shorter outputs add more.
5. **Picking models needs a bake-off, and it costs under $5.** Run all 10 processed chats through each candidate, score them automatically against today's outputs, and choose a model per step.

## Where the money goes today

Totals across all 283 calls on the 10 processed chats (28 message pairs): **$7.93**, or $0.28 per pair.

Thinking 59% · $4.65Output 31% · $2.48In 10%

On an average pair the engine reads about 21,000 tokens and writes about 10,600 visible tokens. Hidden thinking adds about 2,000–2,800 tokens per call on Steps 1b, 1c, 2 and 3. That's why thinking alone costs more than everything else combined.

This changes which savings matter. Prompt caching only touches the 10% of input. Turning down thinking and choosing a cheaper model act on the other 90%.

## Cheaper models, priced on your real tokens

I took every real call's input and output token counts and applied each model's price. "Graph only" means the three steps the node graph needs: 1a actions, 1b outcome tree, 2 requirements and open questions.

| Model and setting | Full pipeline / pair | Graph only / pair | Full, batch | Notes |
| --- | --- | --- | --- | --- |
| Today: Gemini 3.5 Flash, default thinking | $0.2831 | $0.0933 | $0.1416 | Baseline |
| Gemini 3.5 Flash, thinking set to minimal | $0.1272 | $0.0397 | $0.0636 | Same model, so quality risk is lowest. "Minimal" doesn't guarantee zero thinking |
| Gemini 3.5 Flash-Lite | $0.0329 | $0.0099 | $0.0164 | Same provider and key |
| Gemini 3.1 Flash-Lite (already your Step 1a model) | $0.0212 | $0.0066 | $0.0106 | Zero setup |
| GPT-5 nano, minimal reasoning | $0.0066 | $0.0019 | $0.0033 | Reasoning model; assumed +30% hidden tokens |
| Qwen3.5 9B, hosted | $0.0062 | $0.0024 | — | Open weights, also runs on your Mac |
| DeepSeek V4-Flash, non-thinking | $0.0059 | $0.0022 | $0.0030 | Very cheap cached input. Official API is hosted in China |
| gpt-oss-120b on DeepInfra, low reasoning | $0.0024 | $0.0008 | — | Open weights; assumed +50% hidden tokens |
| Local model on your Mac (Ollama) | $0 | $0 | — | Slow: see the local section |

These are estimates. They assume each model writes about as many tokens as Gemini did, and different models are more or less wordy. Prices come from third-party trackers (August–October 2026) and move often. The bake-off below replaces these numbers with measured ones.

### What that means per user

| Monthly use | Today | Flash, minimal thinking | Flash-Lite 3.1 | DeepSeek / nano / Qwen | gpt-oss-120b |
| --- | --- | --- | --- | --- | --- |
| 100 pairs | $28 | $13 | $2.10 | $0.60 | $0.24 |
| 400 pairs | $113 | $51 | $8.50 | $2.50 | $0.96 |
| 1,200 pairs | $340 | $153 | $25 | $7.50 | $2.90 |

Full pipeline on every pair. Mapping only the graph, and auditing only some chats, divides these again by about 3.

## Every lever, ranked by savings per hour of work

Your AGENTS.md treats prompt wording as law, so the last column matters. "Config" levers you can pull at will. "Spec" levers change what the prompts ask for and go through the command center first.

| Lever | Saving | Effort | Type | Risk |
| --- | --- | --- | --- | --- |
| **Set the thinking level per step** (`reasoning_effort` in `engine/llm.py`) | \~55% now | 1 hour | Config | Quality drop on 1b and 3; re-grade |
| **Cheaper model per step**. Model names are already config; add a provider address per step | 4–50× | Half a day | Config | Measure with the bake-off |
| **Never pay twice in development.** Your `llm_cache.py` already records and replays calls; keep it on for every experiment | 100% on re-runs | Exists | Config | None |
| **Run only what the graph needs live**: 1a, 1b, 2. Run 1c and 3 only when auditing | \~3× | 1 day | Config | No percentages until the audit runs |
| **Skip pairs that aren't worth it**: chats under 3 pairs, "thanks" or "ok" turns | 20–40% for typical users (estimate) | Half a day | Spec-adjacent | Missing a real decision in a short turn |
| **Batch or Flex pricing** for audits, backfill and corpus runs | 2× | 1 day | Config | Results within hours, not seconds |
| **JSON schema outputs** instead of free text plus `json_repair` | Fewer retries; slightly shorter output | 1 day | Config | Some providers support schemas only partly |
| **Prompt caching**: instructions already come before the chat text, so the shared start of each prompt can be cached | Up to \~70% of input; matters more on cheap models where input is half the bill | Mostly automatic | Config | None |
| **Bigger Step 3 batches** (`STEP3_BATCH_SIZE` is 3) | Fewer calls, less repeated context | Minutes | Config | Long batches can lower label quality |
| **Shorter outputs**: Step 3 writes a sentence of explanation for every action, including "no connection" ones. Its average visible output is 1,831 tokens | \~40–50% of output (estimate) | 1–2 days | Spec | Explanations may feed the timeline drawer |
| **Embedding pre-filter for Step 3** (spec §9.5, already designed) | Smaller Section A prompts | 2 days | Spec | Recipe not yet tested on your data |
| **Train your own small model** on the expensive model's outputs (distillation) | Near zero per call | 1–2 weeks | Later | Needs hundreds of processed chats first |

## Open source and local models

### On your Mac

Your M3 Pro has 18 GB of memory. A 4B model or Qwen3.5 9B (about 10 GB at 4-bit) fits through Ollama with JSON-schema output. gpt-oss-20b (about 13 GB) is tight.

Speed

\~20–25 tok/s for 9B (estimate)

Graph only

\~2–3 min per pair

Full pipeline

\~8–10 min per pair

Too slow for a live side panel. Good for free overnight runs over your own 55-chat corpus and for a private mode where nothing leaves the machine.

### Hosted open weights

gpt-oss-120b, Qwen and DeepSeek weights are served by DeepInfra, Groq, Together and Cerebras at the prices above, through the same OpenAI-style connection.

- Cheapest per token of any option
- You choose a US or EU host, which matters for other people's chats
- No lock-in: the same weights can move to another host or to your own server

Later, for extension users, Chrome's built-in Gemini Nano runs on the user's own computer for free. It's small, needs 16 GB of RAM, and only suits the simplest step (1a), so treat it as an option to test, not a plan.

## Free tiers and privacy

- **Gemini's free tier** is fine for testing on your own chats, but Google may use free-tier content to improve its products. Never send other people's chats through it. The paid tier excludes this.
- **DeepSeek's own API** is processed in China. For a public product, use DeepSeek's open weights through a US or EU host.
- **Batch pricing** is paid-tier only on Gemini, so the batch discount and the privacy protection come together.
- **For your own corpus** (Takeout and Claude exports are in `data/`), check that nothing in it is too personal to send to a free tier. A local model avoids the question entirely.

## How to choose: a bake-off on your own chats

Nothing here changes a prompt, so it stays inside your rules. Today's Gemini 3.5 Flash outputs are the reference. They aren't ground truth, but they passed your invariants and golden grading.

1. **Add the seam.** In `engine/config.py` and `llm.py`, give each step its own model, provider address, key and thinking level, plus optional JSON-schema output. Defaults reproduce today exactly.½ day
2. **Pick candidates.** 3.5 Flash minimal, 3.1 Flash-Lite, GPT-5 nano, DeepSeek V4-Flash (open-weights host), gpt-oss-120b, Qwen3.5 9B local.—
3. **Run the 10 chats (28 pairs)** through each candidate, cache on, recording cost, seconds and retries per step.\<$5 total
4. **Score automatically** against the reference using the metrics below, then read the disagreements yourself for the top two.1 day
5. **Choose per step.** A likely result is a cheap model for 1a, 1c and 2, and a stronger one only where Step 3 needs it.—

| Check | Why it matters | Suggested pass bar |
| --- | --- | --- |
| Valid JSON, no retries | Retries cost money and time | ≥ 99% first try |
| Invariants 1–16, 19, 21 | Inv 21 catches models that paraphrase instead of quoting verbatim, a common small-model failure | All pass |
| Outcome nodes match | The graph's skeleton | Same count ± 1, matched titles |
| Requirement creator (you or AI) | Bead color | ≥ 90% agreement |
| Open questions opened, resolved, abandoned | Rings and bullseyes | ≥ 85% of events match |
| Step 3 relationship labels and scores | Node mass and direction | ≥ 80% labels, score within ±1 |
| Final numbers | What the user reads | Direction within ±5 points; same mode in ≥ 8 of 10 chats |

The pass bars are my proposals. They're your call, and AGENTS.md rule 5 still applies: the frozen fixture numbers stay exact.

## What to do next with the node design

The backend has already processed 10 chats, and each one has `state.json`, `ledger.jsonl` and `full_export.json` on disk. The graph can run on real data now without any model calls.

| Order | Step | Cost | Done when |
| --- | --- | --- | --- |
| 1 | **Graph projection.** Move the mass, dormancy, birth and focus math out of `compile_all_chats.js` into a tested Python projection (beside `projections/panel.py`) that writes a `graph_bundle.json` per chat. Point the Obsidian and 3D views at it. Commit `design_pack/`. | $0 | c05 shows total mass 62, 237, 412, 625, 919, 1049, 1137 for pairs 1–7, matching the GRAPH_SYSTEM_SPEC audit, in tier-1 tests and on screen |
| 2 | **Run the pipeline step at the end automatically**, so every new chat produces a graph without the manual compile. | $0 | One command takes an export to a graph |
| 3 | **Cost seam and bake-off** (above). | \<$5 | A model chosen per step, with measured cost per pair |
| 4 | **Map the rest of the corpus** (c01–c55) with the winning setup, on batch or locally overnight. This is the real test of the graph on long and wandering chats, and of open question Q7. | \~$1–5 total | 45 more chats render without breaking the layout |
| 5 | **Live on your own sessions**: Claude Code and Codex transcripts feed the graph as you work (N2 in the feasibility report). | \~$1–5 per month | You use it for a week |

## Sources

- [Gemini OpenAI compatibility (reasoning_effort)](https://ai.google.dev/gemini-api/docs/openai); [Gemini 3.5 Flash thinking levels](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.5)
- [Gemini Batch Mode, 50% off](https://developers.googleblog.com/en/scale-your-ai-workloads-batch-mode-gemini-api/); [Gemini pricing and free-tier data use](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 3.5 Flash price](https://pricepertoken.com/pricing-page/model/google-gemini-3.5-flash), [3.5 Flash-Lite price](https://anotherwrapper.com/llm-pricing/gemini-3.5-flash-lite)
- [DeepSeek V4 pricing](https://www.morphllm.com/deepseek-api); [2026 price comparison](https://www.spheron.network/blog/llm-api-pricing-comparison-gpt-claude-gemini-deepseek-2026/)
- [LLM pricing table, October 2026](https://benchlm.ai/llm-pricing) (GPT-5 nano, Qwen3.5 9B); [OpenAI Batch and Flex](https://curlscape.com/blog/openai-api-pricing-guide-2026)
- [gpt-oss-120b provider prices](https://pricepertoken.com/pricing-page/model/openai-gpt-oss-120b); [Groq gpt-oss-120b](https://trevorfox.com/tools/calculators/llm-cost/groq/gpt-oss-120b/)
- [Qwen3.5 9B memory and speed estimates](https://willitrunai.com/can-run/qwen-3.5-9b-on-m1-pro-16gb); [small models for JSON extraction](https://bestllmfor.com/best/structured-data-extraction-json/)
- [Chrome built-in AI](https://developer.chrome.com/docs/ai/built-in)

Token counts and costs come from `data/chats/*/run/llm_monitor.txt` (283 calls, 28 pairs) at commit `bb7ab0a`. Other-model costs are those token counts at third-party list prices. Local speeds are estimates.