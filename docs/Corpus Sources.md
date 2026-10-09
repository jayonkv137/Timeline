# CORPUS_SOURCES.md — public datasets for the test corpus

Research, 2026-09-18. Answers the question: can the corpus be strengthened with public
data rather than only Jayon's own exported chats.

**Short answer: yes, and one source matters more than all the others.** But this is an
addition to the corpus, not a replacement, and it changes what the corpus is for. See
section 5 before acting on any of it.

---

## 1. Why this came up

The 36 ingested chats reconcile perfectly but are weak as an extraction test set:

- 829 images dropped across 909 pairs
- only 10 of 36 chats are clean, and 7 of those are 1 to 4 pairs long
- realistically two usable chats, c14 (14 pairs) and c05 (7 pairs)
- one language, one exporter, one person, and a heavy skew toward creative and visual work

For E1 that is thin. For E3 stability measurement it is thinner, since bands measured on
two chats say almost nothing.

---

## 2. The one that matters most: COTRACE's own data

**CoTrace**, Kim, Mindel, Kim and Wu, arXiv 2605.21363, code at
`github.com/rladmstn1714/CoTrace`.

The paper reports results over **638 real collaboration logs** and publishes its
implementation. If the logs or a subset are in that repository, this is the single most
valuable corpus available, for a reason none of the others share:

**It lets you compare your numbers against theirs on the same data.** Their headline is
humans holding 75 to 89 percent of SHAPER mass and LLMs 96 to 99 percent of EXECUTOR
mass. If your engine, on their data, lands in those bands, your reimplementation is
validated against the source. If it does not, you have found either a bug or a genuine
interpretive difference, and both are thesis material.

Nothing else on this list can do that.

**Action:** check the repository for a `data/` directory and the licence, before
downloading anything. Even 20 of their logs would be worth more than 200 random ones.

---

## 3. General-purpose conversation corpora

### WildChat — the best fit for volume and variety

AllenAI, on Hugging Face. Several sizes: <cite index="31-1">WildChat is a collection of 650K conversations between human users and ChatGPT, collected by offering online users free access to GPT-3.5 and GPT-4</cite>. <cite index="30-1">The larger WildChat-4.8M holds 3,199,860 non-toxic conversations and extends the collection window, including conversations with o1-preview and o1-mini</cite>.

Why it fits: <cite index="31-1">the interactions include ambiguous user requests, code-switching, topic-switching and political discussions</cite>, which is exactly the messy variety your corpus lacks. Coverage spans <cite index="37-1">creative and personal writing, educational and homework queries, and professional work such as drafting emails, presentations and job-seeking material</cite>.

Two cautions worth knowing before you plan around it. <cite index="32-1">Mean turns per conversation is about 2.52</cite>, so most conversations are very short and you would have to filter hard for multi-turn depth. And <cite index="31-1">a small subset contains empty user inputs, 12,405 of 652,139, where users submitted nothing and the assistant responded anyway</cite>, which your importer must handle rather than choke on. Your pairing rules already cover empty turns, so this is a free real-world test of rule 4.

Licence: <cite index="31-1">WildChat is available under the ODC-BY licence, applied retroactively to earlier downloads</cite>, with <cite index="37-1">the datasets publicly hosted on Hugging Face by the Allen Institute for AI under a research-only arrangement</cite>.

### DevGPT — the best fit for technical, goal-dense conversations

NAIST-SE, on GitHub and Zenodo, built for the MSR 2024 Mining Challenge. <cite index="43-1">It was created by mining links to ChatGPT conversations shared by developers through OpenAI's sharing feature, tracked weekly from GitHub and Hacker News starting July 2023</cite>. <cite index="47-1">The October 2023 snapshot contains 4,733 shared links from 3,559 references, totalling 29,778 prompts and answers including 19,106 code snippets, with Python, JavaScript and Bash the top three languages</cite>.

Why it fits your specific need: COTRACE found that technical closed-ended tasks produce
more AI goal-shaping than open-ended ones. DevGPT is almost entirely technical
closed-ended work, so it is the natural counterweight to your own creative-heavy corpus
and the obvious place to test that finding reproduces on your engine.

It also comes with something none of the others have: <cite index="45-1">the conversations are paired with the software development artifacts they relate to, including commits and discussions</cite>. You can see whether what was decided in the chat actually shipped.

Caution: many entries are single exchanges rather than long sessions. Filter for
multi-turn before use.

### LMSYS-Chat-1M — probably skip

One million conversations from the Chatbot Arena. Worth knowing about, worth not using.
A study choosing between the two put the reason plainly: <cite index="36-1">LMSYS-Chat-1M emphasised a gamified interface inviting head-to-head comparisons of 25 models, while WildChat's interface seemed more ecologically valid</cite>. People comparing models are not people doing work, and your engine measures work.

### ShareGPT — legacy, use with care

<cite index="38-1">ShareGPT52K and ShareGPT92K were compiled via a Chrome extension that let users share ChatGPT conversations, with the user IDs and full interactions recorded and downloadable</cite>. Older, messier provenance, and its consent story is weaker than WildChat's. Only if you need extra volume.

---

## 4. The academic neighbours, for a different purpose

### CoAuthor — not a corpus, a comparison point

Lee, Liang and Yang, CHI 2022, Stanford. <cite index="52-1">It contains interactions between 63 writers and 4 instances of GPT-3 across 1,445 writing sessions</cite>, and <cite index="50-1">records writing sessions at keystroke level, capturing text insertion and deletion, cursor movement and suggestion selection</cite>. <cite index="51-1">The dataset and a session replay interface are public at coauthor.stanford.edu</cite>.

**This is not chat data and will not feed your pipeline.** It is inline writing
assistance, not turn-taking dialogue. Its value to you is different and real: it is the
dataset behind CoAuthorViz, one of the academic neighbours from your Step 2 research, and
<cite index="50-1">the stated goal was to investigate where language models succeed and fail in the writing process rather than to make people write faster</cite>, which is close enough to your framing that a supervisor may ask how you differ.

Know it. Cite it. Do not import it.

---

## 5. Before you act on any of this

Five things, and the first two are the important ones.

**5.1 This changes what the corpus is for.** Your 36 chats are *your* conversations. The
thesis is about a person seeing their own agency, and a demo on your own work is worth
more than a demo on a stranger's. Public datasets test whether the **engine** is robust.
Your own chats test whether the **product** means anything. Keep both, label them
separately, and never let a public chat become the demo.

**5.2 The golden chat must stay yours.** Hand-labelling requires knowing what the person
meant. You cannot hand-label a stranger's conversation reliably, because you do not know
which of their statements were binding intentions and which were thinking aloud. `c14`
stays the golden chat.

**5.3 Licences differ and matter for a thesis.** WildChat is ODC-BY and research-oriented.
DevGPT comes from a mining challenge with its own terms. The MSR challenge organisers
were explicit that <cite index="43-1">sharing or using personally identifiable information is strictly prohibited</cite>. Read each licence before committing data into a public repo, which yours now is.

**5.4 Do not commit bulk data.** Your repo is public and already carries 36 personal
conversations. Adding thousands of third-party ones would be a mistake. Store a
**download script plus a manifest of selected ids**, not the data itself. That keeps the
repo small, the licences clean, and the selection reproducible.

**5.5 Import them through the same importer.** A new `source_kind` per dataset, the same
`dialogue.json` contract, the same `source_meta.json` fidelity accounting, the same
`meta.yaml` classification. No dataset gets a special path into the engine. If WildChat
needs a bypass, the importer is wrong.

---

## 6. Recommended plan

Deliberately small, and sequenced so it never blocks the build.

**Now, during E1:** nothing. E1 needs `golden_01` and ten of your own chats. Public data
would only add variables while you are trying to tell whether extraction works at all.

**Before E3, when stability gets measured:**

1. Check `github.com/rladmstn1714/CoTrace` for published logs. If present, this is the
   first and most valuable addition.
2. Add **10 to 15 WildChat conversations**, filtered for 6 or more turns, spread across
   task types, and non-English for one or two.
3. Add **5 to 10 DevGPT conversations**, filtered for multi-turn, to load the technical
   closed-ended end of the matrix.
4. Write `scripts/fetch_public_corpus.py`: takes a manifest of dataset ids, downloads,
   converts to `dialogue.json`, runs the existing importer. Commit the script and the
   manifest. Never the data.
5. Tag every public entry `provenance: public` in `meta.yaml`, and every chat of yours
   `provenance: owner`. Extraction quality gets measured on both. The product
   demonstration only ever uses `owner`.

**Target after that:** roughly 35 usable chats, half yours and half public, across all
six task types, three length bands, both prompt styles, and at least two languages. That
is a corpus worth quoting a stability band from.

---

## 7. Sources

- CoTrace, Kim et al., arXiv 2605.21363, `github.com/rladmstn1714/CoTrace`
- WildChat, AllenAI: `huggingface.co/datasets/allenai/WildChat`, `WildChat-1M`, `WildChat-4.8M`
- DevGPT, Xiao, Treude, Hata and Matsumoto, MSR 2024, arXiv 2309.03914, `github.com/NAIST-SE/DevGPT`, Zenodo record 8304091
- LMSYS-Chat-1M, Chatbot Arena
- ShareGPT52K / 92K, Hugging Face
- CoAuthor, Lee, Liang and Yang, CHI 2022, `coauthor.stanford.edu`, arXiv 2201.06796
