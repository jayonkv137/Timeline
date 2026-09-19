# golden_01 — Hand-Labeled Benchmark Worksheet

**Source Corpus Chat:** `c15_creative_medium`  
**Original Title:** "Portfolio about page redesign"  
**Format:** `claude_web_json`  
**Total Pairs:** 8  
**Task Type:** creative / portfolio film design  
**Language:** en  
**Fidelity Grade:** degraded (1 image dropped across 8 pairs)

---

## 1. Role of golden_01 in the Testing Strategy
- **Breadth Gate:** The 17 usable chats (10 clean + 7 degraded) verify that the pipeline runs robustly across varying domains, styles, and lengths without crashing or violating invariants.
- **Depth / Correctness Gate (This File):** `golden_01` is hand-labeled **by human judgment before the engine touches it**. It provides the ground-truth standard to determine whether what the engine extracts (actions, requirements, decisions, mode) is factually and semantically correct, rather than merely measuring agreement between two language models.

---

## 2. Conversation Narrative Overview
The conversation is a high-level creative direction dialogue where the user pivots their portfolio "About" page from a standard GSAP text scroll into a 45–60s AI-generated nature documentary film treating the creative technologist as an exotic species, narrated in David Attenborough's style, with potential interactive 3D specimen cylinder mechanics.

---

## 3. Pair-by-Pair Dialogue Inventory & Annotation Prompts

### Pair 1: Problem Definition & Review of Existing About Page
- **User Turn (272 chars):** Mentions existing written/text about page; asks AI to review context from other portfolio chats.
- **AI Turn (5,098 chars):** Reconciles context; analyses GSAP scroll-scrub structure.
- **Human Annotation Target:**
  - *Expected Actions:* User states intent to evaluate current about page; AI synthesizes existing architecture.
  - *Requirements Introduced:* Req_01 (Portfolio about page revision).
  - *Steering / Decision:* Balanced initial framing.

### Pair 2: Concept Pivot — Text Scroll to 45–60s AI Film
- **User Turn (903 chars):** Explicit pivot: instead of written text, add an AI Video showcasing creative technologist brand; specifies 45-60s length.
- **AI Turn (6,584 chars):** Validates concept; suggests three structural pillars (tension, voice, visual language) and asks clarifying questions.
- **Human Annotation Target:**
  - *Expected Actions:* User defines major creative constraint (short AI video, 45-60s, brand positioning).
  - *Requirements Introduced:* Req_02 (Short AI video format: 45–60s), Req_03 (Creative technologist brand showcase).
  - *Steering / Decision:* Strong user steering (User establishes core creative pivot).

### Pair 3: Narrative Spine — Attenborough Nature Documentary
- **User Turn (571 chars):** Answers spine question: third-person nature documentary style, David Attenborough voice narrating Jayon's journey like an exotic species in its natural habitat.
- **AI Turn (3,178 chars):** Validates concept enthusiastically; flags voice-cloning ethics/constraints; requests draft script.
- **Human Annotation Target:**
  - *Expected Actions:* User locks spine & narrative persona; AI adds voice-cloning constraint.
  - *Requirements Introduced:* Req_04 (David Attenborough nature documentary voice/persona), Req_05 (Voice cloning / TTS feasibility).
  - *Steering / Decision:* User locks creative theme; AI introduces technical constraint.

### Pair 4: First Draft Script Review & Structural Rewrite
- **User Turn (1,941 chars):** Supplies full rough script draft ("THIS IS JAYON K VINOD...").
- **AI Turn (8,470 chars):** Structural diagnosis; notes draft is ~2.5 minutes (too long for 60s); provides tightened 50s rewrite with shot breakdown.
- **Human Annotation Target:**
  - *Expected Actions:* User provides draft content; AI tightens timing and drafts shot progression.
  - *Requirements Modified:* Req_02 (Timing constraint enforced: ~130 words for 50-60s).
  - *Decisions:* AI structural edit (length discipline); User authored core copy.

### Pair 5: Attenborough Reference & Narration Style Curation
- **User Turn (324 chars):** Asks for specific David Attenborough video references describing species to study narration rhythm.
- **AI Turn (4,594 chars):** Curates 4 iconic Attenborough clips with specific stylistic breakdown (whisper-pause, poetic wonder, scientific cadence).
- **Human Annotation Target:**
  - *Expected Actions:* User requests stylistic reference; AI curates and analyzes clips.
  - *Steering / Decision:* User asks for evidence/reference; AI supplies research material.

### Pair 6: Metaphorical Life-Narrative Nuance
- **User Turn (176 chars):** Clarifies reference preference: wants poetic/metaphorical life narrative rather than clinical observation.
- **AI Turn (4,044 chars):** Reframes clip selection towards metaphorical life-cycle storytelling (Mayfly, Bowerbird).
- **Human Annotation Target:**
  - *Expected Actions:* User sharpens aesthetic nuance (metaphorical over clinical).
  - *Steering / Decision:* User course correction.

### Pair 7: Interactive Video Exploration (Specimen Cylinder)
- **User Turn (2,476 chars):** Shares image (`Browse Shots.jpg`); explores interactive 3D video effect where user scrubs/interacts with specimen in cylinder.
- **AI Turn (9,772 chars):** Validates visual concept; analyzes technical feasibility (video scrub vs 3D canvas vs WebGL); flags heavy production scope risks.
- **Human Annotation Target:**
  - *Expected Actions:* User introduces interactive concept & reference visual; AI provides feasibility breakdown and warns of scope bloat.
  - *Requirements Introduced:* Req_06 (Interactive specimen scrub mechanics — tentative).
  - *Steering / Decision:* User ideates ambitious mechanic; AI acts as reality/scope check.

### Pair 8: Feasibility Hold & Deliberation
- **User Turn (253 chars):** Holds decision: "no no i am first thinking the feasibilty of this but let me think through this properly please".
- **AI Turn (2,062 chars):** Validates pausing decision: confirms user is in idea stage, not decision stage; holds execution.
- **Human Annotation Target:**
  - *Expected Actions:* User explicitly pauses build decision; AI accepts hold.
  - *Requirements Modified:* Req_06 held pending feasibility review.
  - *Decisions:* User decides to hold (explicit human decision).

---

## 4. Human Ground-Truth Consensus Target (To be finalized by Owner)

| Metric / Dimension | Human Expected Value | Owner Confirmation |
|---|---|---|
| **Root Outcome** | Personal portfolio About page redesign (AI film concept) | [ ] Confirmed |
| **Active Sub-Outcomes** | 1. Concept & Spine Definition<br>2. Script & Timing Tightening<br>3. Reference & Style Analysis<br>4. Interactive Cylinder Exploration | [ ] Confirmed |
| **Approximate Requirement Count** | ~5 to 8 core requirements | [ ] Confirmed |
| **Primary Steering Party** | User driven (User creates core concept, voice choice, pivot, and pauses) | [ ] Confirmed |
| **Expected Usage Mode** | **Copilot** (Balanced collaboration: User drives vision & constraints, AI provides structure, pacing & feasibility) | [ ] Confirmed |
| **Expected Direction Hint** | **user_heavy** or **balanced** | [ ] Confirmed |
