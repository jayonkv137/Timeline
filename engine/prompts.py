"""FROZEN — copied from COTRACE_PIPELINE_SPEC v5 §3.1, §4.1, §5.1, §6.1, §7.1;
do not edit without spec change.

Each constant below is the VERBATIM prompt body from the spec's fenced block
(docs/Cotrace Pipeline Spec.md). If a prompt ever seems to need changing, that
is a SPEC_QUESTIONS.md entry plus a conservative workaround — never an edit
here (AGENTS.md rule 1, Build Playbook §5).

Placeholders are `{name}` tokens filled by `fill()` via literal string
replacement (NOT str.format — the prompts contain literal JSON braces).
"""

STEP_1A = """You are analyzing **one block of a longer dialogue** to extract actions.

**ACTION** = An atomic communicative act a speaker **directly performed** in a turn.
- Atomic action = minimal unit of action the speaker directly performed. - e.g.
"User asks to find a paper about HCI in NLP conferences" → split into "User asks
to find a paper about HCI", "User asks to find a paper in NLP conferences".
- Include evidence quote from the utterance.

**Possible action types** (generate new types if needed):
Accept, Acknowledge, Address, Allow, Analyze, Apologize, Ask, Challenge, Clarify,
Classify, Compare, Complain, Confirm, Connect, Constrain, Critique, Decide, Define,
Delegate, Describe, Draft, Emphasize, Evaluate, Explain, Feedback, Formalize, Frame,
Greet, Hypothesize, Implement, Include, Infer, Instruct, Invite, Justify, List,
Modify, Observe, Plan, Provide, Qualify, Recommend, Refuse, Report, Request, State,
Suggest, Summarize, Warn

**Role:** **SHAPER | EXECUTOR | OTHER**
* **SHAPER:** Creates/shapes/revises the goal/requirement by proposing new ideas,
new tasks, constraints, alternatives, or directions.
* **EXECUTOR:** Executes/achieves the desired outcome/goal/requirement (e.g.,
drafting text, providing requested information, coding, searching, implementing).
* **OTHER:** Neither SHAPER nor EXECUTOR.

**Turn ID format:** each turn is labeled **U(x,y)** or **A(x,y)**, where **U**=user
turn, **A**=AI turn, **x**=the pair number this turn belongs to (the 1st user+AI
exchange is pair 1, the 2nd is pair 2, etc.), and **y**=the action's position
within that turn (1, 2, 3… in the order it was extracted). e.g. the user's 2nd
atomic action in pair 1 is "U(1,2)"; the AI's 1st atomic action in pair 3 is
"A(3,1)". Use this format for every turn id below — do not use plain integers.

=== DIALOGUE BLOCK START ===
{dialogue block}
=== DIALOGUE BLOCK END ===

Now, extract ALL actions from EVERY turn. Return JSON only, pretty-printed with
2-space indentation and each key on its own line (not compact/single-line
objects):
{ "actions": [ { "turn id": "<U(x,y) or A(x,y)>", "action type": "<action type>",
"action text": "<brief description in third person>", "role":
"<SHAPER|EXECUTOR|OTHER>", "evidence quote": "<quote from utterance>" } ]
}
Respond with ONLY the JSON object. No additional text."""


STEP_1B = """Step 1b: Outcome Extraction

You are given ALL actions extracted from a complete dialogue. Your task:
(1) Identify **outcomes** (purpose-linked desired deliverables)
(2) Assign every action to exactly one outcome
(3) Maintain the dialogue summary: if the collaboration's core purpose is
unchanged since the prior summary, return it unchanged; if new actions
materially extend or shift that purpose, revise the summary to reflect the
fuller picture. Keep it to 1-2 sentences regardless of which case applies.

Every collaboration has a **purpose**. **Outcomes are purpose-linked desired
deliverables** --- concrete outputs that participants are actually working toward.
- **Outcomes = purpose-linked desired deliverables:** Deliverables are not limited
to text or documents --- they can be a **decision**, **advice**, **plan**,
**clarification**, or any other concrete result. Do **not** include things only
mentioned without being adopted as a goal. - **Requested or agreed outputs:** Any
concrete output a participant **explicitly requests** or participants **agree to
produce** is a deliverable. - **Primary output:** The main thing the dialogue aims
to produce must appear as an outcome. Sub-deliverables are children. - **Phrasing:**
e.g. "decision for X", "advice for X", "draft for X", "plan for X". - **Hierarchy:**
**parent** = abstract/general, **child** = specific/concrete. Use parent outcome id
/ child outcome ids. - **Granularity:** Prefer consolidated, task-level outcomes.
Example: "Workshop plan (date, venue, agenda)" NOT separate "Decide date", "Decide
time", etc. - **No duplicates.** Each distinct deliverable exactly once.

=== DIALOGUE CONTEXT (prior dialogue summary; empty on first call) ===
{dialogue summary}
=== ALL ACTIONS (every action accumulated across the whole dialogue so far) ===
{all actions block}

Return JSON only:
{ "dialogue summary": "<collaboration purpose, 1-2 sentences>", "outcomes": [
{ "outcome id": "outcome 1", "outcome": "<purpose-linked desired deliverable
description>", "turn id": "<U(x,y) or A(x,y) of the action where this outcome
first appears>", "parent outcome id": null, "child outcome ids": [], "related
outcome ids": [], "confidence": <float 0.0--1.0> } ], "action to outcome": {
"<action id>": "<outcome id>" } }
IMPORTANT: action to outcome must map EVERY action id to an outcome id. No action
left unassigned.
Respond with ONLY the JSON object. No additional text."""


STEP_1C = """Step 1c: Intention Extraction

You are given a list of outcomes from a dialogue.

=== OUTCOMES ===
{outcomes list}

(1) Identify distinct **intentions** (high-level goals or purposes) that these
outcomes serve. (2) Assign each outcome to exactly one intention.

Output JSON only:
{ "intentions": [ {"intention id": "I1", "intention": "short label"},
{"intention id": "I2", "intention": "another label"} ], "outcome to intention":
[{"outcome id": "outcome 1", "intention id": "I1"}, ...] }
- Every outcome id appears exactly once in outcome to intention. Use intention id
from the intentions list."""


STEP_2 = """Step 2: Requirement Extraction

You are given ONE outcome and the actions bound to it. Extract **requirements**
(binding success conditions) for this outcome only.

=== OUTCOME ===
{outcome id}: {outcome description}
=== ACTIONS FOR THIS OUTCOME ===
{outcome actions block}
=== PRIOR REQUIREMENTS FOR THIS OUTCOME (if any; empty on first extraction) ===
{prior requirements block}
=== PRIOR OPEN SLOTS FOR THIS OUTCOME (if any; empty on first extraction) ===
{prior open slots block}

**REQUIREMENT** = An atomic, externally verifiable SUCCESS CONDITION for an outcome.
- Binary testable (pass/fail). - Must be explicitly stated or adopted as binding in
the dialogue.

**NOT a requirement:** content itself, advice, implementation methods, internal
reasoning, example outputs, one-off decisions.

Extract ONLY if ALL pass:
1) NECESSITY --- framed as mandatory (must/need/required/cannot, numeric
constraints, explicit include/exclude)
2) GROUNDING --- directly stated, no inference
3) REPLACEABILITY --- cannot be swapped without violating success
4) BINARY TESTABILITY --- reviewer can judge pass/fail

If an action raises a substantive idea, constraint, or decision point but FAILS
gate (1) NECESSITY specifically because of hedge or uncertainty language — this
includes option-uncertainty ("maybe", "could", "might", "may", "would possibly",
"perhaps", "mix / pick later"), epistemic hedges ("I think", "it seems", "I
believe", "it appears" — used to qualify the CONTENT of the claim, not as a
conversational filler elsewhere in the sentence), or approximation language
("about", "some", "most", "somewhat", "probably", "likely") — OR because the
action commits to determining something later rather than specifying it now
("I'll recommend based on your answer", "I'll decide after", "I'll verify before
committing") — do NOT discard it. Use the open_slot operation (see below) instead
of create. This applies only to Necessity failures caused by hedging, uncertainty,
or deferred content; failures of gates 2-4, content that is not substantive at all
(small talk, pure acknowledgment, restating something already said), or content
where a hedge word appears only as filler alongside an otherwise clearly mandatory
statement (e.g. "I think this must include X" — still a requirement, the hedge
qualifies the speaker's tone, not the requirement's content), are still handled
normally (dropped or extracted as create, respectively).

Operations:
- **create**: New requirement. Check PRIOR REQUIREMENTS above for revise BEFORE
create. - **revise**: Modify existing requirement (contradicts/tightens/
relaxes/replaces). Use EXACT existing req id (from PRIOR REQUIREMENTS) in related
to (within this outcome). - **delete**: Explicitly cancels a previously binding
condition. - **open_slot**: A hedged, uncertain, or deferred-content idea that
fails Necessity but is substantive enough to track — neither a binding requirement
nor nothing. Check PRIOR OPEN SLOTS above for resolve BEFORE open_slot: if this
action firmly answers/resolves a prior open slot, emit op="resolve" instead,
turning that slot into a new create with related to pointing at the resolved slot
id. Assign origin: "user" if the hedge came from the user's action, "AI" if from
the AI's action. A slot that has appeared in PRIOR OPEN SLOTS for 3 or more
consecutive pairs without being resolved should be marked op="abandon" — it is no
longer carried forward.

Edge cases:
- Advice itself is NOT a requirement. Only constraints ON the advice. - "Try to /
ideally / could / maybe" → not binding → not a requirement → check if substantive
enough for open_slot (see above); if not even substantive, drop entirely with no op.

Return JSON only (bound outcome id must be "{outcome id}"):
{ "requirement ops": [ { "op": "create", "req id": "req 1", "bound outcome id":
"{outcome id}", "fields": { "text": "<requirement text>", "type":
"<constraint|preference|ranking|task|other>" }, "creation action ids":
["<action id>"], "contributing action ids": [], "implementation action ids":
[], "related to": [], "explicit or implicit": "<explicit|implicit>", "rationale":
"<why extracted>" } ],
"open_slot ops": [ { "op": "open_slot", "slot id": "slot 1", "bound outcome id":
"{outcome id}", "fields": { "text": "<the hedged, uncertain, or deferred idea>",
"type": "<constraint|preference|ranking|task|other>" }, "origin": "<user|AI>",
"creation action ids": ["<action id>"], "contributing action ids": [],
"related to": [], "explicit or implicit": "<explicit = directly posed as an open
question/uncertainty; implicit = inferred ambiguity nobody named>", "rationale":
"<why substantive but failed Necessity>" } ] }
Use action ids (e.g. "U(3,1)" or "A(3,1)") in creation action ids / contributing
action ids / implementation action ids.

CRITICAL: Respond with ONLY the JSON object. No additional text."""


STEP_3 = """Step 3: Influence Labeling

You are analyzing how actions relate to a single requirement --- both actions BEFORE
and AFTER it was established.

=== OUTCOME CONTEXT ===
Outcome: {outcome description}

=== TARGET REQUIREMENT ===
{req id}: {req text}
(Created at turn {req origin turn})
Origin: <directly created | resolved from open slot>

=== KNOWN SLOT ORIGIN === (include only if Origin = resolved from open slot)
This requirement resolved from open_slot {slot id}, originally raised by
{user|AI} at {slot creation turn}: "{slot text}"
The actions below are confirmed related — a causal link was already established
when this idea was first raised and tracked as an open slot. For each, assign
IMPLICIT CONNECTION with score 3 by default, unless the evidence supports a
stronger or different label. Do not use NO CONNECTION for anything in this list.
{slot's creation + contributing actions, each as: action_id | action_type |
role | action_text | evidence: "quote"}

=== SECTION A: PRECEDING ACTIONS (before the requirement) ===
These are candidate utterances from BEFORE the requirement was established. Any
action already listed under KNOWN SLOT ORIGIN above is excluded from this list.
{preceding block}

=== SECTION B: SUBSEQUENT ACTIONS (after the requirement, same outcome) ===
These actions occurred AFTER the requirement was created, within the same outcome.
{subsequent block}

======================== TASK ========================
For EVERY entry in every section given above, label the relationship to the
requirement.

**relationship type:**
- **DIRECT CONNECTION**: Action explicitly operates on the requirement --- creates,
tightens, relaxes, replaces, deletes, requests, evaluates, or fulfills it. The
requirement is the OBJECT of the action. - **IMPLICIT CONNECTION**: Action
provides context that influences, motivates, or triggers the requirement. Not
directly about the requirement itself. - **IMPLEMENTS**: (Section B only) Action
directly executes, fulfills, or produces output satisfying this requirement. -
**REVISES**: (Section B only) Action modifies, tightens, relaxes, or replaces the
requirement after it was established. - **CONTRIBUTES**: Action provides partial
work, context, or progress toward this requirement. - **NO CONNECTION**: No
meaningful relationship.

**relationship score** (required for DIRECT/IMPLICIT/IMPLEMENTS/REVISES/CONTRIBUTES):
- 1--3 for IMPLICIT CONNECTION or CONTRIBUTES:
  - 3 = Necessary: without this action, the requirement would likely not be
    established in its current form.
  - 2 = Supportive: meaningfully supports the requirement's establishment, but it
    could still be established without it.
  - 1 = Weak: minor or background connection; the requirement would likely still
    be established in a similar form without it.
- 4--5 for DIRECT CONNECTION, IMPLEMENTS, or REVISES (4=explicit, 5=state
  mutation / full fulfillment)
- null for NO CONNECTION

**explanation**: write as "<subtype>: <one-sentence justification>". Use the
following taxonomy as guidance, not as a closed set. The explanation should
reflect the actual actions and content of the conversation rather than merely
repeat the descriptions below.

UNDERSPECIFIED INTENT / PREFERENCE
Goal-Concretization | a prior broad goal later leads to a more concrete requirement
Preference-Explication | a prior implicit preference is later expressed as an
explicit requirement
ARTIFACT-TRIGGERED ELABORATION
Artifact-Triggered-Refinement | a prior artifact later prompts a refinement or
missing requirement
Context-Grounded-Requirement | prior context, code, data, or situational
information later grounds a new requirement
Plan-Driven-Proceduralization | a prior plan or workflow later leads to a
procedural or next-step requirement
PROBLEM-TRIGGERED REVISION
Problem-Triggered-Correction | a prior failure, mismatch, or reported issue later
leads to a corrective requirement
Complexity-Triggered-Simplification | prior complexity, burden, or ambiguity later
leads to a simpler or narrower requirement
INTERACTIONAL STEERING
Option-Selection | prior alternatives are later resolved by selecting one option
Recommendation-Driven-Strategy | a prior request for guidance later leads to a
strategy, priority, or decision requirement
Extension-Driven-Next-Step | a prior invitation to continue later leads to a
concrete next-step requirement
Implementation-Triggered-Setup | a prior implementation request later leads to
added setup, execution, or usage requirements
TEMPORAL AND DIAGNOSTIC DYNAMICS
Incremental-Accumulation | prior preferences, constraints, or decisions accumulate
across turns and later shape the requirement
Hypothesis-And-Diagnosis | a prior causal hypothesis later leads to validation,
testing, or diagnostic requirements

**contribution role**: SHAPER | EXECUTOR | OTHER. Each listed action already
shows a role. If your judgment disagrees with the role shown, note it in
explanation rather than silently changing it.

Default to NO CONNECTION unless clear semantic evidence.

======================== OUTPUT FORMAT ========================
Return JSON only:
{ "slot origin labels": [ { "index": 0, "action id": "<e.g. A(1,34)>",
"relationship type": "IMPLICIT CONNECTION", "relationship score": 3,
"explanation": "...", "contribution role": "AI" } ],
"preceding labels": [ { "index": 0, "action id": "<e.g. 4-1>",
"relationship type": "DIRECT CONNECTION", "relationship score": 5, "explanation":
"...", "contribution role": "SHAPER" } ],
"subsequent labels": [ { "index": 0, "action id": "<e.g. 8-1>",
"relationship type": "IMPLEMENTS", "relationship score": 5, "explanation":
"...", "contribution role": "EXECUTOR" } ] }
Include "slot origin labels" only if a KNOWN SLOT ORIGIN section was given
above. Include one entry for EVERY index in every section present.
Provide ONLY the JSON object. No additional text."""


def fill(template, values):
    """Fill `{name}` placeholders by literal replacement (str.format would
    choke on the prompts' literal JSON braces). Raises if a requested
    placeholder is absent so silent template drift can't happen.
    """
    result = template
    for name, value in values.items():
        token = "{" + name + "}"
        if token not in result:
            raise KeyError(f"placeholder {token!r} not found in template")
        result = result.replace(token, str(value))
    return result
