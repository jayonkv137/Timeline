# BRAIN_REGIONS_SPEC: where each chat lives, what it sits next to, and how chats connect

Status: **v0.1, proposed (track B1).** Research done; the empirical study ran on the 55 labelled corpus chats (zero LLM, zero spend). Rules are proposed for owner decision. The engine module and the Brain Lab preview follow the plan in §12.
Companions:
- [`BRAIN_NEURON_SPEC.md`](BRAIN_NEURON_SPEC.md) (what a neuron looks like). This spec decides *where* it sits and *what it connects to*; it closes that spec's Sessions 11–13.
- [`BRAIN_SYSTEM_SPEC.md`](BRAIN_SYSTEM_SPEC.md) §3 (territory claiming, kept).

## Owner's words

> "my research, coding, creative, writing, planning, learning … we need to figure out a system … a research-based system … how we can empirically, with the data we have, map this"
> "what data will we take? What is the proper, empirical, exact data … final summary … dialogue summary … maybe that can be used to connect … between the chats and the neurons and the connections"
> "all of my chats related to film-making will be in one area and coding will be another area … see the bigger chats and how they connect to other chats … which areas are AI-dominated or human-dominated … a mapping of a person's entire brain" (earlier session)

---

## 1. The idea in one paragraph

The real brain stores meaning **by place**. Huth et al. (Nature 2016) showed that semantic domains tile the cortex as a continuous map, shared across people: related concepts sit next to each other. COTRACE's brain does the same with chats. **A chat's position is what it is about.** Chats about the same thing form a **region** (for example "AI film-making", "German learning", "life in Bremen"). Regions are found in the chats' own text, named from their own words, and confirmed or renamed by you. Neighbouring regions are related. **Connections (axons) between chats are drawn only from evidence:**
- the same conversation continued
- text reused between chats
- strong mutual similarity

Each connection carries its evidence.

---

## 2. Two different questions, kept apart (the main finding)

| Question | Example values | Where it shows |
|---|---|---|
| **What is the chat about?** (topic, project, domain) | AI film-making · German learning · life in Bremen · the Timeline project | **Position and region** (data-driven) |
| **What kind of work is it?** (task type) | research · coding · creative · writing · planning · learning | **A property, not a place:** filter, legend, and optionally the neuron's texture (Session 5) |

**Why they must be separate (study §9):**
- **Your task-type labels are not what the content groups by.** The best text fingerprint puts a chat next to a same-label chat only **49%** of the time (chance **19%**); agreement with the labels is weak (NMI 0.33).
- **The content groups by topic, and topics cut across task types:**
  - German learning = 3 "learning" + 2 "planning"
  - Life in Bremen = 1 "writing" + 3–4 "planning"
  - AI film-making = 11 "creative" + 1 "planning" + 1 "writing"
- **The same conversation exported twice carries two different labels:** c06 "planning" and c55 "creative" (similarity 0.98).

**Consequence:** the six fixed topic lobes (`Brain.tsx` `LOBES`, provisional since DDR-007) are retired as a placement rule. The six categories survive as **task type** (S4.7's picker, renamed). They never move a chat.

---

## 3. The data we take from each chat (empirical, in order of availability)

| Tier | When | Fields | Cost |
|---|---|---|---|
| **0, at import** | before any processing | title · every message (yours and the AI's) · timestamps · platform conversation id · attachment names | none |
| **1, after mapping** | when the engine has processed the chat | root goal · outcome titles · requirement and question texts · dialogue summary · mass and share | already paid by processing |
| **2, owner** | any time | region rename, merge or split · manual links ("these belong together") · task type | none |

**The fingerprint** (the text a chat is compared by):
- **At Tier 0:** **title + the full dialogue (F4).** In the study this recovered relations best (NMI 0.33, nearest-neighbour 49%); title-only and title + first message were weaker.
- **After Tier 1:** the engine's own extraction (root goal, outcomes, requirements, summary) is appended. On the 13 processed chats it matched or beat the full dialogue (purity 0.69 vs 0.62).
- **Rule:** all fields are used, every field comes from the data (nothing typed by a model as an opinion), and the fingerprint is hashed so a chat is re-compared only when its text changes.
- **The dialogue summary helps but is not required:** it exists only for processed chats, and regions must work from the moment of import.

**Privacy:** fingerprints are computed locally. Only the embedding step (§4) sends text out, to the provider you configured, under the same consent and cost gate as processing.

---

## 4. Similarity (how alike two chats are)

| Layer | Method | Role |
|---|---|---|
| **Baseline (zero cost, always on)** | TF-IDF on the fingerprint: sublinear term frequency, smoothed IDF, stop words + generic conversation words removed ("step", "thing", "right", "page"…), light stemming; cosine similarity | Works offline and at import, and produces the region keywords (§5.3) |
| **Production (gated)** | Embeddings of the fingerprint through one swappable `MODEL_EMBED` seam (the same OpenAI-compatible client as the pipeline); long chats are chunked and averaged; cached by fingerprint hash, so each chat is embedded once | Meaning-level similarity. It catches what word-matching misses |

**Why both (study §9.3):** word-matching over-fragments. With the baseline, 18 of 55 chats stay alone although they obviously belong somewhere:
- "Hybrid AI filmmaking", the honey product video and the jellyfish animation → AI film-making
- the Anki flashcards chat → German learning
- the visa-extension chat → life in Bremen

German-language chats also share few words with English ones on the same topic. Embeddings fix both; this is the Obsidian *Smart Connections* lesson (related notes found by embedding similarity, not by shared words).

**Acceptance test before embeddings replace the baseline for placement** (run on the corpus, tier2, cost shown first):
1. Fewer solitary chats than the baseline (18 → ≤ 8).
2. The six known pairs above join their regions.
3. Near-duplicate pairs stay at the top (≥ 0.9).
4. Total cost is shown before running; for the whole archive it is expected to be well under $1 at published embedding prices, confirmed at the gate.

---

## 5. Regions (clustering)

### 5.1 Two levels, like an atlas (Clio and Nomic Atlas both use a hierarchy)
- **Areas:** broad, about 4–10 (e.g. "making things with AI images and video", "building software", "life admin in Germany").
- **Regions:** project-level, inside an area (e.g. "Kerala family film", "Nike ad", "portfolio site", "Timeline project").

The overview shows areas; zooming in shows regions (§8).

### 5.2 Method (deterministic, data-calibrated)
1. **Near-duplicates first:** pairs with similarity ≥ 0.90 are the same conversation exported or continued twice. They are linked as **continued** (§7) and always share a region.
2. **Average-linkage agglomerative clustering** on cosine similarity. It needs no fixed number of clusters, is deterministic, and handles odd shapes better than k-means at this size.
3. **Cut heights are calibrated from the data, not hard-coded:** the region cut sits at the corpus's **90th-percentile** pair similarity, the area cut at the **80th**. On the 57 corpus chats with the full fingerprint (dialogue + engine text), those are 0.132 and 0.103. They give about 8 project-level regions and 4 broad areas (study §9.5). Libraries under 12 chats use those measured values directly.
4. **Minimum region size 2.** A chat that joins nothing stays a **solitary neuron.** It is never forced into a region; Clio and BERTopic both keep an outlier class.

### 5.3 Names
- **Proposed name = the region's most distinctive words** (class-based TF-IDF, as in BERTopic): zero cost, fully traceable ("image, shot, character, reference, prompt, style").
- **Optional:** a model writes a short human title from those words and member titles (one cheap call per region, cost-gated), as Clio does.
- **You can rename, merge or split; your name always wins.** Every name records its source (`keywords`, `model`, `owner`). Proposals are never auto-accepted.

### 5.4 Stability (the map must not reshuffle under you)
Mental-map research (Coleman & Parker; Misue et al.) says existing items should move as little as possible when the graph changes. So:
- **A new chat joins** the most similar region if its similarity to the region is at least the region cut; otherwise it becomes a solitary neuron near its nearest neighbour. Existing chats never move.
- **A full re-map** (new clustering and layout) is a **versioned event:**
  - you see a preview of what moves, as an old vs new map
  - you approve it
  - the previous map is archived (the "destructive actions archive and preview" rule)

---

## 6. Placement on the cortex (layout)

1. **Flat map first, as neuroscience atlases do.** HCP and other cortical atlases are shown on flattened hemispheres. The layout is computed on a **flat cortex map**: two discs, left and right hemisphere, side by side. It is then wrapped onto the folded surface.
2. **Areas are laid out on the flat map** with a deterministic, seeded force layout. Attraction = area-to-area similarity; repulsion keeps areas apart. Each area's footprint grows with the total mass of its chats.
3. **Regions are placed inside their area the same way; chats inside their region.** Each chat gets a seed direction near its region centre. Territory claiming (BRAIN_SYSTEM_SPEC §3: moat, first-seen order, cells by mass) then packs the neurons without overlap.
4. **Hemispheres carry no meaning.** Left and right are where the layout put things, not a "left-brain/right-brain" claim. A meaning (e.g. human-led vs AI-led) could be given later only by your decision.
5. **Pinned once placed** (§5.4).

---

## 7. Connections (axons): evidence only

| Type | Evidence (all from the data) | Strength | Look (BRAIN_NEURON_SPEC Session 12) |
|---|---|---|---|
| **continued** | Near-duplicate text (≥ 0.90), or the same title with a continuation marker ("continuation", "part 2", "phase 2"), or consecutive time with similarity ≥ the region cut | strongest | thick, solid, with signal |
| **reused** | Shared verbatim passages: 8-word shingles, Jaccard over shingle sets ≥ 0.02 and ≥ 3 shared shingles (the Stanford IR near-duplicate method); shared attachment file names | strong | solid |
| **similar** | **Mutual** top-3 neighbours **and** similarity ≥ the corpus's 99th-percentile pair similarity (F3 study value 0.27) | weak | thin, dashed |
| **yours** (future) | You linked them by hand (the Obsidian lesson: explicit links are the strongest signal because you made them) | owner | solid, white |

**Rules:**
- **No link without its evidence record:** the type, the score, and the shared keywords or shared passages or timestamps. The evidence is shown when you hover or click the axon.
- **At most 3 axons per neuron at the overview** (strongest first), so the brain never becomes a hairball. All of them show when the neuron is open.
- **Axons dive inside the brain** (white matter), as in BRAIN_NEURON_SPEC §6 placement B.
- **Link prediction from shared neighbours** (Adamic-Adar, as in Obsidian's Graph Analysis plugin) is reserved for when there are enough links to make it meaningful.

---

## 8. Text and zoom (map-label hierarchy, with BRAIN_NEURON_SPEC Session 9)

| Zoom | Shows |
|---|---|
| Far | **Area names** (owner name, else the keyword name) |
| Middle | Region names; chat titles of the biggest chats by mass, never overlapping |
| Near | All chat titles in view |
| Any | Hover or selection shows the title |

Obsidian fades labels by zoom only; its users asked for size-aware fading "like a map where only large regions are labelled when zoomed out". This rule does that.

---

## 9. Empirical study (9–12 Oct 2026, scripts in the session scratchpad; reproducible from `data/corpus`)

### 9.1 Which fingerprint recovers relations? (55 labelled chats, owner task types; chance = 0.185)

| Fingerprint | Nearest neighbour has the same label | Same label in top 3 | Cluster purity | NMI |
|---|---|---|---|---|
| F1 title only | 0.47 | 0.35 | 0.38 | 0.19 |
| F2 title + first message | 0.42 | 0.38 | 0.40 | 0.28 |
| F3 all of your messages | 0.49 | 0.42 | 0.44 | 0.31 |
| **F4 full dialogue** | **0.49** | **0.46** | **0.46** | **0.33** |
| F5 engine extraction (13 processed chats only) | 0.46 | 0.26 | 0.69 | 0.64 |

Reading:
- Content agrees with the task-type labels only weakly. The reason shows in §9.2: the content is organised by topic, which cuts across task types.
- F4 is the best fingerprint available at import.

### 9.2 Regions the content forms by itself (baseline, generic words removed, region cut 0.12)

| Region (keyword name) | Chats | Task types inside |
|---|---|---|
| image · shot · character · reference · prompt · style (**AI film and image**) | 9: Kerala wedding photo, centennial video biography, Kerala family shots, Midjourney hallway, Adobe clips for AI film, hybrid art style, Nike ad ×2, Berliner sausage character | creative 9 |
| page · head · box · brain · colour · branch (**front-end building**) | 10: portfolio site ×2, page animations, Lando Norris effect, technology page, Timeline spec ×2, Figma conversion, "Phase 2 workflow" ×2 | coding 6, planning 2, debugging 1, research 1 |
| requirement · paper · action · outcome · tool (**AI research and career**) | 9: AI-creativity papers, presentation ×2, project revival, chat review, Diehl Aviation ×2, two job applications | mixed (5 types) |
| die · der · word · das · bus (**German learning**) | 5 | learning 3, planning 2 |
| ich · und · room · Bremen (**life in Bremen**) | 4 | planning 3, writing 1 |
| solitary | 18 | — |

**Near-duplicate pairs (similarity ≥ 0.96), all real continuations or re-exports:** c06↔c55, c18↔c53, c34↔c54, c36↔c52.

### 9.3 What the baseline misses (why embeddings, §4)
- The 18 solitary chats include ones a person would place instantly: hybrid AI filmmaking (c24), the honey product video (c23), the jellyfish animation (c27) → film; Anki flashcards (c11) → German learning; the visa extension (c26) → Bremen.
- Word overlap can't see these, but meaning can. Those five, plus the four near-duplicates, are the acceptance set in §4.

### 9.5 Calibrating the cuts on the full fingerprint (engine module, 57 chats)
On the full fingerprint (title + dialogue + engine extraction), pair similarity runs higher than on user messages only: p50 0.052 · p80 0.103 · p90 0.132 · p95 0.168 · p99 0.301.

| Cut | Regions (≥ 2 chats) | Solitary | Region sizes |
|---|---|---|---|
| 0.16 | 8 | 21 | 8, 6, 5, 5, 4, 3, 3, 2 |
| 0.14 | 8 | 18 | 9, 6, 6, 5, 4, 4, 3, 2 |
| 0.12 | 6 | 17 | 10, 10, 9, 5, 4, 2 |
| 0.10 | 4 | 14 | 22, 11, 5, 5 |

So **regions use p90** (about 0.13, project level) and **areas use p80** (about 0.10, broad).

### 9.4 Similarity distribution (calibrates link thresholds)
All 1,485 pairs, F3: median 0.033 · 90th percentile 0.101 · 95th 0.134 · 99th 0.268 · max 0.996. Almost all pairs are unrelated, so thresholds must be percentiles of *your* data, not fixed constants.

---

## 10. Data contract: `brain_map.json` (library root; regenerated on demand, versioned)

```json
{
  "version": 3, "createdAt": "…", "method": {"similarity": "tfidf-v1 | embed:<model>", "regionCut": 0.12, "areaCut": 0.08, "fingerprint": "F4+engine"},
  "chats": {"<chatId>": {"fingerprintHash": "…", "area": "a2", "region": "r7", "side": 1, "direction": [x, y, z], "pinned": true}},
  "areas":   {"a2": {"name": "…", "nameSource": "keywords|model|owner", "keywords": ["…"], "regions": ["r7", "r9"]}},
  "regions": {"r7": {"name": "…", "nameSource": "…", "keywords": ["…"], "members": ["<chatId>"], "cohesion": 0.30}},
  "links": [{"a": "<chatId>", "b": "<chatId>", "type": "continued|reused|similar|owner", "score": 0.97, "evidence": {"keywords": ["…"], "passages": ["…"], "gapHours": 3}}],
  "previous": "brain_map.v2.json"
}
```

**Engine:** `engine/brainmap.py`, pure Python (the engine's dependency rule: no numpy). CLI: `python -m engine brainmap <library-or-corpus> -o brain_map.json`. The Brain reads `chats[id].side/direction` instead of `LOBES`.

---

## 11. Honesty rules
1. Position comes only from chat text. No position from a label you didn't confirm.
2. Every region name records its source; owner names win; proposals are never auto-accepted.
3. Every axon carries its evidence; no evidence, no axon.
4. Solitary chats stay solitary rather than being forced into a region.
5. A re-map is previewed and archived, never silent.
6. Task type never moves a chat.

---

## 12. Plan (track B1; ENGINE work by Claude Code, the S4.7 UI by its assigned builder)

| Step | What | Done when | Gate |
|---|---|---|---|
| **B1.0** | This spec + study | committed | **owner reads §2 and decides: regions by content, task type as property** |
| **B1.1** | `engine/brainmap.py` baseline: fingerprints, TF-IDF, near-duplicates, two-level clustering, keyword names, continued/reused/similar links, flat-map layout → `brain_map.json`; CLI; tier1 tests (determinism, near-duplicates join, solitary stays solitary, every link has evidence, stability: adding a chat moves no one) | tests green; corpus map reproduces §9.2 | — |
| **B1.2** | Brain Lab preview: placement from `brain_map.json`, area and region labels, axons with evidence on hover; unmapped corpus chats shown as faint, unprocessed somas | screenshot review | **owner judges the map** |
| **B1.3** | **S4.7 amended:** the review-table picker is **task type** (6 kinds; optional cheap suggestion, never auto-accepted). After promotion the engine assigns the chat to a region (zero LLM) and the Brain places it | a newly imported chat lands next to related chats | — |
| **B1.4** | `MODEL_EMBED` seam + cache; run the §4 acceptance test on the corpus | acceptance numbers in this spec | **cost gate, then owner decides baseline vs embeddings** |
| **B1.5** | Region naming by model (optional) + owner rename/merge/split UI; versioned re-map with preview | owner can rename a region and re-map with a preview | owner |
| **B1.6** | Workspace Brain switches from `LOBES` to `brain_map.json` | the workspace Brain shows regions | owner |

---

## Sources
- Huth, de Heer, Griffiths, Theunissen, Gallant, *Natural speech reveals the semantic maps that tile human cerebral cortex*, Nature 532 (2016): [PMC4852309](https://pmc.ncbi.nlm.nih.gov/articles/PMC4852309), [Gallant Lab](https://gallantlab.org/publications/2016-natural-speech-reveals-semantic/)
- Tamkin et al., *Clio: Privacy-Preserving Insights into Real-World AI Use* (Anthropic, 2024), facets → embeddings → k-means → model-named clusters → hierarchy: [arXiv 2412.13678](https://arxiv.org/pdf/2412.13678), [Anthropic](https://anthropic.com/news/clio), [Simon Willison's notes](https://simonwillison.net/2024/Dec/12/clio/)
- Chatterji et al., *How People Use ChatGPT* (NBER w34255, 2025), a topic taxonomy for chats: [NBER](https://www.nber.org/papers/w34255)
- Obsidian: [Smart Connections (embedding-based related notes)](https://obsidianstats.com/plugins/smart-connections); [Graph Analysis (Jaccard, Adamic-Adar, co-citation)](https://github.com/skepticmystic/graph-analysis); [graph view help](https://obsidian.md/help/plugins/graph); [size-aware label fading request](https://forum.obsidian.md/t/graph-text-fade-threshold-consider-node-size/6737)
- BERTopic (embeddings → UMAP → HDBSCAN → c-TF-IDF): [guide](https://www.analyticsvidhya.com/blog/2026/04/bertopic-guide/); UMAP on a sphere: [UMAP docs](https://umap-learn.readthedocs.io/en/latest/embedding_space.html)
- Hierarchical topic maps: [Nomic Atlas topic modeling](https://docs.nomic.ai/atlas/data-maps/topic-modeling); [Cosmograph clustering](https://cosmograph.app/docs-lib/features/clustering/)
- Mental-map preservation in changing graphs: [Diehl & Görg, GD 2002](https://www.st.uni-trier.de/diehl/pubs/GD02_LNCS.pdf); [Archambault & Purchase, memorability](https://research.monash.edu/en/publications/the-mental-map-and-memorability-in-dynamic-graphs/)
- Near-duplicates and reuse: [Stanford IR book, shingling](https://nlp.stanford.edu/IR-book/html/htmledition/near-duplicates-and-shingling-1.html); TF-IDF as a strong clustering baseline: [arXiv 2104.11556](https://arxiv.org/pdf/2104.11556)
