# Brain Vision — the Human × AI Co-Creation Brain

**Status:** the owner's North Star. Not a spec. It says where the product is going so that
everything built now (the node graph, the design system) is compatible with it.
**Source:** the owner's design conversations, consolidated 8 October 2026.
**Read by:** every role, before designing or building anything visual.

---

## 1. The idea in one paragraph

A living spatial map of everything a person and AI have created, explored, changed and
connected together over time. At the top it is a "brain": a portrait of the whole Human ×
AI collaboration that you understand in about five seconds. Zooming in moves through the
same object, from regions of work, to projects, to the story of one chat, to a single
exchange, to the original words. Every visible mark traces back to the real conversation.

The questions it answers:

- **What am I using AI for?** The main territories of work.
- **How am I working with it?** Who steered, who carried the work, where we truly co-created.
- **How do things connect?** An idea from one chat reused months later in another.
- **How did this evolve?** The path of one chat: intention → change → direction → output.

---

## 2. The zoom ladder

One structure, seen at different levels. Not five screens.

| Level | Shows | Answers |
|---|---|---|
| **Brain** | Major regions and clusters of work, overall Human and AI influence, strong connections | "What have Human and AI been working on together?" |
| **Project or goal** | Sub-goals, the chats that contributed, major outputs | "What makes up this project?" |
| **Chat** | The chat as a trajectory through time: start, meaningful states, direction changes, outputs. Alongside it, the outcome map (today's graph) | "How did this line of thinking evolve?" |
| **Pair** | One exchange as a transition from one state to the next, and who shaped it | "What changed here, and who shaped it?" |
| **Source** | The original user message and AI reply | "What exactly was said?" |

```
PAIR → CHAT EVOLUTION → CONNECTED CHATS → GOAL / PROJECT → PROJECT CLUSTERS → BRAIN
```

**The chat is a trajectory, not a container.** At chat level a node opens into a path.
Human and AI can be two strands within it, stronger or weaker as the work moves.

**A pair is a transition, not a node.** State before → the pair → state after. A visible
"beat" may later group several pairs; real data decides.

---

## 3. What the visuals must carry

**Two persistent colours.** One always means the human, one always means the AI, at
every level and on every surface. They never mean anything else. Regions, strands and
nodes carry their proportions, so you see where you steered, where AI carried the work,
and where you co-created, without reading numbers.

**Influence, not word count.** Showing who wrote more text is wrong. In the owner's first
real pair, the user set the direction and the AI did the retrieval and synthesis. The
visual must show *steering* and *carrying the work* as different things. The engine's
roles (SHAPER, EXECUTOR) and influence ledger are what make that possible.

**Geometry instead of labels.** A redirection bends the path; a new sub-goal branches; two
ideas converging merge. No "DIRECTION CHANGE" badges. Shapes are added only when real pairs
prove they're needed.

**Provenance everywhere.** Brain → project → chat → beat → transcript, always one click
from the original exchange. The visualisation summarises; the chat stays the source of
truth.

**Connections with honest strength.** "Discussed a similar topic" is weaker evidence than
"continued earlier work", which is weaker than "reused an output". They must be
distinguishable, even if they start out looking similar.

---

## 4. The working visual grammar (from the owner's Figma playground)

Primitives:

```
SEED   STATE   PAIR SEGMENT   BRANCH / MERGE   OUTPUT
```

Channels:

| Channel | Means |
|---|---|
| Colour | Who: human or AI |
| Position | Structure |
| Thickness | Contribution |
| Geometry | Change |
| Size | Significance |
| Proximity | Relationship |

**Open:** this grammar and today's `GRAPH_SYSTEM_SPEC.md` disagree in one place. The
graph spec uses node *size* for ledger mass, which is contribution. This grammar uses
*thickness* for contribution and *size* for significance. The design system (D5)
reconciles them, so one channel means one thing at every level.

---

## 5. The workspace

| Area | Purpose |
|---|---|
| **Brain tab** | Home base. Patterns and connections across all chats |
| **Chat tabs** | Several original conversations open at once, like browser tabs |
| **Left sidebar** | Search and find chats directly |
| **Right panel** | With the Brain active: explains the selected area. With a chat active: switches between that chat's **Map** and **Pair** views |

The core journey: **whole history → meaningful area → relevant chat → specific exchange →
original evidence**, and back to the same place in the Brain.

---

## 6. The head

At the top level the space can sit inside a subtle Human × AI head or brain silhouette:
an identity and orientation device saying "this is my shared thinking space with AI".

- Not anatomy. No "career lives in the frontal cortex". The data decides where things sit;
  related things cluster.
- It must never imply that the product has measured anyone's brain or ability.
- 2D or 3D, its exact form, and how colour works inside it are open.

---

## 7. What the Brain is not

- Not a dashboard full of metrics.
- Not every requirement as a node.
- Not every message linked to every other.
- Not 3D particles because they look cool.
- Not "AI 62.379%" everywhere.

**The engine is complex; the Brain is radically simpler.** The engine produces reliable
meaning (actions, outcomes, requirements, influence, provenance). A distilled visual model
(seed, state, pair transition, branch, merge, output, Human and AI influence) carries it.
The Brain renders that.

---

## 8. Real scale to design for

From `data/archive/registry.json` (8 Oct 2026), Claude only, before the ChatGPT and
Gemini exports:

| | |
|---|---|
| Conversations | 313 |
| Pairs | 2,759 |
| Median chat length | 2 pairs |
| Longest chat | 242 pairs |

Most chats are tiny and a few are huge. The Brain must stay calm with hundreds of mostly
short chats and readable inside a 242-pair chat. With all platforms, expect thousands.

---

## 9. Where each level lives (from the extension and plugin research)

| Surface | Main levels | Constraint |
|---|---|---|
| Web app | All five; Brain is home | Full workspace |
| Browser side panel on claude.ai and chatgpt.com | Chat (Map) and Pair, for the open chat; "Open in Brain" goes to the full app | 360–420 px, host page beside it, local-first data |
| In-chat widget (MCP Apps) | One chat's Map | Host theme, sandboxed, only what the model passes |
| Claude Code and Codex sessions | Chat and Pair, live | Developer audience, tool-heavy chats |
| 3D head view | Brain and Project | WebGL, stable positions, readable labels |
| Print and design pack | Chat storyline, Pair | Static, ink-safe |

---

## 10. Settled and open

**Settled:** the purpose (a simple, traceable, evolving picture of Human × AI
co-creation); two persistent party colours; semantic zoom through one object; provenance
to the original exchange; influence over word count; simplicity over the engine's
complexity; real data decides the grammar, pair by pair.

**Open:** the exact colours; the head's form; 2D vs 3D at each level; how colour
proportions render (blend, strands, shares); whether beats group pairs; how cross-chat
links and projects are computed. The engine doesn't have this layer yet. It will be a
separate track; see `docs/ROADMAP.md`.

**Method the owner chose:** develop the grammar from real data, one pair at a time.
Understand the exchange, inspect what the engine recorded, decide what matters to the
viewer, explore a few simple representations, choose provisionally, add the next pair,
and adjust.
