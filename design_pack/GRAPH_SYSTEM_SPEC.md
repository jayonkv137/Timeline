# CoTrace 3D Graph System Specification

## Step 1: The Root Goal (Origin Anchor)

### 1. Data Source & Fetch Rule
* **File:** `state.json` (or `sample_data/<chat_id>.json`)
* **Path:** `outcomes[]`
* **Fetch Logic:** Find the single object where `parent === null`.
* **Field Used:** `outcome.text`
* **Exact Wording Rule:** Use 100% literal string from `text`. No field names, no IDs (no "outcome 1"), no turn IDs (no "U(1,1)"), no prefixes.

#### Proof from `c05_research_medium`:
```json
{
  "id": "outcome 1",
  "text": "Course assignment strategy and deliverables",
  "parent": null,
  "children": ["outcome 2", "outcome 3", "outcome 4", "outcome 5", "outcome 6"]
}
```

---

### 2. Spatial Anchor Rule
* **Node Position:** Fixed at origin $(0, 0, 0)$.
* **Text Position:** Anchored strictly directly below the node:
  $$X_{\text{label}} = 0$$
  $$Y_{\text{label}} = -R_{\text{node}} - \Delta_{\text{offset}}$$
* **Alignment:** Centered horizontally (`text-align: center`).

---

### 3. Visibility Rule
* **Permanent Visibility:** The Root Goal text is **always visible** across all zoom levels.
* **Zoom Behavior:** Unlike leaf nodes, the root label never fades to 0 opacity when zooming out. Font size maintains a minimum readable floor so orientation is never lost.

---

### 4. Design Intent & Rationale (Owner's Vision)
* **The Session Singularity:** When entering the graph or viewing the system, this node represents the starting point and the parent goal of the entire conversation. It holds the overarching objective of the collaboration.
* **Macro-to-Micro Zoom Hierarchy:** At the macro level (zoomed all the way out, viewing the entire space), the root goal remains clearly readable as the project beacon. As the user zooms in, the finer sub-goals (outcomes) and decisions emerge around it.
* **Visual Distinction:** Because it defines the identity of the entire session, it must have clear structural distinction and stand out prominently from all coming child nodes.

---

### 5. Future Research Vectors (Prototyping Notes)
* **Real-Time Mode Identity Indicator:** In the underlying research paper, interactions are classified into collaboration modes (**Copilot**, **Centaur**, **Cyborg** / **Autopilot**).
* **Dynamic Spherical State:** An exploratory concept for future iterations is using the root sphere to reflect the real-time interaction mode pair-by-pair as the conversation progresses, visually communicating the evolving collaboration dynamic at the center of the graph.

---

## Step 2: Child Outcomes & Connection Lines

### 1. Connection Line Rules
* **Parent-Child Tether (Solid):** Drawn directly from parent node center to child node center when `child.parent === parent.id`. Style: Solid line, 1.4px width, medium opacity (0.45).
* **Cross-Branch Relation (Dashed):** Drawn between nodes listed in `outcome.related[]`. Style: Dashed pattern (5px dash, 5px gap), 1.2px width, subtle opacity (0.35).
* **Unrelated Tangent:** Nodes with `parent === null` and empty `related[]` receive no tether lines and drift freely via repulsive force.

### 2. Node Sizing by Ledger Mass
* Child node radius scales deterministically by total accumulated points from `ledger.jsonl`:
  $$R_{\text{child}} = R_{\text{base}} + \Delta \cdot \left(\frac{M_{\text{child}}}{M_{\text{max}}}\right)$$
* Visual hierarchy: Higher-mass deliverables occupy greater spatial volume.

### 3. Dual Internal Light Emission (Frosted Glass Shell)
* Each child node is rendered as a translucent frosted sphere.
* Two point-light sources reside inside the sphere's core:
  - **User Source:** Cyan/Blue light (`#38bdf8`), intensity proportional to User ledger points.
  - **AI Source:** Orange/Amber light (`#fb923c`), intensity proportional to AI ledger points.
* Photons physically mix inside the frosted diffuser, producing a bright fused white core and an exterior aura reflecting the human-AI energy balance.

### 4. Label Constraints
* Only the exact verbatim text from `outcome.text` is displayed.
* Strictly no IDs (`outcome 2`), turn tags (`U(1,2)`), or numerical score overlays.
* Clamped readability floor ensures labels remain legible during camera navigation.

---

## Step 3: Active Turn Illumination & Pair-State Transitions

### 1. Active vs. Dormant Deliverables (Pair Delta Rule)
* **Activity Test:** At the conclusion of Pair $P$, calculate $\Delta \text{Mass}_P(X)$ from `ledger.jsonl`.
* **Active State ($\Delta \text{Mass}_P(X) > 0$):**
  - Tether lines are **bright and crisp** (white/light-slate, opacity $0.65\text{--}0.75$, 1.4px).
  - Internal photon sources blend actively within the shell.
* **Dormant State ($\Delta \text{Mass}_P(X) = 0$):**
  - Tether lines drop to **subtle neutral gray** (`#334155` / opacity $0.20$).
  - Spheres rest at their current accumulated mass without active pulsation.

### 2. Terminal Active Focus Node (Session Cursor)
* **Identification:** Determined by the final AI action $A(P, \text{last})$ in `state.json` and the last row of `pair_added == P` in `ledger.jsonl`.
* **Visual Beacon:** The terminal deliverable radiates a delicate breathing pulse/halo around its frosted shell, indicating where the conversation is currently resting and awaiting the user's response.

---

## Step 4: Micro-Anatomy & KISS Navigation

### 1. Connection Line Clipping (Outer Circumference Rule)
* **Zero Interior Penetration:** Connection lines (parent tethers, relational cross-links, and satellite orbital tethers) must never cut through the interior volume of any sphere.
* **Vector Offset:** Lines originate and terminate strictly at the outer circumference:
  $$\vec{P}_{\text{start}} = \vec{C}_1 + R_1 \cdot \frac{\vec{C}_2 - \vec{C}_1}{\|\vec{C}_2 - \vec{C}_1\|}$$
  $$\vec{P}_{\text{end}} = \vec{C}_2 - R_2 \cdot \frac{\vec{C}_2 - \vec{C}_1}{\|\vec{C}_2 - \vec{C}_1\|}$$

### 2. Spatial Sector Allocation (Upper Crown Guarantee)
* **Collision-Free Canopy:** All satellite micro-atoms (requirements and open questions) are placed strictly within the upper canopy ($Y < Y_{\text{node}}$ in 2D / $Y > Y_{\text{node}}$ in 3D), maintaining a minimum $45^\circ$ clearance above the deliverable's horizontal equator.
* **Pedestal Text Isolation:** Deliverable text labels are placed strictly beneath the lower hemisphere ($Y > Y_{\text{node}} + R_{\text{node}}$ in 2D / $Y < Y_{\text{node}} - R_{\text{node}}$ in 3D). This spatial separation mathematically guarantees **0% collision** between satellite beads and label text.

### 3. Visual Geometry & Atom Types
* **User Requirement (Solid Bead):** Solid cyan/blue bead (`#38bdf8`, radius 3.5px). Represents an established human constraint or request extracted from `step_2_requirements`.
* **AI Open Question / Slot (Hollow Ring):** Pulsing amber/orange ring (`#fb923c`, radius 4.5px, hollow core). Represents an open fork or question proposed by the AI awaiting user resolution, extracted from `step_2_slots`.
* **State Transition (Pair Resolution):** In subsequent conversation pairs, when the user resolves an open slot, the hollow ring collapses and fills into a solid requirement bead (`req N`).

### 4. Minimalist Tooltip Metaphor (Black + Pop Accent)
* **Visual Palette:** Deep obsidian pitch black background (`#090a0f`), ultra-crisp border with subtle pop accent glow, zero heavy dashboard panels.
* **User Requirement Tooltip:**
  - Header: `USER REQUIREMENT` in pop cyan (`#38bdf8`, 9.5px, uppercase, tracking).
  - Body: Verbatim text from `requirement.text` in crisp white/slate (`#f1f5f9`).
  - Zero Fluff: Strictly no entity IDs (`req 1`), no action tags, no instructional filler text.
* **AI Open Question Tooltip:**
  - Header: `AI OPEN QUESTION` in pop amber (`#fb923c`, 9.5px, uppercase, tracking).
  - Body: Verbatim question text from `slot.text` in white (`#f8fafc`).
  - Options: The exact choice options extracted directly from backend output, indented with an orange accent bar.
  - Zero Fluff: Strictly no entity IDs (`slot 1`), no internal action tags (`A(1,8)`), no quotes, no conversational status badges.

### 5. KISS Chat Navigation (Click to Jump)
* **Direct Jump Interaction:** Clicking any Deliverable sphere, User Requirement bead, or AI Open Question ring navigates directly to the exact corresponding turn in the chat transcript where that element was created or discussed.
* **Minimalist Feedback:** A subtle, temporary floating black-and-accent pill appears at the base of the viewport confirming the chat jump without disrupting the spatial graph view.

---

## Step 5: Deliverable Inception, Atom Provenance & Dynamic Dormancy

### 1. Deliverable Inception (New Node Spawning)
* **Trigger:** When `operations_log` records `op: "create", target_type: "outcome"` in Pair $P$.
* **Connection Rule:** The newly born deliverable connects to the Root Goal via a bright crisp white solid tether (`0xffffff`, opacity 0.65), plus dashed cross-links to any related outcomes specified in `outcome.related[]`.
* **Spatial Sizing:** Node radius scales strictly by accumulated ledger points $\Delta \text{Mass}_P$ from `ledger.jsonl`.

---

### 2. Atom Provenance & Lifecycle (The Concentric History Metaphor)
The graph preserves the complete origin story of every decision through pure geometry, eliminating the need for text-heavy dashboards or confusing historical panels.

```
Pure User Req:     ●  (Solid Cyan Bead)
Pure AI Req:       ●  (Solid Orange Bead)
Open AI Question:  ○  (Hollow Pulsing Orange Ring)
Resolved Decision: ⦿  (Concentric: Resolution Core inside Amber Provenance Ring)
```

* **State A: Pure User Requirement (`●` Solid Cyan Bead):**
  - Dictated directly by human prompt (`U(...)`) without prior AI questioning.
  - Geometry: Solid cyan bead (`#38bdf8`, radius 3.5px).
* **State B: Pure AI Requirement (`●` Solid Orange Bead):**
  - Committed directly by AI (`A(...)`) as a self-imposed technical rule or constraint.
  - Geometry: Solid orange bead (`#fb923c`, radius 3.5px).
* **State C: Active AI Open Question (`○` Hollow Orange Ring):**
  - Fork proposed by AI, actively awaiting user response.
  - Geometry: Hollow pulsing amber ring (`#fb923c`, radius 4.5px).
* **State D: Resolved Decision (`⦿` Concentric Bullseye):**
  - When an open question (`slot N`) is resolved and locked into a permanent requirement (`req N`).
  - **Outer Provenance Ring:** Crisp amber halo (`#fb923c`, radius 5.8px), preserving the historic memory that this atom originated as an AI fork.
  - **Inner Resolution Core:** Solid bead filled with the color of whoever finalized the decision:
    - **Solid Cyan Core (`#38bdf8`):** Human made the choice (e.g. Turn 2 resolution of paper directions).
    - **Solid Orange Core (`#fb923c`):** AI autonomously resolved the choice (autopilot / agentic execution).

---

### 3. Deterministic KISS Tooltip Components (Zero Fluff)

Every tooltip is deterministically mapped 1:1 to pipeline data fields (`slot.text`, `slot.choices[]`, `req.text`), styled in deep pitch-black (`#090a0f`):

#### Component 1: Active Open Question (`○`)
* **Header:** `AI OPEN QUESTION` in glowing amber (`#fb923c`).
* **Question Body:** Verbatim text from `slot.text`.
* **Options Tray:** Indented list with orange accent bar displaying `slot.choices[]`.
* **Status:** Cleanly indicates an active fork awaiting human decision.

#### Component 2: Human-Resolved Decision (`⦿`)
* **Header:** `HUMAN-RESOLVED` in pop cyan (`#38bdf8`) with pill tag `FROM AI QUESTION`.
* **Question Body:** Original question string from `slot.text`.
* **Decision Trace (Accent Bar):**
  - `✓ User Chose: [selected option text]` (in bright cyan).
  - Muted bullet list of alternative options that were offered.
* **Resulting Requirement:** Full verbatim text from `req.text` separated by a subtle divider.

#### Component 3: AI-Resolved Decision (`⦿`)
* **Header:** `AI-RESOLVED` in pop amber (`#fb923c`) with pill tag `FROM AI QUESTION`.
* **Question Body:** Original question string from `slot.text`.
* **Decision Trace (Accent Bar):**
  - `✓ AI Chose: [selected option text]` (in bright amber).
  - Muted bullet list of alternative options.
* **Resulting Requirement:** Full verbatim text from `req.text`.

---

### 4. Dynamic Dormancy Transitions (Pair Delta Rule)
* **Activity Evaluation:** At the conclusion of Pair $P$, evaluate $\Delta \text{Mass}_P(X)$ for every existing outcome.
* **Dormant State ($\Delta \text{Mass} == 0$):**
  - Tether line to Root Origin drops to subtle neutral gray (`#334155`, opacity 0.25).
  - Internal photon emission drops to resting intensity, drawing the eye toward active branches while keeping complete history intact.
* **Reactivation ($\Delta \text{Mass} > 0$):**
  - If a dormant deliverable receives work in a future turn, its tether instantly restores to bright crisp white (`0xffffff`, opacity 0.65).

---

### 5. Terminal Active Focus Cursor
* **Tracking Rule:** A breathing cyan beacon halo strictly orbits the single deliverable associated with the final AI action $A(P, \text{last})$ that holds an active open question or pending user response, establishing an intuitive "You are here" cursor on the graph.

---

## Step 6: Complete Pipeline-to-Graph Field & Function Mapping Matrix

Every visual element, position, color, line style, and interaction in the CoTrace graph is 100% deterministically computed from the backend pipeline output files (`full_export.json`, `state.json`, `ledger.jsonl`, and `dialogue.json`). There are zero hardcoded visual assumptions or hallucinated scores.

### 1. Mathematical Functions & Transformation Rules

#### Function 1: Deliverable Existence & Inception $\mathcal{E}(P)$
Determines which deliverable nodes exist in the graph at Pair $P$:
$$\mathcal{E}(P) = \{ X \in \text{outcomes} \mid \exists p \le P : X \in \text{ledger\_rows}_p \lor X \in \text{operations}_p \}$$
* If an outcome appears for the first time at Pair $P$, its inception status is **Born** (Spawning animation with crisp white tether to Root).

#### Function 2: Cumulative Ledger Mass $\text{Mass}_{\text{cum}}(X, P)$
Computes the true cumulative weight of deliverable $X$ across all turns up to Pair $P$:
$$\text{Mass}_{\text{cum}}(X, P) = \sum_{p=1}^P \sum_{r \in \text{ledger}_p, r.\text{outcome\_id} = X} r.\text{score}$$
$$\text{UserMass}_{\text{cum}}(X, P) = \sum_{p=1}^P \sum_{r \in \text{ledger}_p, r.\text{outcome\_id} = X, r.\text{speaker} = 'U'} r.\text{score}$$
$$\text{AIMass}_{\text{cum}}(X, P) = \sum_{p=1}^P \sum_{r \in \text{ledger}_p, r.\text{outcome\_id} = X, r.\text{speaker} = 'A'} r.\text{score}$$

#### Function 3: Pair Delta Activity & Dormancy $\Delta \text{Mass}_P(X)$
Evaluates whether a deliverable is actively being worked on in Pair $P$ or has fallen dormant:
$$\Delta \text{Mass}_P(X) = \sum_{r \in \text{ledger}_P, r.\text{outcome\_id} = X} r.\text{score}$$
$$\text{State}(X, P) = \begin{cases} \text{Dormant} & \text{if } \Delta \text{Mass}_P(X) = 0 \\ \text{Active} & \text{if } \Delta \text{Mass}_P(X) > 0 \end{cases}$$
* **Dormant Rendering:** Tether color transitions to neutral slate gray (`#334155`), opacity drops to $0.25$, internal photon pulsation ceases.
* **Active Rendering:** Tether color is crisp white/slate (`#f8fafc`), opacity $0.65$, internal photon blending is active.

#### Function 4: Frosted Glass Dual-Photon Emission
Determines the internal lighting ratio inside each frosted sphere:
$$I_{\text{user}}(X) = I_{\text{base}} \cdot \frac{\text{UserMass}_{\text{cum}}(X, P)}{\text{Mass}_{\text{cum}}(X, P)}$$
$$I_{\text{ai}}(X) = I_{\text{base}} \cdot \frac{\text{AIMass}_{\text{cum}}(X, P)}{\text{Mass}_{\text{cum}}(X, P)}$$
* Cyan point source: `#38bdf8` at coordinate $(X_c - 0.2 R, Y_c, Z_c + 0.1 R)$
* Amber point source: `#fb923c` at coordinate $(X_c + 0.2 R, Y_c, Z_c + 0.1 R)$
* The two photon wavelengths physically mix through the frosted scattering shader, producing a pure white specular highlight at the center and an aura tint matching the dominant contributor.

#### Function 5: Vector Circumference Clipping
Guarantees lines start and stop precisely on the outer boundary of spheres with zero interior bleed:
$$\vec{u} = \frac{\vec{C}_{\text{target}} - \vec{C}_{\text{source}}}{\|\vec{C}_{\text{target}} - \vec{C}_{\text{source}}\|}$$
$$\vec{P}_{\text{start}} = \vec{C}_{\text{source}} + R_{\text{source}} \cdot \vec{u}$$
$$\vec{P}_{\text{end}} = \vec{C}_{\text{target}} - R_{\text{target}} \cdot \vec{u}$$

#### Function 6: Micro-Atom Provenance & Discriminator $\mathcal{T}(atom)$
Classifies every satellite atom orbiting an outcome into its exact geometry and color:

$$\mathcal{T}(atom) = \begin{cases} 
\text{Pure User Requirement } (● \text{ Solid Cyan}) & \text{if } atom \in \text{reqs} \land atom.\text{related\_to} = \emptyset \land atom.\text{creation\_action}[0] \in \mathcal{U} \\
\text{Pure AI Requirement } (● \text{ Solid Orange}) & \text{if } atom \in \text{reqs} \land atom.\text{related\_to} = \emptyset \land atom.\text{creation\_action}[0] \in \mathcal{A} \\
\text{Active Open Question } (○ \text{ Hollow Orange Ring}) & \text{if } atom \in \text{slots} \land atom.\text{status} = \text{'open'} \\
\text{Human-Resolved Decision } (⦿ \text{ Bullseye, Cyan Core}) & \text{if } atom \in \text{reqs} \land atom.\text{related\_to} \ne \emptyset \land atom.\text{creation\_action}[0] \in \mathcal{U} \\
\text{AI-Resolved Decision } (⦿ \text{ Bullseye, Orange Core}) & \text{if } atom \in \text{reqs} \land atom.\text{related\_to} \ne \emptyset \land atom.\text{creation\_action}[0] \in \mathcal{A}
\end{cases}$$

#### Function 7: Terminal Active Focus Selector $\mathcal{F}(P)$
Identifies the exact deliverable that holds the conversational cursor at Pair $P$:
$$\mathcal{F}(P) = \text{slot.outcome\_id} \quad \text{where} \quad \text{slot} \in \text{slots}_P \land \text{slot.status} = \text{'open'}$$
* In Pair 1: Outcome 3 holds `slot 1` (created by `A(1,8)`).
* In Pair 2: Outcome 4 holds `slot 1` (created by `A(2,11)`).

---

### 2. Complete Field-to-Field Mapping Matrix

| Graph Visual Element | Visual Property / Attribute | Source File | Pipeline Path / JSON Field | Deterministic Transformation Function |
| :--- | :--- | :--- | :--- | :--- |
| **Root Goal** | Position $(X, Y, Z)$ | `state.json` | Fixed Origin | Fixed at $(0, 0, 0)$ |
| | Label String | `full_export.json` | `step_1_outcomes[parent=null].text` | Verbatim text string (no IDs, no prefixes) |
| | Permanent Visibility | Logic Rule | Invariant Floor | `opacity = max(0.4, 1.0 - zoom * 0.1)` |
| **Child Deliverables** | Existence in Pair $P$ | `full_export.json` | `step_4_pairs[p<=P].ledger_rows` | Present if outcome has $\ge 1$ ledger row up to Pair $P$ |
| | Label String | `full_export.json` | `step_1_outcomes[id=X].text` | Verbatim text string positioned beneath node |
| | Spatial Sizing (Radius $R$) | `ledger.jsonl` | `ledger_rows[outcome=X].score` | $R = R_{\text{base}} + \Delta_R \cdot (\text{Mass}_{\text{cum}} / \text{Mass}_{\text{max}})$ |
| | Dual Photon Light Ratio | `ledger.jsonl` | `ledger_rows[outcome=X].speaker` | $I_{\text{user}} = I_0 \cdot (M_U / M_{\text{total}})$, $I_{\text{ai}} = I_0 \cdot (M_A / M_{\text{total}})$ |
| | Activity State | `ledger.jsonl` | `step_4_pairs[P].ledger_rows` | $\Delta \text{Mass}_P > 0 \rightarrow$ Active; $\Delta \text{Mass}_P = 0 \rightarrow$ Dormant |
| | Parent Tether (Solid) | `full_export.json` | `outcome.parent` | Drawn to `outcome.parent` if non-null |
| | Relational Link (Dashed) | `full_export.json` | `outcome.related[]` | Drawn between $(X, Y)$ if $Y \in X.\text{related}$ |
| | Line Boundary Clipping | Geometry | $\vec{C}_1, R_1, \vec{C}_2, R_2$ | Clipped at outer circumferences using Function 5 |
| | Terminal Beacon Halo | `full_export.json` | `step_4_pairs[P].slots_created` | Pulsing cyan halo on $\mathcal{F}(P)$ (Function 7) |
| **Micro-Atoms** | Position Sector | Geometry | Upper Canopy $(45^\circ \text{--} 135^\circ)$ | $X_a = X_c + r_{\text{orb}} \cos\theta$, $Y_a = Y_c - r_{\text{orb}} \sin\theta$ |
| | Pure User Requirement | `state.json` | `requirements[related_to=[]]` | Solid cyan bead (`#38bdf8`, 3.5px) if creator is User |
| | Pure AI Requirement | `state.json` | `requirements[related_to=[]]` | Solid orange bead (`#fb923c`, 3.5px) if creator is AI |
| | Active Open Question | `state.json` | `slots[status='open']` | Hollow pulsing orange ring (`#fb923c`, 4.5px) |
| | Concentric Bullseye | `state.json` | `requirements[related_to=['slot X']]` | Outer amber ring (`#fb923c`, 5.8px) + Solid resolution core |
| | Bullseye Core Color | `state.json` | `req.creation_action_ids[0]` | Cyan (`#38bdf8`) if User-resolved; Amber (`#fb923c`) if AI-resolved |
| **KISS Tooltips** | Header Tag | Tooltip Engine | `atom.type` + `provenance` | `USER REQUIREMENT`, `AI REQUIREMENT`, or `HUMAN-RESOLVED` |
| | Question String | `state.json` | `slots[slot_id].text` | Verbatim text from original slot definition |
| | Selected Option Trace | `dialogue.json` | `actions[creation_action_id].quote` | Verbatim quote of chosen option prefixed by `✓ User Chose:` |
| | Alternative Options | `dialogue.json` | AI prompt choices for slot | Muted bullet list of unselected choices |
| | Requirement Text | `state.json` | `requirements[req_id].text` | Verbatim text string from requirement record |
| **Chat Navigation** | Direct Click Jump | `dialogue.json` | `creation_action_ids[0]` | Scrolls chat directly to turn where action occurred |

---

### 3. Ground-Truth Data Audit & Mathematical Proof (Pair 1 vs. Pair 2)

#### 1. Outcomes Ledger Mass & Activity Audit
| Outcome ID | Verbatim Deliverable Title | Pair 1 Cumulative | Pair 1 State | Pair 2 Delta & Cumulative | Pair 2 State | Pair 3 Delta & Cumulative | Pair 3 State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **outcome 1** | Course assignment strategy and deliverables | N/A (Root Anchor) | **Origin Anchor** | N/A (Root Anchor) | **Origin Anchor** | N/A (Root Anchor) | **Origin Anchor** |
| **outcome 2** | Initial assignment plan and paper search strategy | User: 19.0, AI: 25.0<br>**Total: 44.0** | **Active**<br>(Crisp tether) | $\Delta = 0.0$<br>**Total: 44.0** | **Dormant**<br>(Gray tether `#334155`) | $\Delta = 0.0$<br>**Total: 44.0** | **Dormant**<br>(Gray tether `#334155`) |
| **outcome 3** | Expanded paper bank and recommendations | User: 8.0, AI: 10.0<br>**Total: 18.0** | **Active**<br>(Holding Slot 1) | $\Delta = 125.0$ (U: 26, A: 99)<br>**Total: 143.0** | **Active (Expanded)**<br>(Slot resolved $\rightarrow$ req 2) | $\Delta = 175.0$ (U: 32, A: 143)<br>**Total: 318.0** | **Hyper-Active (Surge)**<br>(Terminal focus beacon) |
| **outcome 4** | Reading strategy and presentation preparation guide | Does not exist | *Non-existent* | $\Delta = 50.0$ (U: 10, A: 40)<br>**Total: 50.0** | **Active (Born)**<br>(Holding active slot 1) | $\Delta = 0.0$<br>**Total: 50.0** | **Dormant**<br>(Gray tether `#334155`) |

#### 2. Micro-Atom Lifecycle & Provenance Audit
| Outcome | Atom ID | Origin Action | `related_to` | Raw Pipeline Text | Graph Representation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pair 1 · Outcome 2** | `req 1` | `U(1,3)` | `[]` | "The AI must review and understand the user's handwritten notes." | `●` Solid Cyan Bead (`#38bdf8`) |
| **Pair 1 · Outcome 2** | `req 2` | `U(1,3)` | `[]` | "The AI must review the project files and assignment requirements to ground its recommendations in the actual course requirements." | `●` Solid Cyan Bead (`#38bdf8`) |
| **Pair 1 · Outcome 3** | `req 1` | `U(1,2)` | `[]` | "The search for research papers must target papers related to AI creativity and the specified course requirements." | `●` Solid Cyan Bead (`#38bdf8`) |
| **Pair 1 · Outcome 3** | `slot 1` | `A(1,8)` | N/A | "Selection of two specific research directions to guide the paper search." | `○` Hollow Amber Ring (`#fb923c`)<br>*(Terminal Active Cursor)* |
| **Pair 2 · Outcome 3** | `req 1` | `U(1,2)` | `[]` | *(Persisted from Pair 1)* | `●` Solid Cyan Bead (`#38bdf8`) |
| **Pair 2 · Outcome 3** | `req 2` | `['U(2,1)', 'U(2,2)']` | `['slot 1']` | "The selected research papers must bridge both angles (deskilling and creative autonomy/canvas-based tools), with the priority paper for Monday being the closest fit to the user's notes on deskilling and creative autonomy." | `⦿` **Concentric Bullseye**<br>Outer Amber Ring (`#fb923c`) + Solid Cyan Core (`#38bdf8`) |
| **Pair 2 · Outcome 3** | `req 3` | `A(2,6)` | `[]` | "The selected highest-priority paper must be verified as a proper full paper published in a canonical venue (such as ACM CHI) with standard page count." | `●` **Solid Orange Bead** (`#fb923c`)<br>*(Pure AI Requirement)* |
| **Pair 2 · Outcome 4** | `req 1` | `A(2,8)` | `[]` | "The assignment plan and preparation instructions must be delivered in a Markdown document format." | `●` **Solid Orange Bead** (`#fb923c`)<br>*(Pure AI Requirement)* |
| **Pair 2 · Outcome 4** | `req 2` | `A(2,10)` | `[]` | "The document must include preparation instructions for Monday, specifically detailing pulling, printing, and rewriting the Woodruff et al. CHI '24 paper." | `●` **Solid Orange Bead** (`#fb923c`)<br>*(Pure AI Requirement)* |
| **Pair 2 · Outcome 4** | `slot 1` | `A(2,11)` | N/A | "Whether the user will volunteer their own presentation topic or select one of Prof. von Maydell's topics." | `○` Hollow Amber Ring (`#fb923c`)<br>*(Terminal Active Cursor)* |
| **Pair 3 · Outcome 3** | `req 4` | `U(3,2)` | `[]` | "The expanded paper bank must include papers similar to the de-skilling and protosampling papers, with a specific focus on video/filmmaking." | `●` **Solid Cyan Bead** (`#38bdf8`)<br>*(Pure User Requirement)* |
| **Pair 3 · Outcome 3** | `req 5` | `A(3,8)` | `[]` | "The expanded paper bank must be documented with proper citations and confidence tiers." | `●` **Solid Orange Bead** (`#fb923c`)<br>*(Pure AI Requirement)* |
| **Pair 3 · Outcome 4** | `slot 1` | `A(2,11)` | N/A | *(Persists open awaiting topic resolution)* | `○` Hollow Amber Ring (`#fb923c`) |

#### 3. Resolved Slot Decision Trace Audit (Req 2 on Outcome 3)
* **Trigger:** Operation in Pair 2: `{'pair': 2, 'outcome_id': 'outcome 3', 'op': 'resolve', 'target_id': 'slot 1', 'target_type': 'slot'}` followed by `create` of `req 2` with `related_to: ['slot 1']`.
* **Original Slot Question (`slot 1.text`):** *"Selection of two specific research directions to guide the paper search."*
* **AI Offered Choices (from `A(1,8)` in `dialogue.json`):**
  - Angle 1: *Deskilling & Cognitive Erosion in heavy AI users*
  - Angle 2: *Creative Autonomy & Generative User Interfaces / Canvas Tools*
* **User Selection (from `U(2,1)` & `U(2,2)` quotes):**
  - `U(2,1)` quote: *"Both — I want the presentation to bridge them"*
  - `U(2,2)` quote: *"Closest fit to my notes (deskilling + creative autonomy)"*
* **Resulting Locked Requirement (`req 2.text`):**
  *"The selected research papers must bridge both angles (deskilling and creative autonomy/canvas-based tools), with the priority paper for Monday being the closest fit to the user's notes on deskilling and creative autonomy."*
* **KISS Tooltip Verification:**
  - Header: `HUMAN-RESOLVED` `[FROM AI QUESTION]`
  - Body: Shows the original question.
  - Trace: `✓ User Chose: Bridge both angles (Angle 1 + Angle 2)`
  - Divider + Resulting requirement text.
  - 100% verified against raw pipeline data with zero hallucination.

---

### 4. Interactive Bottom Timeline Scrubber Specification

#### 1. Visual Capsule Architecture
* **Placement:** Floating horizontally centered at the bottom of the viewport (`bottom: 22px; left: 50%; transform: translateX(-50%)`).
* **Design Metaphor:** Frosted obsidian glass capsule (`rgba(9, 10, 15, 0.92)` with `backdrop-filter: blur(20px)` and subtle border `1px solid rgba(255, 255, 255, 0.16)`).
* **Track & Progress Fill:**
  - Base Rail: 4px height, subtle slate line (`rgba(255, 255, 255, 0.12)`).
  - Progress Fill: Gradient from cyan to amber (`linear-gradient(90deg, #38bdf8, #fb923c)`), scaling width smoothly by $\frac{P - 1}{P_{\text{max}} - 1} \times 100\%$.
* **Step Notches:**
  - 7 discrete notches placed along a 360px rail corresponding to Pairs 1 through 7:
    $$\text{Position}(P) = \frac{P - 1}{6} \times 100\% \quad \text{for } P \in \{1, 2, 3, 4, 5, 6, 7\}$$
  - Inactive Notch: Dark bead (`#1e293b`) with muted gray border (`#64748b`).
  - Active Notch: Solid cyan core (`#38bdf8`) with white border and subtle glow.
  - Current Notch: Glowing amber core (`#fb923c`) with breathing pulse and prominent label (`P1` .. `P7`).
* **Controls & Keybindings:**
  - Previous (`◀`) and Next (`▶`) tactile circular buttons with hover feedback and automatic bounds disabling.
  - Full Keyboard Arrow Support: Pressing `ArrowLeft` or `ArrowRight` immediately scrubs between pairs.
  - Live Metric Pill: Real-time badge indicating current pair cumulative ledger mass and deliverable state breakdown.

#### 2. Complete 7-Pair Deterministic State Transition Matrix
| Scrubber Step | Active Deliverables ($\Delta M_P > 0$) | Dormant Deliverables ($\Delta M_P = 0$) | Cumulative Total Mass | Terminal Active Focus $\mathcal{F}(P)$ | Conversational Trajectory & Visual Dynamics |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pair 1** | Outcome 2 ($M=44$), Outcome 3 ($M=18$) | *None* | **62.0** | Outcome 3 (`A(1,8)`) | Genesis. Root anchors at $(0,0,0)$. 3 pure user reqs (`●` Cyan), 1 open slot (`○` Hollow Orange Ring). |
| **Pair 2** | Outcome 3 ($M=143$), Outcome 4 ($M=50$) | Outcome 2 ($M=44$) | **237.0** | Outcome 4 (`A(2,11)`) | Outcome 4 is born; Outcome 2 tether drops to neutral slate gray (`#334155`, 0.25). Outcome 3 slot 1 resolves into concentric bullseye `req 2` (`⦿`). |
| **Pair 3** | Outcome 3 ($M=318$) | Outcome 2 ($M=44$), Outcome 4 ($M=50$) | **412.0** | Outcome 3 (`A(3,12)`) | Outcome 3 hyper-surges (+175 mass) with 5 micro-atoms (video/filmmaking focus). Outcome 4 tether drops to gray. Active focus halo returns to Outcome 3. |
| **Pair 4** | Outcome 5 ($M=213$) | Outcome 2, Outcome 3, Outcome 4 | **625.0** | Outcome 5 (`A(4,8)`) | **Outcome 5 is born** at $(-38, -32, 14)$ with 3 requirements on late 2025/2026 literature. Outcomes 2, 3, 4 tethers are dormant slate gray. Active halo on Outcome 5. |
| **Pair 5** | Outcome 5 ($M=507$) | Outcome 2, Outcome 3, Outcome 4 | **919.0** | Outcome 5 (`A(5,9)`) | **Outcome 5 hyper-surges** (+294 mass, $R=16.5$) with 6 micro-atoms (Casacuberta comparative analysis for presentation). Dual photon lights expand. Active halo on Outcome 5. |
| **Pair 6** | Outcome 6 ($M=130$) | Outcome 2, Outcome 3, Outcome 4, Outcome 5 | **1049.0** | Outcome 6 (`A(6,5)`) | **Outcome 6 is born** at $(36, -34, -16)$ with 3 user requirements (reading strategy for 'Disembodied Creativity'). Outcome 5 tether drops to dormant gray. Active halo on Outcome 6. |
| **Pair 7 (Final)** | **Outcome 4 ($M=138$) [REACTIVATED]** | Outcome 2, Outcome 3, Outcome 5, Outcome 6 | **1137.0** | Outcome 4 (`A(7,11)`) | **Outcome 4 REACTIVATES from dormancy** ($\Delta = 88.0$). Tether RE-ILLUMINATES from slate gray back to crisp white (`#ffffff`, 0.85). Radius expands to 10.8. Added `req 3` (3-act delivery structure). |

---

### 5. Architectural & Design Evaluation: The 6 Trajectory Edge Cases & The KISS Rule

#### 1. Analysis of the 6 Trajectory Edge Cases
1. **Mid-Session Deliverable Inception (Pairs 2, 4, 6):**
   - Deliverables are not statically pre-allocated. Outcome 4 appears in Pair 2, Outcome 5 in Pair 4, and Outcome 6 in Pair 6.
   - *Design Verdict:* Nodes emerge dynamically when their cumulative ledger mass becomes $> 0$. Tethers smoothly draw from the Root Origin anchor.
2. **Deliverable Dormancy ($\Delta \text{Mass}_P = 0$):**
   - Outcomes often pause while conversational focus shifts (Outcome 2 dormant P2–P7, Outcome 3 dormant P4–P7, Outcome 5 dormant P6–P7).
   - *Design Verdict:* Inactive deliverables must not vanish (which would induce spatial disorientation). Instead, their connecting tethers attenuate to neutral slate gray (`#334155`, opacity 0.25) and sphere luminosity dims to ambient idle, preserving the mental spatial map.
3. **Reactivation from Dormancy (Pair 7 Outcome 4):**
   - After sitting dormant through Pairs 3, 4, 5, and 6, Outcome 4 receives a massive update (+88.0 mass) in the final pair.
   - *Design Verdict:* Tethers are fully dynamic. Outcome 4's tether instantaneously re-illuminates from slate gray back to radiant crisp white (`#ffffff`, 0.85), proving the graph is a live state-machine rather than a static snapshot.
4. **Slot Abandonment (Pairs 4 & 5):**
   - `slot 1` on Outcome 1 (abandoned in P4) and `slot 1` on Outcome 4 (abandoned in P5 when user chose the Casacuberta paper instead of seminar topics).
   - *Design Verdict:* Abandoned slots cleanly dissolve and fade out from the canopy; only active or resolved slots are rendered.
5. **Slot Resolution into Concentric Bullseye (Pair 2 Outcome 3):**
   - When an open question (`slot 1`) is answered, it morphs into `req 2` with `related_to: ['slot 1']`.
   - *Design Verdict:* Rendered as a concentric bullseye (`⦿` outer amber ring `#fb923c` + inner cyan core `#38bdf8`), honoring its question ancestry while celebrating user resolution.
6. **Multi-Outcome Turnover (Pairs 1 & 2):**
   - Turns in the pipeline frequently touch multiple deliverables simultaneously (Pair 1 touches O2 & O3; Pair 2 touches O3 & O4).

#### 2. User Design Inquiry: Should Deliverable Nodes Display a "Highlighting Note / Turn Summary"?
* **The Proposal:** Display a floating summary note on hover or over the latest deliverable node stating what happened in the turn or what is going to happen next.
* **KISS & Systems Architecture Evaluation:**
  1. **Category Error (Deliverable vs. Turn Event):**
     A deliverable node represents an *Artifact / Outcome* (a persistent noun, e.g. "Reading strategy and presentation preparation guide"). A turn summary is an *Event / Activity* (a transient verb, e.g. "Drafted CHI 24 reading plan"). Attaching turn events to deliverable spheres conflates artifacts with actions and breaks completely when a single pair touches multiple deliverables.
  2. **Violates KISS Simplicity:**
     Overlaying multi-sentence prose or summary boxes onto 3D spheres introduces visual noise, occludes neighboring satellites, and turns a sleek knowledge graph into a cluttered dashboard.
  3. **The Clean, Deterministic Solution:**
     - **Deliverable Spheres:** Strictly preserve the pure artifact identity (verbatim title + mass + photon beads).
     - **Micro-Atoms:** Hold the atomic requirements and resolved slot histories in concise tooltips.
     - **Terminal Active Focus Beacon ("You Are Here"):** The pulsing halo surrounds the single deliverable receiving the conversational cursor, with the bottom status badge and top brand capsule displaying the deterministic $\le 5$-word milestone summary (e.g., `Pair 7 · Mass 1137 (O4 Reactivated)`).
     - **Timeline Scrubber:** Enables instantaneous, zero-friction time-travel across all 7 pairs with notches and keyboard arrow keys, making turn-by-turn evolution immediately intuitive without textual clutter.
---

### Phase 7: Universal Multi-Chat Architecture (All 12 Real Pipeline Chats)

The CoTrace graph visualizer has been expanded from a single benchmark to a universal, fully data-driven engine supporting **all 12 chats** available in `design_pack/sample_data/` and `data/chats/`.

#### 1. Available Chats Catalog & Metrics

| Chat ID | Domain | Total Pairs | Deliverable Canopy | Genesis Mass | Final Mass | Key Dynamics |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `c05_research_medium` | Research | 7 | 5 children | 62 | 1137 | Multi-surge, Casacuberta deep dive, O4 reactivation |
| `golden_01` | Video Design | 7 | 4 children | 16 | 446 | Attenborough narrative, late deliverable branching |
| `c04_writing_short` | Writing | 4 | 4 children | 40 | 375 | Design system interaction modes, O5 born & surging |
| `c07_research_short` | Research | 4 | 3 children | 22 | 312 | Open slot epistemology, conceptual refinement |
| `c03_coding_short` | Coding | 3 | 3 children | 40 | 248 | 3D interactive portfolio website, rapid surge |
| `c20_coding_short` | Coding | 3 | 3 children | 97 | 313 | Figma migration audit (Phase 9), O4 born |
| `c27_creative_short` | Creative | 2 | 3 children | 53 | 152 | Jellyfish animation prompts, prompt bank expansion |
| `c30_creative_short` | Creative | 2 | 2 children | 49 | 220 | Language learning video system & content pipeline |
| `c10_research_short` | Research | 1 | 3 children | 91 | 91 | Genesis benchmark: Project contribution breakdown |
| `c16_research_short` | Research | 1 | 3 children | 61 | 61 | Genesis benchmark: Co-creative panel evaluation |
| `c17_research_short` | Research | 1 | 1 child | 10 | 10 | Genesis benchmark: Datafied Society research topics |
| `fixture_pair1` | Synthesis | 1 | 5 children | 275 | 275 | Genesis benchmark: Style DNA & Production Bible |

#### 2. Compiler Architecture (`compile_all_chats.js`)
* **Single Source of Truth:** `compile_all_chats.js` processes all 12 raw JSON logs and emits `all_chats_data.js` (373 KB).
* **Deterministic Layout Invariant:** Deliverable coordinates in 2D and 3D remain spatially locked across all pairs  \in [1, P_{\text{max}}]$, eliminating node jitter when deliverables appear or go dormant.
* **Turn Deltas & Lifecycle Tagging:** Each pair calculates:
  - $\text{Mass}_{\text{total}} = \sum M_{\text{child}}$ (or {\text{root}}$ if canopy is genesis).
  - Event tags: `Genesis`, `[Outcome] Born`, `[Outcome] Reactivated`, or `[Outcome] Surge`.
  - Terminal focus deliverable $\mathcal{F}(P)$ receiving the active beacon cursor.

#### 3. Dual-View Synchronization & Scrubber
* **Seamless View Switching:** Both `playground_obsidian.html` and `playground_3d.html` include top-bar dropdowns populated dynamically with all 12 chats.
* **Deep-Linking & Cross-View Sync:** Switching between 2D and 3D carries URL query parameters (`?chat=<id>&pair=<num>`), synchronizing conversational state seamlessly.
* **Elastic Scrubber Notches:** The floating bottom timeline scrubber dynamically scales its rail width and generates exact notches  \dots P_N$ corresponding to each chat's total pairs. Single-pair benchmarks render a single centered notch with 100% progress fill and disabled navigation arrows.
