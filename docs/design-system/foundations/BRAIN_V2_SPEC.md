# BRAIN_V2_SPEC: the simple brain (KISS)

Status: **v0.1, proposed (owner review 12 Oct 2026).** Prototype: `npm run workspace` → `http://localhost:5180/brain-v2.html`; data from `scripts/design_system/brain_v2_data.py`.

**Supersedes** the detailed neuron template (BRAIN_NEURON_SPEC §7–10) as the Brain's overview design. Kept from the earlier work:
- the empirical rules: size from mass (Session 3), who-led from the ledger share, regions and connections (BRAIN_REGIONS_SPEC)
- the honesty rules

## Owner's words (12 Oct 2026)

> "I don't like this design at all … the current nerve system looks really really bad"
> "I don't like the synthetic orange colour, how the neurons are shaped, how it is sized, then the connections, how the light radiates — nobody can distinguish in one second what it is"
> "for a very higher top view itself the disparity of human vs AI in the full brain should be very clearly recognisable … how much of the human brain is taken over by AI or becoming symbiotic"
> "the range of distinct broader topics you and AI are discussing … what is the best way to show a user's interests"
> "not only for my specific chats … universally and generically for any type of user"
> "KISS rule … simple and elegant", reference: an Obsidian knowledge graph drawn inside a brain, with coloured clusters

---

## 1. The one-second test (every rule below serves it)

A stranger looks at the brain for one second and can say:
1. **How much of this person's work was the AI's?** → the brain is mostly one colour or the other; the balance bar says the exact number.
2. **What does this person talk to AI about?** → the lobe names, the same eight for everyone.
3. **Where are the big things?** → the biggest dots.

Anything that does not help one of these three is removed from the overview.

## 2. One channel, one meaning

| Channel | Means | Rule |
|---|---|---|
| **A dot** | one chat | a glowing point on the brain; nothing else is a dot except its outcomes |
| **Dot size** | how much happened | R = 0.028 × ∛(mass ÷ 25) (Session 3, volume-true) |
| **Dot colour (Who lens)** | who led the work | **three states, full colour:** human-led (you did ≥ 60% of the measured work) · co-created (40–60%, white) · AI-led (AI did ≥ 60%) · grey ring = not mapped yet |
| **Small dots + lines around a chat** | its outcomes (the chat's own graph) | same colour rule per outcome; thin line to its parent |
| **Where** | what it is about | universal lobe (§4) → your own region inside it (BRAIN_REGIONS_SPEC) |
| **Lobe glow** | the lobe's balance | Who lens: the lobe glows in the colour of its total work balance, so you see which parts of your brain became AI-led. Topics lens: the lobe's topic hue |
| **Lines between chats** | evidence of a connection | smooth arcs over the brain; continued (bright) > reused > similar (faint); only the open chat's lines when one is open |
| **Balance bar** (top left) | the whole brain | You x% · AI y% of the measured work across mapped chats. The one headline number; the owner asked for the disparity to be evident |

**Why three discrete states, not a gradient:**
- Hue is read pre-attentively, but a continuous blend makes 25%-you and 45%-you look nearly alike, and blends wash out to beige or white under glow (review 1, §8).
- Three named states with fixed thresholds are read instantly and explained in one legend line.
- Exact percentages live in the tooltip, the card and the bar.

## 3. Two lenses, never both at once
- **Who led** (default): colour = human / co-created / AI.
- **Topics:** colour = universal domain, like the coloured clusters in the owner's reference.

Both questions use hue. Showing them together would make neither readable, so one switch picks the question.

## 4. Universal topics: the same eight lobes for everyone

| Lobe | Covers | Place (brain metaphor) |
|---|---|---|
| Work & career | jobs, applications, business, strategy | frontal, upper (planning) |
| Life & admin | housing, visas, money, travel, paperwork | frontal, lower |
| Writing & communication | emails, letters, editing, translation | temporal, front (language) |
| Learning & education | lessons, practice, languages, courses | temporal, middle (memory) |
| Research & ideas | papers, analysis, concepts, reflection | upper middle |
| Technology & code | software, websites, data, tools | parietal, upper back |
| Creative & media | images, video, film, art, music | occipital, back (vision) |
| Health & personal | health, relationships, feelings, personal life | temporal, lower back |
| (Other) | anything that fits none | lateral centre |

**Why fixed lobes, and why these eight:**
- Every person's brain then has the same anatomy: "creative is at the back" holds for anyone, and two people's brains can be compared.
- The largest real-world studies of AI chats both classify into a small fixed top level:
  - OpenAI *How People Use ChatGPT* (Chatterji et al., NBER 2025): 7 broad topics, e.g. practical guidance, seeking information, writing, technical help, multimedia, self-expression
  - Anthropic's Economic Index: Clio maps each conversation to an O\*NET task, which rolls up into broad occupational groups (Computer & Mathematical 37%, Arts & Media 10%, Education 9%, …)
- Those two cover work (O\*NET) and purpose (ChatGPT) but not life domains such as housing and relationships. The eight lobes merge both and add life admin and personal.
- **COTRACE itself** (Kim et al., 2026) goes "broader" only *inside* one chat: actions → outcomes → **intentions** (Step 1c). It has no cross-chat topic layer, so this layer is ours.

**Below the lobes, the person's own topics:** inside each lobe, chats cluster into the person's own regions, found in their text (BRAIN_REGIONS_SPEC). A region votes its majority lobe so its chats stay together.

**Classification (how a chat gets its lobe):**
1. **Now, zero cost:** a keyword baseline over title (×3) and messages, then the region vote. On the 57 corpus chats this is about 9 in 10 sensible by reading the titles. Clear misses:
   - two job applications filed under Research (the region vote pulled them)
   - a text-correction chat filed under Research
   - two portfolio-page chats filed under Writing
2. **Production (cost-gated):** a closed-set classifier, either one cheap model call per chat (as OpenAI and Anthropic do) or embedding similarity to lobe descriptions. Acceptance: ≥ 95% on an owner-checked sample, multilingual.
3. **The owner's correction always wins** and is stored. The suggestion is shown as a suggestion ("keyword baseline: you can correct it").

## 5. What the engine gives us to tell human from AI (final state of every chat)

| Signal | Engine source | Shown where |
|---|---|---|
| **Work share** (who shaped the outcomes) | ledger: Σ human vs AI mass | **dot colour, lobe glow, balance bar** |
| Per-outcome work share | ledger by outcome | outcome dots |
| Decisions (who created each requirement) | requirement creators | card ("decisions: you 13, AI 5") |
| Work mode per exchange (Centaur, Cyborg, Self-Automator) | panel bundle HOW | card (later) |
| Roles (shaper vs executor actions) | Step 1a actions | card (later) |
| Questions asked / answered by whom | slots | card (later) |
| Size of the chat | mass, exchanges | dot size; card |

**KISS:** only the **work share** is on the brain. Everything else is one click away.

## 6. Text and interaction
- **Always visible:** lobe names, with chat count and the lobe's state ("16 chats · AI-led"). Labels show only for lobes facing you.
- **Hover:** chat title and "you x% · AI y% · state".
- **Click:**
  - the camera turns to the chat
  - its outcome graph and connections light up and everything else dims
  - the card shows topic, region, work share bar, outcomes, decisions, exchanges and connections with evidence
  - Esc closes.
- **Options:** outcomes on or off, connections on or off, AI colour (two palettes for the owner to choose).

## 7. Works for anyone (universality checklist)
- [x] The lobes are fixed and person-independent; empty lobes stay dark, so nothing is invented.
- [x] All thresholds are either fixed meanings (60/40 for who led) or percentiles of the person's own data (regions, connections).
- [x] Chats not yet processed are shown honestly (grey ring, placed by text, no colour or size).
- [x] Size uses one absolute scale, so a new chat never shrinks the others.
- [ ] **Multilingual classification.** The baseline lexicon is English with German function words; production needs the multilingual classifier (§4).
- [ ] Scale test at 300+ chats (the label budget and glow overlap rules).

## 8. Open decisions for the owner
1. **The AI colour:** blue/amber (current tokens) or cyan/violet (closer to the reference). This decides DDR-005.
2. **The eight lobes:** keep these names and places?
3. **The 60/40 thresholds** for human-led and AI-led.
4. **Retire the detailed neuron (twigs, membranes) from the Brain entirely,** or keep it only for a single opened chat in a later phase?

## 9. Measured on the corpus (57 chats, 14 mapped)
- **Balance:** you 2,405 · AI 4,928 of measured mass = **you 33% · AI 67%**.
- **Lobes:**

  | Lobe | Chats |
  |---|---|
  | Research | 16 |
  | Creative | 14 |
  | Tech | 11 |
  | Learning | 7 |
  | Life | 5 |
  | Writing | 3 |
  | Work | 1 |

  Most mapped chats are AI-led; c10 is the only human-led one.
- **Screenshots in `brain-neuron/v2/`:**
  - who lens: `who-blue-amber.jpg`
  - topics lens: `topics.jpg`
  - cyan/violet palette: `who-cyan-violet.jpg`
  - an opened chat: `open-chat.jpg`

## Sources
- COTRACE: Kim, Mindel, Kim, Wu, *"I Didn't Make the Micro Decisions": Measuring, Inducing, and Exposing Goal-Level AI Contributions in Collaboration* (2026): [arXiv 2605.21363](https://arxiv.org/pdf/2605.21363)
- Chatterji et al., *How People Use ChatGPT* (NBER w34255, 2025): [NBER](https://www.nber.org/papers/w34255), [OpenAI PDF](https://cdn.openai.com/pdf/a253471f-8260-40c6-a2cc-aa93fe9f142e/economic-research-chatgpt-usage-paper.pdf)
- Anthropic Economic Index (Clio → O\*NET tasks → occupational groups): [Anthropic](https://www.anthropic.com/news/the-anthropic-economic-index), [arXiv 2503.04761](https://arxiv.org/pdf/2503.04761)
- Part-to-whole and colour perception: [Bailey & Gleicher 2025](https://arxiv.org/pdf/2508.01881); [palette families for judgments (EuroVis 2024)](https://arxiv.org/abs/2406.14452)
- Hierarchical topic display: [bubble treemaps](https://graphics.uni-konstanz.de/publikationen/Goertler2018BubbleTreemapsUncertainty/bubble-treemaps.pdf); [hierarchy visualisation evaluation](https://arxiv.org/pdf/1908.01277)
- Smooth, bundled links: [Holten 2006, hierarchical edge bundles](https://research.tue.nl/nl/publications/hierarchical-edge-bundles-visualization-of-adjacency-relations-in/)
