import { useState, useRef, useEffect, useMemo } from "react";
import { Plus, Send, MessageSquare, Trash2, Menu, X, Paperclip, ArrowDown } from "lucide-react";


type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: number;
  attachment?: { name: string; src: string };
};

type Conversation = {
  id: string;
  title: string;
  titleFinal: string;
  shortTitle: string;
  messages: Message[];
  pairs: PairRow[];
  ts: number;
  goalTree?: GoalTreeNode[];       // the persistent §4 outcome tree
  pairGoals?: PairGoal[];          // per-pair lit node, indexed like `pairs`
};

const T = Date.now();
const min = (n: number) => T - n * 60000;

/* ─── Agency data model ───────────────────────────────────────────────────── */

type GoalNode = {
  label: string;
  isCurrent?: boolean;
  isSideTrack?: boolean; // new branch not nested under previous
};

// §4 goal-hierarchy model: one tree per chat (STATE persists), each pair lights one node.
type GoalTreeNode = {
  id: string;
  label: string;
  parentId: string | null; // null = root (rendered as the chat title)
  kind?: "side"; // §4.7 side-track: hangs off root, dashed ⤳, never an ancestor of work
};

type PairGoal = {
  currentNodeId: string;   // §4.3 R-LEAF: the one node this pair is working on
  relatesTo?: string;      // §4.4 back-ref: this pair re-opens an existing outcome
};

type BarLen = "small" | "medium" | "large";

type PairSnapshot = {
  currentGoal: string;
  goalThread: GoalNode[]; // ordered path from closest ancestor → current goal
  // Direction — C(t,you)/(C(t,you)+C(t,AI)) cumulative snapshot (authored for demo)
  youPct: number;
  aiPct: number;
  // Decisions — count of requirements created, grouped by earliest-creation speaker
  decisionsYou: number;
  decisionsAI: number;
  latestAIDecision?: string; // most recent AI-created requirement text, clause-truncated
  // HOW axis
  analogy: string;
  modeSplit: { driving: number; together: number; backseat: number };
  // legacy fields kept for backward compat (unused in new design)
  aiIdeaCount?: number;
  ideaCardText?: string;
};

type PairRow = {
  id: string;
  side: "YOU" | "AI" | "BOTH";
  length: BarLen;
  // For two-tone (BOTH) rows: independent blue-left / orange-right lengths.
  // Falls back to `length` for both halves when omitted.
  leftLen?: BarLen;
  rightLen?: BarLen;
  topic: string;
  msgId: string;
  shapedBy: "You" | "AI" | "Both";
  snap: PairSnapshot;
};

/* Chat 1 — "You Drove": user diagnoses and decides; AI assists. Bars lean LEFT/blue. */
const CHAT_1_PAIRS: PairRow[] = [
  {
    id: "P1", side: "YOU", length: "medium", topic: "fixing the input bug", msgId: "m1u", shapedBy: "You",
    snap: {
      currentGoal: "Diagnose why input value isn't updating",
      goalThread: [
        { label: "Diagnose the input issue", isCurrent: true },
      ],
      youPct: 100, aiPct: 0, decisionsYou: 1, decisionsAI: 0,
      analogy: "You're driving — the AI's reading you the map.",
      modeSplit: { driving: 100, together: 0, backseat: 0 },
    },
  },
  {
    id: "P2", side: "YOU", length: "medium", topic: "redirecting the diagnosis", msgId: "m2u", shapedBy: "You",
    snap: {
      currentGoal: "Find the real bug — the state mutation",
      goalThread: [
        { label: "Diagnose the input issue" },
        { label: "Find the state mutation", isCurrent: true },
      ],
      youPct: 96, aiPct: 4, decisionsYou: 2, decisionsAI: 0,
      analogy: "You're driving — the AI's reading you the map.",
      modeSplit: { driving: 100, together: 0, backseat: 0 },
    },
  },
  {
    id: "P3", side: "YOU", length: "medium", topic: "rejecting the spread approach", msgId: "m3u", shapedBy: "You",
    snap: {
      currentGoal: "Pick the right update pattern for 30 fields",
      goalThread: [
        { label: "Diagnose the input issue" },
        { label: "Pick the update pattern", isCurrent: true },
      ],
      youPct: 88, aiPct: 12, decisionsYou: 3, decisionsAI: 1, latestAIDecision: "use spread or functional update for the 30-field form",
      analogy: "You're driving — the AI's reading you the map.",
      modeSplit: { driving: 83, together: 17, backseat: 0 },
    },
  },
  {
    id: "P4", side: "YOU", length: "medium", topic: "choosing the functional update", msgId: "m4u", shapedBy: "You",
    snap: {
      currentGoal: "Fix checkbox sending 'on' instead of true/false",
      goalThread: [
        { label: "Diagnose the input issue" },
        { label: "Pick the update pattern" },
        { label: "Fix checkbox bug", isCurrent: true },
      ],
      youPct: 87, aiPct: 13, decisionsYou: 3, decisionsAI: 2, latestAIDecision: "read e.target.checked for checkboxes, not .value",
      analogy: "You're driving — the AI's reading you the map.",
      modeSplit: { driving: 83, together: 17, backseat: 0 },
    },
  },
  {
    id: "P5", side: "YOU", length: "small", topic: "catching the AI's wrong call", msgId: "m5u", shapedBy: "You",
    snap: {
      currentGoal: "Call out the AI's wrong first diagnosis",
      goalThread: [
        { label: "Call out AI's error", isCurrent: true, isSideTrack: true },
      ],
      youPct: 93, aiPct: 7, decisionsYou: 4, decisionsAI: 2, latestAIDecision: "read e.target.checked for checkboxes, not .value",
      analogy: "You're driving — the AI's reading you the map.",
      modeSplit: { driving: 83, together: 12, backseat: 5 },
    },
  },
  {
    id: "P6", side: "YOU", length: "small", topic: "skipping debounce — my call", msgId: "m6u", shapedBy: "You",
    snap: {
      currentGoal: "Skip debounce on onChange",
      goalThread: [
        { label: "Skip debounce", isCurrent: true },
      ],
      youPct: 95, aiPct: 5, decisionsYou: 5, decisionsAI: 2, latestAIDecision: "read e.target.checked for checkboxes, not .value",
      analogy: "You're driving — the AI's reading you the map.",
      modeSplit: { driving: 83, together: 12, backseat: 5 },
    },
  },
];

/* Chat 2 — "AI Drove": vague handoff, AI authors everything; small blue nudges.
   Bars lean RIGHT/orange, front-loaded (P1 large = AI wrote the whole letter). */
const CHAT_2_PAIRS: PairRow[] = [
  {
    id: "P1", side: "AI", length: "large", topic: "AI wrote the whole letter", msgId: "c2m1u", shapedBy: "AI",
    snap: {
      currentGoal: "Get a cover letter written from a one-line ask",
      goalThread: [
        { label: "Write the cover letter", isCurrent: true },
      ],
      youPct: 10, aiPct: 90, decisionsYou: 0, decisionsAI: 1, latestAIDecision: "write a three-paragraph letter built around your five years in social media and email",
      analogy: "You're in the back seat — the AI's driving.",
      modeSplit: { driving: 10, together: 0, backseat: 90 },
    },
  },
  {
    id: "P2", side: "AI", length: "medium", topic: "AI expanded it (+1 para)", msgId: "c2m3u", shapedBy: "AI",
    snap: {
      currentGoal: "Make the letter longer",
      goalThread: [
        { label: "Write the cover letter" },
        { label: "Make it longer", isCurrent: true },
      ],
      youPct: 16, aiPct: 84, decisionsYou: 0, decisionsAI: 2, latestAIDecision: "add a data-informed paragraph about owning a channel end to end",
      analogy: "You're in the back seat — the AI's driving.",
      modeSplit: { driving: 14, together: 0, backseat: 86 },
    },
  },
  {
    id: "P3", side: "AI", length: "medium", topic: "AI authored the hook", msgId: "c2m4u", shapedBy: "AI",
    snap: {
      currentGoal: "Sharpen the opening line",
      goalThread: [
        { label: "Write the cover letter" },
        { label: "Sharpen the opening", isCurrent: true },
      ],
      youPct: 20, aiPct: 80, decisionsYou: 0, decisionsAI: 3, latestAIDecision: "open with 'the hardest part of early-stage marketing' hook",
      analogy: "You're in the back seat — the AI's driving.",
      modeSplit: { driving: 16, together: 0, backseat: 84 },
    },
  },
  {
    id: "P4", side: "AI", length: "small", topic: "AI suggested metrics (declined)", msgId: "c2m5u", shapedBy: "AI",
    snap: {
      currentGoal: "Decide if it's ready to send",
      goalThread: [
        { label: "Write the cover letter" },
        { label: "Decide if it's ready", isCurrent: true },
      ],
      youPct: 24, aiPct: 76, decisionsYou: 0, decisionsAI: 4, latestAIDecision: "add one concrete metric and one Lumen-specific detail",
      analogy: "You're in the back seat — the AI's driving.",
      modeSplit: { driving: 22, together: 6, backseat: 72 },
    },
  },
  {
    id: "P5", side: "AI", length: "medium", topic: "AI wrote the email", msgId: "c2m6u", shapedBy: "AI",
    snap: {
      currentGoal: "Write the accompanying email",
      goalThread: [
        { label: "Write the cover letter" },
        { label: "Write the accompanying email", isCurrent: true },
      ],
      youPct: 25, aiPct: 75, decisionsYou: 0, decisionsAI: 5, latestAIDecision: "send a two-sentence cover email, subject: Marketing Manager Application",
      analogy: "You're in the back seat — the AI's driving.",
      modeSplit: { driving: 20, together: 0, backseat: 80 },
    },
  },
];

/* Chat 3 — "Real Collaboration": back-and-forth co-creation. Rows are TWO-TONE
   (blue-left + orange-right meeting at the spine); P5 is the largest, the co-created
   core. Woven column, ~50/50, no long single-color run. */
const CHAT_3_PAIRS: PairRow[] = [
  {
    id: "P1", side: "BOTH", length: "medium", leftLen: "medium", rightLen: "medium",
    topic: "framing the problem + first angles", msgId: "c3m1u", shapedBy: "Both",
    snap: {
      currentGoal: "Frame the problem & surface possible angles",
      goalThread: [
        { label: "Explore possible angles", isCurrent: true },
      ],
      youPct: 50, aiPct: 50, decisionsYou: 1, decisionsAI: 1, latestAIDecision: "productivity's crowding is mostly in tips/tools; emotional side is wide open",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 30, together: 60, backseat: 10 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
  {
    id: "P2", side: "BOTH", length: "medium", leftLen: "medium", rightLen: "small",
    topic: "redirecting to sustainable pace", msgId: "c3m2u", shapedBy: "Both",
    snap: {
      currentGoal: "Land the lane on 'sustainable pace'",
      goalThread: [
        { label: "Explore possible angles" },
        { label: "Land on 'sustainable pace'", isCurrent: true },
      ],
      youPct: 56, aiPct: 44, decisionsYou: 2, decisionsAI: 1, latestAIDecision: "productivity's crowding is mostly in tips/tools; emotional side is wide open",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 34, together: 56, backseat: 10 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
  {
    id: "P3", side: "BOTH", length: "medium", leftLen: "medium", rightLen: "medium",
    topic: "sharpening to 'already burned out'", msgId: "c3m3u", shapedBy: "Both",
    snap: {
      currentGoal: "Sharpen the reader to post-burnout recovery",
      goalThread: [
        { label: "Explore possible angles" },
        { label: "Sharpen the reader", isCurrent: true },
      ],
      youPct: 52, aiPct: 48, decisionsYou: 3, decisionsAI: 2, latestAIDecision: "for ambitious people who refuse to burn out — threads between hustle and wellness",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 32, together: 58, backseat: 10 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
  {
    id: "P4", side: "BOTH", length: "medium", leftLen: "medium", rightLen: "medium",
    topic: "reacting to names, pivot to 'pace'", msgId: "c3m4u", shapedBy: "Both",
    snap: {
      currentGoal: "Riff on names around 'pace'",
      goalThread: [
        { label: "Riff on names", isCurrent: true, isSideTrack: true },
      ],
      youPct: 50, aiPct: 50, decisionsYou: 3, decisionsAI: 3, latestAIDecision: "Pace implies control and sustainability — stronger than Steady or Cadence",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 30, together: 58, backseat: 12 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
  {
    id: "P5", side: "BOTH", length: "large", leftLen: "large", rightLen: "large",
    topic: "co-created the 'subtraction' core", msgId: "c3m6u", shapedBy: "Both",
    snap: {
      currentGoal: "Make 'subtraction' the whole concept",
      goalThread: [
        { label: "Define the core concept", isCurrent: true },
      ],
      youPct: 50, aiPct: 50, decisionsYou: 4, decisionsAI: 4, latestAIDecision: "subtraction as the entire brand — burnout is addition, recovery is subtraction",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 26, together: 64, backseat: 10 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
  {
    id: "P6", side: "BOTH", length: "medium", leftLen: "small", rightLen: "medium",
    topic: "stress-testing if it has legs", msgId: "c3m7u", shapedBy: "Both",
    snap: {
      currentGoal: "Prove it has a year+ of range",
      goalThread: [
        { label: "Define the core concept" },
        { label: "Stress-test the range", isCurrent: true },
      ],
      youPct: 46, aiPct: 54, decisionsYou: 4, decisionsAI: 5, latestAIDecision: "five buckets (habits, commitments, beliefs, inputs, obligations) — past a year before repeating",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 28, together: 57, backseat: 15 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
  {
    id: "P7", side: "BOTH", length: "medium", leftLen: "medium", rightLen: "medium",
    topic: "debating the final name", msgId: "c3m8u", shapedBy: "Both",
    snap: {
      currentGoal: "Choosing the name",
      goalThread: [
        { label: "Define the core concept" },
        { label: "Choose the name", isCurrent: true, isSideTrack: true },
      ],
      youPct: 50, aiPct: 50, decisionsYou: 5, decisionsAI: 5, latestAIDecision: "five buckets (habits, commitments, beliefs, inputs, obligations) — past a year before repeating",
      analogy: "You and the AI are figuring out the route together.",
      modeSplit: { driving: 28, together: 58, backseat: 14 },
      ideaCardText: "of your choices were shaped with the AI",
    },
  },
];

const CHAT_1: Conversation = {
  id: "conv-1",
  title: "React Form Debug Investigation",
  titleFinal: "React Form Debug Investigation",
  shortTitle: "React Form Debug",
  ts: min(28),
  pairs: CHAT_1_PAIRS,
  goalTree: [
    { id: "root", label: "React Form Debug", parentId: null },
    { id: "c1", label: "Get the form updating", parentId: "root" },
    { id: "c1a", label: "Diagnose the state bug", parentId: "c1" },
    { id: "c1a1", label: "Spot the mutation", parentId: "c1a" },
    { id: "c1a2", label: "Fix checkbox handling", parentId: "c1a" },
    { id: "c1b", label: "Choose the update pattern", parentId: "c1" },
    { id: "s1", label: "Call out AI's wrong first call", parentId: "root", kind: "side" },
    { id: "c2", label: "Skip debounce", parentId: "root" },
  ],
  // depth path: P1 d1 · P2 d2 · P3 d2 · P4 d3 (ellipsis) · P5 side-track · P6 d1
  pairGoals: [
    { currentNodeId: "c1" },
    { currentNodeId: "c1a" },
    { currentNodeId: "c1b" },
    { currentNodeId: "c1a2" },
    { currentNodeId: "s1" },
    { currentNodeId: "c2" },
  ],
  messages: [
    {
      id: "m1u",
      role: "user",
      content: "my form input isn't updating when i type. the value just stays empty. here's the component:\n\nfunction ProfileForm() {\n  const [formData, setFormData] = useState({ name: \"\", email: \"\", bio: \"\" });\n  const handleChange = (e) => {\n    formData[e.target.name] = e.target.value;\n    setFormData(formData);\n  };\n  return <input name=\"name\" value={formData.name} onChange={handleChange} />;\n}\n\nwhat am i missing?",
      ts: min(28),
    },
    {
      id: "m1a",
      role: "assistant",
      content: "A couple of things could cause this. The most common is that the input isn't wired as a controlled component — make sure each input has both `value` and `onChange`. Can you confirm the `onChange` is firing at all (drop a console.log in `handleChange`)?",
      ts: min(26),
    },
    {
      id: "m2u",
      role: "user",
      content: "no the onChange is there, look at the code — `onChange={handleChange}` is on the input. and yeah the log fires, i see it on every keystroke. the handler runs, the value just doesn't change on screen.",
      ts: min(24),
    },
    {
      id: "m2a",
      role: "assistant",
      content: "Got it — then it's not a controlled-component wiring issue, it's the state update itself. Two bugs in `handleChange`: you're mutating the existing `formData` object directly (`formData[e.target.name] = ...`) and then passing the *same* object reference to `setFormData`. React compares by reference, sees the same object, and skips the re-render. You need a new object:\n\n```js\nconst handleChange = (e) => {\n  setFormData({ ...formData, [e.target.name]: e.target.value });\n};\n```",
      ts: min(23),
    },
    {
      id: "m3u",
      role: "user",
      content: "ok that makes sense, the reference thing. but i don't love spreading the whole object on every keystroke — this form actually has like 30 fields, not 3. is there a cleaner pattern or is spread fine?",
      ts: min(20),
    },
    {
      id: "m3a",
      role: "assistant",
      content: "Spread is genuinely fine performance-wise even at 30 fields — it's a shallow copy, it's cheap. But if you want it cleaner, two options: (1) `useReducer` with a single `UPDATE_FIELD` action, or (2) keep the functional update so you're not closing over stale state: `setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))`. That last one is the smallest change and also fixes a stale-closure bug you'd hit with rapid typing.",
      ts: min(19),
    },
    {
      id: "m4u",
      role: "user",
      content: "yeah give me the functional one, i don't want to bring in a reducer for this. let me try it. ... ok that works now for the text fields. but my checkbox is broken now — it's sending \"on\" instead of true/false.",
      ts: min(16),
    },
    {
      id: "m4a",
      role: "assistant",
      content: "Right — checkboxes don't use `e.target.value`, they use `e.target.checked`. You'll need to branch on the input type:\n\n```js\nconst handleChange = (e) => {\n  const value = e.target.type === \"checkbox\" ? e.target.checked : e.target.value;\n  setFormData(prev => ({ ...prev, [e.target.name]: value }));\n};\n```",
      ts: min(15),
    },
    {
      id: "m5u",
      role: "user",
      content: "that's it, fixed. though just noting — your first answer about it being a controlled-component issue was a red herring, it was never that, it was the mutation. would've saved a step if we'd looked at the handler first.",
      ts: min(10),
    },
    {
      id: "m5a",
      role: "assistant",
      content: "Fair point — you're right, I should have read the handler before suggesting the controlled-component check. The mutation was the actual bug from the start.",
      ts: min(9),
    },
    {
      id: "m6u",
      role: "user",
      content: "one more thing then i'm done — should i debounce the onChange, or is that overkill for a form this size?",
      ts: min(5),
    },
    {
      id: "m6a",
      role: "assistant",
      content: "For a form that's just updating local state on keystroke, debouncing is overkill — it adds latency to the typing feel for no real benefit. You'd only want it if each change triggered something expensive (a network call, a heavy re-render of a big tree). Is anything firing off the change beyond the state update?",
      ts: min(4),
    },
    {
      id: "m7u",
      role: "user",
      content: "nope, just local state, it's an internal admin tool. then i'll skip it, perf doesn't matter here. thanks, all sorted.",
      ts: min(2),
    },
  ],
};

const CHAT_2: Conversation = {
  id: "conv-2",
  title: "Cover Letter — Lumen",
  titleFinal: "Cover Letter — Lumen",
  shortTitle: "Cover letter for Lumen",
  ts: min(80),
  pairs: CHAT_2_PAIRS,
  goalTree: [
    { id: "root", label: "Cover letter for Lumen", parentId: null },
    { id: "d1", label: "Draft the letter", parentId: "root" },
    { id: "d1a", label: "Expand the letter", parentId: "d1" },
    { id: "d1b", label: "Sharpen the opening", parentId: "d1" },
    { id: "d2", label: "Decide if it's ready", parentId: "root" },
    { id: "d3", label: "Write the accompanying email", parentId: "root" },
  ],
  // shallow / linear — no ellipsis, no side-track, no sibling overflow
  pairGoals: [
    { currentNodeId: "d1" },
    { currentNodeId: "d1a" },
    { currentNodeId: "d1b" },
    { currentNodeId: "d2" },
    { currentNodeId: "d3" },
  ],
  messages: [
    {
      id: "c2m1u",
      role: "user",
      content: "can you write me a cover letter for a marketing manager role at a startup called Lumen? i'm applying tomorrow",
      ts: min(80),
    },
    {
      id: "c2m1a",
      role: "assistant",
      content: "Happy to. To make it land, anything specific about your background or why Lumen — or should I write a strong general version you can lightly tweak?",
      ts: min(80),
    },
    {
      id: "c2m2u",
      role: "user",
      content: "uh i've got about 5 years in marketing, mostly social media and some email campaigns. that's really it. just make it sound good",
      ts: min(79),
    },
    {
      id: "c2m2a",
      role: "assistant",
      content: "Here's a strong draft:\n\nDear Hiring Team,\n\nI'm excited to apply for the Marketing Manager position at Lumen. With over five years of experience driving marketing initiatives, I've developed expertise in social media strategy and email campaign management that aligns closely with what a fast-moving startup like Lumen needs.\n\nIn previous roles, I led social media efforts that grew engaged audiences and designed email campaigns that nurtured leads through the funnel. I thrive where I can wear multiple hats, move quickly, and see the direct impact of my work on growth.\n\nWhat draws me to Lumen is the chance to help shape a brand at an early stage — to build rather than maintain. I'd love to bring my energy and experience to your team.\n\nSincerely,\n[Your Name]",
      ts: min(79),
    },
    {
      id: "c2m3u",
      role: "user",
      content: "oh nice. can you make it a bit longer though? feels a little short for a cover letter",
      ts: min(77),
    },
    {
      id: "c2m3a",
      role: "assistant",
      content: "Sure — here's an expanded version with an extra paragraph on your impact and approach:\n\n[...same opening...]\n\nBeyond execution, I take a data-informed approach — I pay attention to what's actually moving the needle and double down there rather than spreading effort thin. Whether testing subject lines, refining targeting, or finding formats that resonate, I'm comfortable owning a channel end to end and reporting on what works.\n\nI'm especially comfortable in the ambiguity of an early-stage company, where priorities shift and the playbook is still being written...\n\n[...same closing...]",
      ts: min(76),
    },
    {
      id: "c2m4u",
      role: "user",
      content: "perfect. actually can the opening be more catchy? the \"I'm excited to apply\" thing is so generic",
      ts: min(75),
    },
    {
      id: "c2m4a",
      role: "assistant",
      content: "Agreed — a sharper hook:\n\n\"The hardest part of early-stage marketing isn't doing the work — it's knowing which work matters. That's the instinct I've spent five years sharpening, and exactly what I'd bring to Lumen as your next Marketing Manager.\"\n\nThen it flows into the body as before. Want me to send you the full thing clean?",
      ts: min(74),
    },
    {
      id: "c2m5u",
      role: "user",
      content: "yes love it, that's so much better. is this good enough to send or should i change anything?",
      ts: min(73),
    },
    {
      id: "c2m5a",
      role: "assistant",
      content: "It's solid and ready. Two optional lifts: (1) swap in one concrete metric — \"grew Instagram following 40%\" or \"improved open rates from X to Y\" — specifics beat adjectives, and (2) name one specific thing about Lumen's product to show you researched them.",
      ts: min(72),
    },
    {
      id: "c2m6u",
      role: "user",
      content: "i don't really have exact metrics off the top of my head lol, just leave it as is. can you also write a short email to send it with?",
      ts: min(71),
    },
    {
      id: "c2m6a",
      role: "assistant",
      content: "Of course:\n\nSubject: Marketing Manager Application — [Your Name]\n\nHi [Hiring Manager], I've attached my cover letter and resume for the Marketing Manager role at Lumen. I'd love to bring my marketing experience to your team as you scale, and welcome the chance to talk. Thank you for your time.\n\nBest,\n[Your Name]",
      ts: min(70),
    },
    {
      id: "c2m7u",
      role: "user",
      content: "great, thanks, this is perfect",
      ts: min(69),
    },
  ],
};

const CHAT_3: Conversation = {
  id: "conv-3",
  title: "Newsletter Angle — Brainstorm",
  titleFinal: "Newsletter Angle — Brainstorm",
  shortTitle: "Find the newsletter's angle",
  ts: min(140),
  pairs: CHAT_3_PAIRS,
  goalTree: [
    { id: "root", label: "Find the newsletter's angle", parentId: null },
    { id: "a1", label: "Pick the core angle", parentId: "root" },
    { id: "a1a", label: "Sustainable pace angle", parentId: "a1" },
    { id: "a1b", label: "Post-burnout recovery angle", parentId: "a1" },
    { id: "a1c", label: "Subtraction as the whole concept", parentId: "a1" },
    { id: "nm", label: "Name the newsletter", parentId: "root" },
    { id: "n1", label: "Second Wind", parentId: "nm" },
    { id: "n2", label: "Pace", parentId: "nm" },
    { id: "n3", label: "The Subtraction", parentId: "nm" },
    { id: "n4", label: "One Less", parentId: "nm" },
    { id: "n5", label: "Less", parentId: "nm" },
    { id: "a2", label: "Prove it has a year of range", parentId: "root" },
  ],
  // wide naming node (5 children) → sibling collapse on P4/P7; P7 back-refs the naming node
  pairGoals: [
    { currentNodeId: "a1" },
    { currentNodeId: "a1a" },
    { currentNodeId: "a1b" },
    { currentNodeId: "n2" },
    { currentNodeId: "a1c" },
    { currentNodeId: "a2" },
    { currentNodeId: "n4", relatesTo: "n2" },
  ],
  messages: [
    {
      id: "c3m1u",
      role: "user",
      content: "i want to start a newsletter but i'm stuck on the angle. it's about productivity but that space is SO saturated, every angle feels taken. help me think through it",
      ts: min(140),
    },
    {
      id: "c3m1a",
      role: "assistant",
      content: "Let's pull it apart. The crowding is mostly in one lane — tips, tools, optimization. Less-worn angles: (a) anti-productivity / push back on hustle culture, (b) productivity for one specific identity (new managers, parents, ADHD), (c) the emotional side — guilt, burnout, comparison, which almost no tactics-newsletter touches. Which feels closest to what you actually want to say?",
      ts: min(140),
    },
    {
      id: "c3m2u",
      role: "user",
      content: "the anti-productivity one is interesting but it feels a bit edgy-for-the-sake-of-it, contrarian just to stand out. what i actually care about is more like... sustainable pace. not burning yourself out to achieve things. but i don't want it to become woo-woo wellness stuff either",
      ts: min(138),
    },
    {
      id: "c3m2a",
      role: "assistant",
      content: "That's a real lane, narrower than \"wellness\" — it's for people still ambitious, still wanting to achieve, who've rejected grinding as the only path. Something like \"for ambitious people who refuse to burn out to get there.\" Keeps the drive, swaps the method. Threads between hustle-bros and bubble-bath wellness.",
      ts: min(137),
    },
    {
      id: "c3m3u",
      role: "user",
      content: "ooh yeah, \"ambitious but not at any cost.\" that's close. i'd sharpen it — i think it's specifically for people who've ALREADY burned out once, hit the wall, and are terrified of doing it again. that's the emotional truth. recovery, not prevention",
      ts: min(135),
    },
    {
      id: "c3m3a",
      role: "assistant",
      content: "Much sharper — \"I've been there and I'm not going back\" is visceral, and it gives you authority and a clear reader. On names, want to riff? Directions: recovery (Second Wind, Round Two), pace/tempo (Steady, Cadence), or the wall itself (After the Wall).",
      ts: min(134),
    },
    {
      id: "c3m4u",
      role: "user",
      content: "\"Second Wind\" is great but 100% taken. i like the recovery vibe though. what about something built around \"pace\" specifically?",
      ts: min(132),
    },
    {
      id: "c3m4a",
      role: "assistant",
      content: "Pace is strong — implies control and sustainability without being soft. Options: \"Pace\" (clean but plain), \"Set the Pace,\" \"Pacemaker\" (memorable but pulls medical), \"At Your Own Pace.\" Cadence is the close cousin.",
      ts: min(131),
    },
    {
      id: "c3m5u",
      role: "user",
      content: "haha \"Pacemaker\" sounds like the heart thing. ok let me park the name. more important — what would actually be IN it each week? what does a reader get",
      ts: min(129),
    },
    {
      id: "c3m5a",
      role: "assistant",
      content: "A repeatable three-part structure: (1) a short essay on the mindset/emotional side, (2) one concrete sustainable tactic, (3) \"one thing to stop doing this week.\" The third is the differentiator — everyone says what to add, almost nobody curates what to remove.",
      ts: min(128),
    },
    {
      id: "c3m6u",
      role: "user",
      content: "the \"one thing to stop doing\" — THAT'S the differentiator. everyone's adding, nobody's subtracting. let me make that the core, not just a section. what if the whole newsletter is about subtraction — removing things — not addition. that's the recovery story too, you burn out from doing too much",
      ts: min(126),
    },
    {
      id: "c3m6a",
      role: "assistant",
      content: "That's the whole thing — and it ties everything together. Burnout is addition; recovery is subtraction. So it's not \"here's more to do,\" it's \"here's one thing to remove this week, and why it's quietly costing you.\" Pace, recovery, anti-hustle all collapse into one clean idea: less. Subtraction as the entire brand.",
      ts: min(125),
    },
    {
      id: "c3m7u",
      role: "user",
      content: "YES. ok now i'm actually excited. so each issue = one thing to remove. only worry — does that have legs? can i find 52 things to subtract a year or do i run out in a month",
      ts: min(123),
    },
    {
      id: "c3m7a",
      role: "assistant",
      content: "More range than it looks: habits (the 5th coffee, doomscrolling), commitments (the meeting that should be an email), beliefs (you must answer immediately, busy = valuable), inputs (newsletters you don't read — meta and funny), obligations (the standing call nobody wants). Five buckets, ~10 each — past a year before repeating, and \"beliefs\" is bottomless.",
      ts: min(122),
    },
    {
      id: "c3m8u",
      role: "user",
      content: "ok that's plenty. so for the name — \"The Subtraction\"? or just \"Less\"? though \"Less\" might be too generic and impossible to search for",
      ts: min(120),
    },
    {
      id: "c3m8a",
      role: "assistant",
      content: "You've answered it — \"Less\" is clean but unsearchable and undefendable. \"The Subtraction\" is distinctive and names the mechanic, though a touch clinical. If you want warmth, \"One Less\" keeps the idea but feels human and ties to the one-per-issue format. I'd lean that way over \"Less.\"",
      ts: min(119),
    },
    {
      id: "c3m9u",
      role: "user",
      content: "yeah \"Less\" is out. i'll sit with the subtraction ones, maybe \"One Less.\" but honestly this was huge — i went from \"i have nothing\" to a sharp angle with a real hook. thanks for thinking it through with me",
      ts: min(117),
    },
  ],
};

const PRELOADED_CONVS: Conversation[] = [CHAT_1, CHAT_2, CHAT_3];

function makeId() {
  return Math.random().toString(36).slice(2);
}

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function titleFromMessage(msg: string) {
  return msg.length > 36 ? msg.slice(0, 36).trim() + "…" : msg;
}

const SAMPLE_RESPONSES = [
  "That's an interesting question. Let me think through it carefully — there are a few ways to approach this.",
  "Sure, I can help with that. Here's what I know about the topic.",
  "Great point. To expand on that, the key things to consider are context, clarity, and conciseness.",
  "I understand what you're looking for. Let me break it down step by step.",
  "Happy to help. Here's a straightforward explanation of how that works.",
];

function fakeReply(): Promise<string> {
  return new Promise((res) =>
    setTimeout(
      () => res(SAMPLE_RESPONSES[Math.floor(Math.random() * SAMPLE_RESPONSES.length)]),
      900 + Math.random() * 600
    )
  );
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(PRELOADED_CONVS);
  const [activeId, setActiveId] = useState<string>("conv-1");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [titleUpdating, setTitleUpdating] = useState(false);
  const [minimapLoading, setMinimapLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  // ── Shared timeline↔chat state (lifted so both views stay in lockstep) ──
  const pairs = active?.pairs ?? [];
  const messages = active?.messages ?? [];
  const [selectedPairIdx, setSelectedPairIdx] = useState(0);
  // Interaction model is fixed: Focus reveal + Highlight connection (decided in design).
  const revealMode: "replay" | "focus" = "focus";
  const connectionStyle: "highlight" | "line" | "spotlight" = "highlight";
  const mainAreaRef = useRef<HTMLDivElement>(null);

  const hasPairs = pairs.length > 0;
  const isLatest = !hasPairs || selectedPairIdx >= pairs.length - 1;
  const safePairIdx = Math.min(Math.max(0, selectedPairIdx), Math.max(0, pairs.length - 1));

  // pair → message-range mapping
  const pairStarts = pairs.map((p) => messages.findIndex((m) => m.id === p.msgId));
  function pairIdxForMsg(i: number) {
    let r = -1;
    for (let k = 0; k < pairStarts.length; k++) if (pairStarts[k] >= 0 && i >= pairStarts[k]) r = k;
    return r;
  }
  const selEnd = hasPairs
    ? (safePairIdx + 1 < pairStarts.length ? pairStarts[safePairIdx + 1] : messages.length) - 1
    : messages.length - 1;
  const visibleMessages = revealMode === "replay" && hasPairs ? messages.slice(0, selEnd + 1) : messages;

  const activePair = pairs[safePairIdx];
  const activeAccent = activePair
    ? activePair.side === "AI" ? AI_COLOR : activePair.side === "BOTH" ? "#9aa0a6" : YOU_COLOR
    : YOU_COLOR;

  // reset selection to latest when switching chats
  useEffect(() => {
    setSelectedPairIdx(Math.max(0, pairs.length - 1));
  }, [activeId, pairs.length]);

  function selectPair(idx: number) {
    setSelectedPairIdx(idx);
    const pair = pairs[idx];
    if (!pair) return;
    requestAnimationFrame(() => {
      const el = document.getElementById(`msg-${pair.msgId}`);
      el?.scrollIntoView({ behavior: "smooth", block: revealMode === "focus" ? "center" : "start" });
    });
  }

  function jumpToLatest() {
    const last = Math.max(0, pairs.length - 1);
    setSelectedPairIdx(last);
    requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }));
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [active?.messages.length, loading]);

  // Scroll-sync (focus mode only): nearest pair to viewport center becomes current
  useEffect(() => {
    if (revealMode !== "focus" || !hasPairs) return;
    const el = chatScrollRef.current;
    if (!el) return;
    function onScroll() {
      if (!el) return;
      const center = el.scrollTop + el.clientHeight / 2;
      let best = 0;
      let bestDist = Infinity;
      pairs.forEach((pair, i) => {
        const m = document.getElementById(`msg-${pair.msgId}`);
        if (!m) return;
        const d = Math.abs(m.offsetTop - center);
        if (d < bestDist) { bestDist = d; best = i; }
      });
      setSelectedPairIdx(best);
    }
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [revealMode, hasPairs, activeId]);

  useEffect(() => {
    if (!sidebarOpen) return;
    function handle(e: MouseEvent) {
      const sidebar = document.getElementById("sidebar");
      if (sidebar && !sidebar.contains(e.target as Node)) setSidebarOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [sidebarOpen]);

  function newChat() {
    const conv: Conversation = {
      id: makeId(),
      title: "New conversation",
      titleFinal: "New conversation",
      shortTitle: "New conversation",
      messages: [],
      pairs: [],
      ts: Date.now(),
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
    setInput("");
    setSidebarOpen(false);
  }

  function selectConv(id: string) {
    setActiveId(id);
    setSidebarOpen(false);
  }

  function deleteConv(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(conversations[0]?.id ?? "");
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    let convId = activeId;
    if (!convId) {
      const conv: Conversation = {
        id: makeId(),
        title: titleFromMessage(text),
        titleFinal: titleFromMessage(text),
        shortTitle: titleFromMessage(text),
        messages: [],
        pairs: [],
        ts: Date.now(),
      };
      setConversations((prev) => [conv, ...prev]);
      convId = conv.id;
      setActiveId(convId);
    }

    const userMsg: Message = { id: makeId(), role: "user", content: text, ts: Date.now() };

    setConversations((prev) =>
      prev.map((c) =>
        c.id === convId
          ? {
              ...c,
              title: c.messages.length === 0 ? titleFromMessage(text) : c.title,
              titleFinal: c.messages.length === 0 ? titleFromMessage(text) : c.titleFinal,
              messages: [...c.messages, userMsg],
            }
          : c
      )
    );
    setInput("");
    setLoading(true);
    setMinimapLoading(true);
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const reply = await fakeReply();
    const aiMsg: Message = { id: makeId(), role: "assistant", content: reply, ts: Date.now() };

    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, aiMsg] } : c))
    );
    setLoading(false);
    setTimeout(() => setMinimapLoading(false), 1200);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function onInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }

  return (
    <div className="size-full flex overflow-hidden" style={{ fontFamily: "'Inter', sans-serif", background: "var(--background)" }}>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 md:hidden"
          style={{ background: "rgba(0,0,0,0.25)" }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        id="sidebar"
        className="flex flex-col h-full shrink-0 z-30 transition-transform duration-200"
        style={{
          width: 240,
          background: "var(--secondary)",
          borderRight: "1px solid var(--border)",
        }}
      >
        <SidebarInner
          conversations={conversations}
          activeId={activeId}
          titleUpdating={titleUpdating}
          onNew={newChat}
          onSelect={selectConv}
          onDelete={deleteConv}
          onClose={() => setSidebarOpen(false)}
        />
      </aside>

      <style>{`
        @media (max-width: 767px) {
          #sidebar {
            position: fixed !important;
            top: 0; left: 0; bottom: 0;
            transform: translateX(${sidebarOpen ? "0" : "-100%"});
            box-shadow: ${sidebarOpen ? "4px 0 24px rgba(0,0,0,0.10)" : "none"};
          }
        }
        @keyframes blink-cursor {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        .shimmer-bar {
          background: linear-gradient(
            90deg,
            var(--accent) 25%,
            var(--muted) 50%,
            var(--accent) 75%
          );
          background-size: 200% 100%;
          animation: shimmer 1.6s ease-in-out infinite;
        }
        @keyframes livePulse {
          0%   { box-shadow: 0 0 0 0 rgba(34,160,90,0.55); }
          70%  { box-shadow: 0 0 0 5px rgba(34,160,90,0); }
          100% { box-shadow: 0 0 0 0 rgba(34,160,90,0); }
        }
        .live-dot { animation: livePulse 2s ease-out infinite; }
        @keyframes pillRise {
          from { opacity: 0; transform: translate(-50%, 8px); }
          to   { opacity: 1; transform: translate(-50%, 0); }
        }
        .pill-rise { animation: pillRise 0.22s ease-out; }
      `}</style>

      {/* Main area */}
      <div ref={mainAreaRef} className="flex flex-1 h-full min-w-0 relative">

        {/* History hairline — whole-surface cue that you're viewing the past */}
        <div
          className="pointer-events-none absolute top-0 left-0 right-0"
          style={{
            height: 2,
            zIndex: 20,
            background: "#e69614",
            opacity: hasPairs && !isLatest ? 0.9 : 0,
            transition: "opacity 0.25s",
          }}
        />

        {/* Chat column */}
        <div className="flex flex-col flex-1 h-full min-w-0 relative">

          {/* Floating 'Back to latest' pill — chat-side, appears only when viewing history */}
          {active && active.messages.length > 0 && hasPairs && !isLatest && (
            <button
              onClick={jumpToLatest}
              className="pill-rise absolute left-1/2 flex items-center gap-1.5 rounded-full px-3 py-1.5 z-20"
              style={{
                bottom: 92,
                background: "var(--card)",
                border: "1px solid var(--border)",
                boxShadow: "0 4px 14px rgba(0,0,0,0.12)",
                color: "var(--foreground)",
                fontSize: 12,
                fontWeight: 500,
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#e69614", display: "inline-block" }} />
              Back to latest
              <ArrowDown size={13} strokeWidth={2} />
            </button>
          )}

          {/* Mobile menu row */}
          <div
            className="flex items-center gap-3 px-4 py-2 md:hidden"
            style={{ borderBottom: "1px solid var(--border)", background: "var(--background)" }}
          >
            <button onClick={() => setSidebarOpen(true)} className="p-1.5 rounded-lg" style={{ color: "var(--foreground)" }}>
              <Menu size={18} strokeWidth={1.8} />
            </button>
            <span className="flex-1 text-sm truncate" style={{ fontWeight: 500, color: "var(--foreground)" }}>
              {active?.title ?? "AI Assistant"}
            </span>
            <button onClick={newChat} className="p-1.5 rounded-lg" style={{ color: "var(--muted-foreground)" }}>
              <Plus size={18} strokeWidth={1.8} />
            </button>
          </div>


          {/* Content */}
          <div className="flex-1 overflow-y-auto flex flex-col" style={{ scrollbarWidth: "none" }}>
            {!active || active.messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center px-4 md:px-6">
                <div className="w-full max-w-2xl flex flex-col items-center gap-6">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--accent)" }}>
                      <MessageSquare size={18} strokeWidth={1.5} style={{ color: "var(--muted-foreground)" }} />
                    </div>
                    <p className="text-sm" style={{ color: "var(--muted-foreground)" }}>What can I help you with?</p>
                  </div>
                  <InputBox textareaRef={textareaRef} input={input} loading={loading} onChange={onInputChange} onKeyDown={onKeyDown} onSend={send} />
                </div>
              </div>
            ) : (
              <>
                <div ref={chatScrollRef} className="flex-1 overflow-y-auto" style={{ scrollbarWidth: "none" }}>
                  <div className="max-w-2xl mx-auto px-4 md:px-6 py-6 md:py-8 flex flex-col gap-5 md:gap-6">
                    {visibleMessages.map((msg, i) => {
                      const mp = pairIdxForMsg(i);
                      const isActivePair = hasPairs && mp === safePairIdx;
                      const isPairStart = mp >= 0 && pairs[mp]?.msgId === msg.id;
                      const dim = connectionStyle === "spotlight" && hasPairs && !isActivePair;
                      const ringed = isActivePair && (connectionStyle === "highlight" || connectionStyle === "line");
                      return (
                      <div
                        id={`msg-${msg.id}`}
                        key={msg.id}
                        className={`flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}
                        style={{ opacity: dim ? 0.32 : 1, transition: "opacity 0.25s" }}
                      >
                        <div
                          className="flex items-center gap-1.5 mb-0.5"
                          style={{ color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", fontSize: 10, letterSpacing: "0.04em" }}
                        >
                          {isActivePair && isPairStart && connectionStyle === "highlight" && (
                            <span
                              className="rounded"
                              style={{ background: activeAccent, color: "#fff", fontSize: 9, padding: "1px 5px", fontWeight: 600, letterSpacing: "0.02em" }}
                            >
                              {pairs[mp].id}
                            </span>
                          )}
                          <span>{msg.role === "user" ? "you" : "assistant"} · {formatTime(msg.ts)}</span>
                        </div>

                        {/* Attachment thumbnail */}
                        {msg.attachment && (
                          <div
                            className="mb-1.5 rounded-xl overflow-hidden flex items-center gap-2 px-3 py-2"
                            style={{
                              background: "var(--accent)",
                              border: "1px solid var(--border)",
                              maxWidth: "min(80%, 340px)",
                            }}
                          >
                            <img
                              src={msg.attachment.src}
                              alt={msg.attachment.name}
                              className="w-12 h-12 rounded-lg object-cover shrink-0"
                            />
                            <div className="flex flex-col min-w-0">
                              <span className="text-xs font-medium truncate" style={{ color: "var(--foreground)" }}>
                                {msg.attachment.name}
                              </span>
                              <span className="flex items-center gap-1 text-xs mt-0.5" style={{ color: "var(--muted-foreground)" }}>
                                <Paperclip size={10} /> attachment
                              </span>
                            </div>
                          </div>
                        )}

                        <div
                          className="text-sm leading-relaxed px-4 py-3 rounded-2xl"
                          style={{
                            maxWidth: "min(80%, 480px)",
                            ...(msg.role === "user"
                              ? { background: "var(--primary)", color: "var(--primary-foreground)", borderBottomRightRadius: 6 }
                              : { background: "var(--card)", color: "var(--foreground)", border: "1px solid var(--border)", borderBottomLeftRadius: 6 }),
                            ...(ringed ? { boxShadow: `0 0 0 2px ${activeAccent}`, transition: "box-shadow 0.2s" } : {}),
                          }}
                        >
                          {msg.content}
                        </div>
                      </div>
                      );
                    })}

                    {revealMode === "replay" && hasPairs && !isLatest && (
                      <div className="flex items-center gap-2 py-1 select-none" style={{ opacity: 0.6 }}>
                        <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
                        <span style={{ fontSize: 10, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace" }}>
                          replaying up to {activePair?.id} · {messages.length - visibleMessages.length} more hidden
                        </span>
                        <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
                      </div>
                    )}

                    {loading && (
                      <div className="flex flex-col items-start gap-1">
                        <div className="text-xs mb-0.5" style={{ color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", fontSize: 10 }}>
                          assistant
                        </div>
                        <div className="px-4 py-3 rounded-2xl" style={{ background: "var(--card)", border: "1px solid var(--border)", borderBottomLeftRadius: 6 }}>
                          <TypingDots />
                        </div>
                      </div>
                    )}
                    <div ref={bottomRef} />
                  </div>
                </div>

                <div className="px-4 md:px-6 py-3 md:py-4" style={{ borderTop: "1px solid var(--border)" }}>
                  <InputBox textareaRef={textareaRef} input={input} loading={loading} onChange={onInputChange} onKeyDown={onKeyDown} onSend={send} />
                </div>
              </>
            )}
          </div>
        </div>
        {/* end chat column */}

        {/* Minimap panel — hidden on mobile */}
        <div
          className="hidden md:flex flex-col h-full shrink-0"
          style={{ width: 260, borderLeft: "1px solid var(--border)", background: "var(--secondary)" }}
        >
          <Minimap
            shortTitle={active?.shortTitle ?? "Conversation"}
            pairs={pairs}
            goalTree={active?.goalTree}
            pairGoals={active?.pairGoals}
            isLoading={minimapLoading}
            selectedIdx={safePairIdx}
            isLatest={isLatest}
            onSelectPair={selectPair}
          />
        </div>

      </div>
    </div>
  );
}

/* ─── Sidebar ─────────────────────────────────────────────────────────────── */

function SidebarInner({
  conversations,
  activeId,
  titleUpdating,
  onNew,
  onSelect,
  onDelete,
  onClose,
}: {
  conversations: Conversation[];
  activeId: string | null;
  titleUpdating: boolean;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onClose: () => void;
}) {
  return (
    <>
      <div className="flex items-center justify-between px-4 pt-5 pb-3">
        <span className="text-xs tracking-widest uppercase" style={{ color: "var(--muted-foreground)", letterSpacing: "0.12em" }}>
          Chats
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={onNew}
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition-colors"
            style={{ background: "var(--accent)", color: "var(--foreground)" }}
          >
            <Plus size={13} strokeWidth={2} /> New
          </button>
          <button onClick={onClose} className="md:hidden ml-1 p-1.5 rounded-lg" style={{ color: "var(--muted-foreground)" }}>
            <X size={15} strokeWidth={1.8} />
          </button>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-4" style={{ scrollbarWidth: "none" }}>
        {conversations.length === 0 && (
          <p className="text-xs px-2 pt-2" style={{ color: "var(--muted-foreground)" }}>No conversations yet.</p>
        )}
        {conversations.map((c) => {
          const isActive = c.id === activeId;
          const isUpdating = isActive && titleUpdating;
          return (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              className="w-full flex items-start gap-2 rounded-lg px-2.5 py-2 mb-0.5 text-left group transition-colors"
              style={{ background: isActive ? "var(--accent)" : "transparent", color: "var(--foreground)" }}
            >
              <MessageSquare size={13} strokeWidth={1.5} className="mt-0.5 shrink-0" style={{ color: "var(--muted-foreground)" }} />
              <span className="flex-1 text-xs leading-snug flex items-start gap-1" style={{ fontWeight: isActive ? 500 : 400, wordBreak: "break-word" }}>
                {c.title}
                {isUpdating && (
                  <span
                    className="inline-block w-0.5 h-3 rounded-sm"
                    style={{
                      background: "var(--muted-foreground)",
                      animation: "blink-cursor 0.8s step-end infinite",
                      verticalAlign: "middle",
                    }}
                  />
                )}
              </span>
              <span
                onClick={(e) => onDelete(c.id, e)}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded"
                style={{ color: "var(--muted-foreground)" }}
              >
                <Trash2 size={11} />
              </span>
            </button>
          );
        })}
      </nav>

      <div className="px-4 py-3 text-xs" style={{ borderTop: "1px solid var(--border)", color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", fontSize: 11 }}>
        AI Assistant · v1.0
      </div>
    </>
  );
}

/* ─── GoalThread ──────────────────────────────────────────────────────────── */

function GoalThread({ nodes }: { nodes: GoalNode[] }) {
  if (nodes.length === 0) return null;

  return (
    <div className="flex flex-col" style={{ marginTop: 2 }}>
      {nodes.map((node, i) => {
        const depth = i; // each successive node is one level deeper
        const isLast = i === nodes.length - 1;
        const indent = depth * 14;

        return (
          <div key={i} className="flex items-stretch" style={{ paddingLeft: 4 + indent }}>
            {/* Connector column */}
            <div className="flex flex-col items-center shrink-0" style={{ width: 14, marginRight: 6 }}>
              {/* Vertical line from parent */}
              <div style={{
                width: 1.5,
                flex: isLast ? "0 0 10px" : "1",
                minHeight: 8,
                background: node.isSideTrack ? "transparent" : "var(--border)",
                borderLeft: node.isSideTrack ? "1.5px dashed var(--border)" : "none",
                marginLeft: node.isSideTrack ? -0.75 : 0,
              }} />
              {/* Elbow */}
              <div style={{
                width: 10,
                height: 8,
                borderLeft: `1.5px ${node.isSideTrack ? "dashed" : "solid"} var(--border)`,
                borderBottom: `1.5px ${node.isSideTrack ? "dashed" : "solid"} var(--border)`,
                borderBottomLeftRadius: 3,
                flexShrink: 0,
              }} />
            </div>

            {/* Node content */}
            <div
              className="flex items-center gap-1.5 py-1.5 min-w-0"
              style={{ flex: 1 }}
            >
              {/* Node dot */}
              <div style={{
                width: node.isCurrent ? 7 : 5,
                height: node.isCurrent ? 7 : 5,
                borderRadius: "50%",
                flexShrink: 0,
                background: node.isCurrent ? YOU_COLOR : "var(--border)",
                boxShadow: node.isCurrent ? `0 0 6px ${YOU_COLOR}66` : "none",
                transition: "all 0.2s",
              }} />
              <span
                className="leading-snug min-w-0 truncate"
                style={{
                  fontSize: node.isCurrent ? 11 : 10,
                  color: node.isCurrent ? "var(--foreground)" : "var(--muted-foreground)",
                  fontWeight: node.isCurrent ? 500 : 400,
                  fontStyle: node.isSideTrack ? "italic" : "normal",
                  transition: "color 0.2s",
                }}
              >
                {node.label}
              </span>
              {node.isSideTrack && (
                <span style={{ fontSize: 8, color: AI_COLOR, fontFamily: "'DM Mono', monospace", flexShrink: 0 }}>
                  ⤳
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Goal hierarchy (§4 display layer) ───────────────────────────────────── */

// ── Goal hierarchy types ─────────────────────────────────────────────────────

type CollapsedRow =
  | { kind: "root";     label: string; nodeId?: string }
  | { kind: "chip";     hidden: number }           // ⌄ N more — interactive
  | { kind: "ancestor"; label: string; depth: number; nodeId: string }
  | { kind: "current";  label: string; depth: number; nodeId: string }
  | { kind: "side";     label: string; nodeId: string }; // side-track off root

// One node in the fully-expanded tree (recursive)
type FullNode = {
  id: string;
  label: string;
  kind?: "side";
  isCurrent: boolean;
  children: FullNode[];
};

type GoalRender = {
  collapsed: CollapsedRow[];   // default constant-size view
  fullTree: FullNode[];        // expanded view (children of root)
  hiddenCount: number;         // > 0 → chip exists in collapsed view
  currentId: string;
};

// Build the full recursive tree rooted at `rootId`.
function buildFullTree(
  tree: GoalTreeNode[],
  rootId: string | null,
  currentId: string,
  byId: Map<string, GoalTreeNode>
): FullNode[] {
  return tree
    .filter((n) => n.parentId === rootId)
    .map((n) => ({
      id: n.id,
      label: n.label,
      kind: n.kind,
      isCurrent: n.id === currentId,
      children: buildFullTree(tree, n.id, currentId, byId),
    }));
}

// Compute path from root node (parentId=null) to currentId.
function pathToNode(
  tree: GoalTreeNode[],
  currentId: string,
  byId: Map<string, GoalTreeNode>
): GoalTreeNode[] {
  const path: GoalTreeNode[] = [];
  let cur = byId.get(currentId);
  while (cur) {
    path.unshift(cur);
    cur = cur.parentId ? byId.get(cur.parentId) : undefined;
  }
  return path; // [root, …, current]
}

function computeGoalRender(
  tree: GoalTreeNode[],
  currentId: string,
  rootLabel: string
): GoalRender | null {
  const byId = new Map(tree.map((n) => [n.id, n]));
  const current = byId.get(currentId);
  if (!current) return null;

  // Full tree for expanded view (children of the virtual root label node)
  const rootNode = tree.find((n) => n.parentId === null);
  const fullTree = rootNode
    ? buildFullTree(tree, rootNode.id, currentId, byId)
    : buildFullTree(tree, null, currentId, byId);

  // §4.7 side-track: root → side node (dashed)
  if (current.kind === "side") {
    return {
      collapsed: [
        { kind: "root", label: rootLabel },
        { kind: "side", label: current.label, nodeId: currentId },
      ],
      fullTree,
      hiddenCount: 0,
      currentId,
    };
  }

  const path = pathToNode(tree, currentId, byId);
  // path[0] is the root outcome node; we replace its label with rootLabel in rendering
  const d = path.length - 1; // depth below root node

  const collapsed: CollapsedRow[] = [{ kind: "root", label: rootLabel }];

  if (d <= 1) {
    collapsed.push({ kind: "current", label: current.label, depth: 1, nodeId: currentId });
  } else if (d === 2) {
    collapsed.push({ kind: "ancestor", label: path[1].label, depth: 1, nodeId: path[1].id });
    collapsed.push({ kind: "current", label: current.label, depth: 2, nodeId: currentId });
  } else {
    const hidden = d - 2;
    collapsed.push({ kind: "chip", hidden });
    collapsed.push({ kind: "ancestor", label: path[d - 1].label, depth: 1, nodeId: path[d - 1].id });
    collapsed.push({ kind: "current", label: current.label, depth: 2, nodeId: currentId });
  }

  return { collapsed, fullTree, hiddenCount: Math.max(0, d - 2), currentId };
}

// ── Shared line constants ─────────────────────────────────────────────────────
const LINE_W = 14;        // width of the connector column
const LINE_COLOR = "rgba(0,0,0,0.13)";
const LINE_PX = 1;        // line weight
const ARC_R = 7;          // border-radius of the arc turn

// A single node row used in both collapsed and expanded views.
function GoalNode({
  label,
  isCurrent,
  isRoot,
  isSide,
  isDim,
  showLine,     // draw the vertical segment above this node
  isLast,       // arc terminates here (no line below)
  dashed,
  onClick,
}: {
  label: string;
  isCurrent?: boolean;
  isRoot?: boolean;
  isSide?: boolean;
  isDim?: boolean;
  showLine?: boolean;
  isLast?: boolean;
  dashed?: boolean;
  onClick?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const clickable = !!onClick;
  const dotSize = isCurrent ? 7 : isRoot ? 7 : 5;
  const dotColor = isCurrent ? YOU_COLOR : isRoot ? "var(--foreground)" : "var(--muted-foreground)";
  const dotOpacity = isRoot ? 0.45 : isSide ? 0.55 : isDim ? 0.4 : 1;

  return (
    <div
      className="flex items-stretch rounded-sm"
      onClick={onClick}
      onMouseEnter={() => clickable && setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: clickable ? "pointer" : "default",
        minHeight: 26,
        background: hovered ? "rgba(0,0,0,0.05)" : "transparent",
        marginLeft: isRoot ? -6 : -4,
        paddingLeft: isRoot ? 6 : 4,
        marginRight: -4,
        paddingRight: 4,
        transition: "background 0.1s",
      }}
    >
      {/* Connector column — omitted entirely for root so it sits flush left */}
      {!isRoot && (
        <div
          className="shrink-0 flex flex-col items-center"
          style={{ width: LINE_W, marginRight: 8 }}
        >
          {/* vertical segment above the arc */}
          {showLine && (
            <div style={{
              width: LINE_PX,
              flex: "0 0 8px",
              background: dashed ? "transparent" : LINE_COLOR,
              borderLeft: dashed ? `${LINE_PX}px dashed ${LINE_COLOR}` : "none",
            }} />
          )}
          {!showLine && <div style={{ flex: "0 0 8px" }} />}

          {/* arc turn (L-shaped) */}
          <div style={{
            width: LINE_W - 2,
            height: 9,
            borderLeft: `${LINE_PX}px ${dashed ? "dashed" : "solid"} ${LINE_COLOR}`,
            borderBottom: `${LINE_PX}px ${dashed ? "dashed" : "solid"} ${LINE_COLOR}`,
            borderBottomLeftRadius: ARC_R,
            flexShrink: 0,
          }} />

          {/* vertical segment continuing below (if not the last in this branch) */}
          {!isLast && (
            <div style={{
              width: LINE_PX,
              flex: 1,
              minHeight: 4,
              background: dashed ? "transparent" : LINE_COLOR,
              borderLeft: dashed ? `${LINE_PX}px dashed ${LINE_COLOR}` : "none",
            }} />
          )}
        </div>
      )}

      {/* Node content */}
      <div
        className="flex items-center gap-2 min-w-0 py-1"
        style={{ flex: 1, opacity: isDim ? 0.45 : 1, transition: "opacity 0.15s" }}
      >
        <div style={{
          width: dotSize,
          height: dotSize,
          borderRadius: "50%",
          flexShrink: 0,
          background: dotColor,
          opacity: dotOpacity,
          boxShadow: isCurrent ? `0 0 0 2.5px ${YOU_COLOR}28` : "none",
        }} />
        <span
          className="leading-snug min-w-0 truncate"
          style={{
            fontSize: isCurrent ? 12 : isRoot ? 12 : 11,
            fontWeight: isCurrent ? 600 : isRoot ? 600 : 400,
            color: isCurrent ? "var(--foreground)" : isRoot ? "var(--foreground)" : "var(--muted-foreground)",
            fontStyle: isSide ? "italic" : "normal",
          }}
        >
          {label}
        </span>
      </div>
    </div>
  );
}

// Expanded tree — renders full hierarchy recursively with YouTube-style lines.
function ExpandedTree({
  nodes,
  depth = 0,
  parentHasMore = false,
  currentId,
  onNodeClick,
}: {
  nodes: FullNode[];
  depth?: number;
  parentHasMore?: boolean;
  currentId: string;
  onNodeClick: (id: string) => void;
}) {
  if (nodes.length === 0) return null;
  return (
    <div style={{ paddingLeft: depth > 0 ? LINE_W + 8 : 0 }}>
      {nodes.map((node, i) => {
        const isLast = i === nodes.length - 1;
        const isCurrent = node.id === currentId;
        const isSide = node.kind === "side";
        return (
          <div key={node.id}>
            <GoalNode
              label={node.label}
              isCurrent={isCurrent}
              isSide={isSide}
              showLine={true}
              isLast={isLast && node.children.length === 0}
              dashed={isSide}
              onClick={() => onNodeClick(node.id)}
            />
            {node.children.length > 0 && (
              <ExpandedTree
                nodes={node.children}
                depth={depth + 1}
                currentId={currentId}
                onNodeClick={onNodeClick}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function GoalHierarchy({
  data,
  onNodeClick,
}: {
  data: GoalRender;
  onNodeClick?: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasChip = data.hiddenCount > 0;

  return (
    <div className="flex flex-col">
      {!expanded ? (
        /* ── Collapsed view ─────────────────────────────────────── */
        <>
          {data.collapsed.map((row, i) => {
            if (row.kind === "root") {
              const hasChildBelow = i < data.collapsed.length - 1;
              return (
                <GoalNode
                  key="root"
                  label={row.label}
                  isRoot
                  showLine={false}
                  isLast={!hasChildBelow}
                />
              );
            }

            if (row.kind === "chip") {
              // ⌄ N more chip — line runs through it
              return (
                <div key="chip" className="flex items-center" style={{ minHeight: 24 }}>
                  {/* continuous line segment */}
                  <div
                    className="shrink-0 flex justify-center"
                    style={{ width: LINE_W, marginRight: 8 }}
                  >
                    <div style={{ width: LINE_PX, height: "100%", background: LINE_COLOR }} />
                  </div>
                  <button
                    onClick={() => setExpanded(true)}
                    className="flex items-center gap-1 rounded transition-colors"
                    style={{
                      fontSize: 11,
                      color: "var(--muted-foreground)",
                      background: "var(--accent)",
                      padding: "2px 7px",
                      border: "none",
                      cursor: "pointer",
                      fontFamily: "'DM Mono', monospace",
                    }}
                  >
                    ⌄ {row.hidden} more
                  </button>
                </div>
              );
            }

            if (row.kind === "ancestor") {
              const isBeforeCurrent = i < data.collapsed.length - 1;
              return (
                <GoalNode
                  key={`ancestor-${i}`}
                  label={row.label}
                  isDim
                  showLine={true}
                  isLast={!isBeforeCurrent}
                  dashed={false}
                  onClick={onNodeClick ? () => onNodeClick(row.nodeId) : undefined}
                />
              );
            }

            if (row.kind === "current") {
              return (
                <GoalNode
                  key="current"
                  label={row.label}
                  isCurrent
                  showLine={true}
                  isLast={true}
                  onClick={onNodeClick ? () => onNodeClick(row.nodeId) : undefined}
                />
              );
            }

            if (row.kind === "side") {
              return (
                <GoalNode
                  key="side"
                  label={row.label}
                  isCurrent
                  isSide
                  showLine={true}
                  isLast={true}
                  dashed={true}
                  onClick={onNodeClick ? () => onNodeClick(row.nodeId) : undefined}
                />
              );
            }

            return null;
          })}

          {/* Expand chip at bottom when chip already shown above, nothing extra needed.
              For d=2 with a wide tree, we don't show a chip — user expands via the
              bottom "Show full tree" affordance when applicable. */}
          {!hasChip && data.fullTree.some(n => n.children.length > 0) && (
            <button
              onClick={() => setExpanded(true)}
              className="flex items-center gap-1 mt-1 self-start"
              style={{
                fontSize: 10,
                color: "var(--muted-foreground)",
                background: "none",
                border: "none",
                cursor: "pointer",
                paddingLeft: LINE_W + 8 + 9 + 8, // align with current node text
                fontFamily: "'DM Mono', monospace",
              }}
            >
              ⌄ show full tree
            </button>
          )}
        </>
      ) : (
        /* ── Expanded view ─────────────────────────────────────── */
        <>
          {/* Root node */}
          <GoalNode
            label={data.collapsed[0].kind === "root" ? data.collapsed[0].label : ""}
            isRoot
            showLine={false}
            isLast={data.fullTree.length === 0}
          />

          {/* Full recursive tree */}
          <ExpandedTree
            nodes={data.fullTree}
            currentId={data.currentId}
            onNodeClick={(id) => { onNodeClick?.(id); }}
          />

          {/* Show less */}
          <button
            onClick={() => setExpanded(false)}
            className="flex items-center gap-1 mt-2 self-start"
            style={{
              fontSize: 10,
              color: "var(--muted-foreground)",
              background: "none",
              border: "none",
              cursor: "pointer",
              paddingLeft: 4,
              fontFamily: "'DM Mono', monospace",
            }}
          >
            ↑ show less
          </button>
        </>
      )}
    </div>
  );
}

/* ─── Minimap ─────────────────────────────────────────────────────────────── */

const YOU_COLOR = "#1A8CFF";
const AI_COLOR  = "#F2671D";
const BAR_PX = { small: 6, medium: 12, large: 18 };
const BAR_GAP = 2; // gap between a bar and the center spine — keeps two-tone halves distinct

const TOUR_SECTIONS: { key: string; label: string }[] = [
  { key: "GOAL", label: "Goal" },
  { key: "DIRECTION", label: "Direction" },
  { key: "DECISIONS", label: "Decisions" },
  { key: "TIMELINE", label: "Timeline" },
  { key: "HOW", label: "How You're Working" },
];
const TOUR_KEY = "agency-panel-tour-seen-v1";

// Coach-mark tour: a separate one-time highlight+caption mechanism (spec v4 §optional).
// Deliberately NOT reusing InfoPopover content — this is orientation, those are reference.
const TOUR_CAPTIONS: Record<string, string> = {
  GOAL:      "This tracks what you're working towards — it updates as the conversation shifts.",
  DIRECTION: "This bar shows how much of the chat's direction came from you vs. the AI.",
  DECISIONS: "This counts who introduced each new idea or requirement first.",
  TIMELINE:  "One row per exchange — tap any row to focus on that moment.",
  HOW:       "This summarises how you and the AI divided the work this exchange.",
};

function OnboardingTour({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);
  const current = TOUR_SECTIONS[step];
  const caption = TOUR_CAPTIONS[current.key] ?? "";
  const isLast = step === TOUR_SECTIONS.length - 1;

  return (
    // Positioned inside the panel column (not full-screen) so the highlight feels attached
    <div
      className="absolute bottom-16 right-3 z-50 pointer-events-auto"
      style={{ width: 218 }}
    >
      <div
        className="flex flex-col gap-2.5 rounded-xl"
        style={{
          background: "var(--card)",
          border: "1px solid var(--border)",
          boxShadow: "0 6px 28px rgba(0,0,0,0.14)",
          padding: "11px 13px 12px",
        }}
      >
        {/* Header row */}
        <div className="flex items-center justify-between">
          <span style={{ fontSize: 9, fontFamily: "'DM Mono', monospace", letterSpacing: "0.08em", textTransform: "uppercase", color: YOU_COLOR, fontWeight: 600 }}>
            {current.label}
          </span>
          <button
            onClick={onDone}
            aria-label="Skip tour"
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--muted-foreground)", fontSize: 14, lineHeight: 1, opacity: 0.6 }}
          >×</button>
        </div>

        {/* Caption — distinct from popover copy, shorter, orientation-focused */}
        <p style={{ margin: 0, fontSize: 11, lineHeight: 1.6, color: "var(--foreground)" }}>
          {caption}
        </p>

        {/* Footer: dots + nav */}
        <div className="flex items-center justify-between pt-0.5">
          <div className="flex gap-1 items-center">
            {TOUR_SECTIONS.map((_, i) => (
              <div
                key={i}
                style={{
                  width: i === step ? 14 : 5,
                  height: 5,
                  borderRadius: 999,
                  background: i === step ? YOU_COLOR : "var(--border)",
                  transition: "width 0.2s",
                }}
              />
            ))}
          </div>
          <div className="flex gap-2 items-center">
            <button
              onClick={onDone}
              style={{ fontSize: 10, fontFamily: "'DM Mono', monospace", background: "none", border: "none", cursor: "pointer", color: "var(--muted-foreground)" }}
            >
              Skip
            </button>
            <button
              onClick={() => isLast ? onDone() : setStep((s) => s + 1)}
              style={{
                fontSize: 10, fontFamily: "'DM Mono', monospace",
                background: YOU_COLOR, color: "#fff",
                border: "none", borderRadius: 6, padding: "4px 10px", cursor: "pointer",
              }}
            >
              {isLast ? "Done" : "Next →"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Minimap({
  shortTitle, pairs, goalTree, pairGoals, isLoading, selectedIdx, isLatest, onSelectPair,
}: {
  shortTitle: string;
  pairs: PairRow[];
  goalTree?: GoalTreeNode[];
  pairGoals?: PairGoal[];
  isLoading: boolean;
  selectedIdx: number;
  isLatest: boolean;
  onSelectPair: (idx: number) => void;
}) {
  const [tourVisible, setTourVisible] = useState(() => {
    try { return !localStorage.getItem(TOUR_KEY); } catch { return false; }
  });

  function dismissTour() {
    try { localStorage.setItem(TOUR_KEY, "1"); } catch {}
    setTourVisible(false);
  }

  if (pairs.length === 0) {
    return (
      <div className="flex flex-col h-full w-full items-center justify-center px-6 text-center select-none">
        <p style={{ fontSize: 11, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", lineHeight: 1.6 }}>
          Your conversation map<br />will build as you chat.
        </p>
      </div>
    );
  }

  const safeIdx = Math.min(Math.max(0, selectedIdx), pairs.length - 1);
  const snap = pairs[safeIdx].snap;

  // §4 goal-hierarchy render for the selected pair
  const pairGoal = pairGoals?.[safeIdx];
  const goalData = goalTree && pairGoal
    ? computeGoalRender(goalTree, pairGoal.currentNodeId, shortTitle)
    : null;

  // Build nodeId → pairIdx map so clicking a goal node jumps the timeline + chat.
  // Direct: every pairGoals[i].currentNodeId maps to i.
  // Grouping/ancestor nodes: map to the earliest pair whose current node is
  // a descendant of that grouping node (first time the user "entered" it).
  const nodeIdToPairIdx = useMemo<Map<string, number>>(() => {
    const map = new Map<string, number>();
    if (!goalTree || !pairGoals) return map;
    const byId = new Map(goalTree.map((n) => [n.id, n]));

    // Direct mappings first (lowest index wins for duplicates)
    pairGoals.forEach((pg, i) => {
      if (!map.has(pg.currentNodeId)) map.set(pg.currentNodeId, i);
    });

    // For every node not yet mapped: walk its descendants, take the min pairIdx found
    function firstPairUnder(nodeId: string): number | undefined {
      if (map.has(nodeId)) return map.get(nodeId)!;
      const children = goalTree!.filter((n) => n.parentId === nodeId);
      let best: number | undefined;
      for (const child of children) {
        const v = firstPairUnder(child.id);
        if (v !== undefined && (best === undefined || v < best)) best = v;
      }
      return best;
    }

    goalTree.forEach((n) => {
      if (!map.has(n.id)) {
        const v = firstPairUnder(n.id);
        if (v !== undefined) map.set(n.id, v);
      }
    });

    return map;
  }, [goalTree, pairGoals]);

  return (
    <div className="flex flex-col h-full w-full overflow-hidden select-none">

      {/* ── Status row — always fixed height ── */}
      <div
        className="shrink-0 flex items-center justify-between px-4 pt-3 pb-2"
        style={{ background: "var(--secondary)" }}
      >
        <span
          className="flex items-center gap-1.5 rounded-full px-2 py-0.5"
          style={{
            fontSize: 9, fontFamily: "'DM Mono', monospace", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 600,
            background: isLatest ? "rgba(34,160,90,0.12)" : "rgba(230,150,20,0.14)",
            color: isLatest ? "#1f8f4e" : "#b3760a",
          }}
        >
          <span
            className={isLatest ? "live-dot" : undefined}
            style={{ width: 6, height: 6, borderRadius: "50%", background: isLatest ? "#22a05a" : "#e69614", display: "inline-block" }}
          />
          {isLatest ? "Live" : `Viewing ${pairs[safeIdx].id} · history`}
        </span>
        <span style={{ fontSize: 8, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace" }}>
          {safeIdx + 1}/{pairs.length}
        </span>
      </div>

      {/* ── Goal section — grows when expanded; scrolls internally ── */}
      <div
        className="shrink-0 flex flex-col overflow-y-auto"
        style={{
          maxHeight: "46%",
          borderBottom: "1px solid var(--border)",
          background: "var(--secondary)",
          scrollbarWidth: "none",
        }}
      >
        <SectionHeader label="Goal" sectionKey="GOAL" />
        <div className="px-4 pt-0 pb-3">
          {goalData ? (
            <GoalHierarchy
              data={goalData}
              onNodeClick={(nodeId) => {
                const idx = nodeIdToPairIdx.get(nodeId);
                if (idx !== undefined) onSelectPair(idx);
              }}
            />
          ) : (
            <div className="flex items-center gap-2 py-2">
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--muted-foreground)", opacity: 0.4, flexShrink: 0 }} />
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--foreground)" }}>{shortTitle}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Direction (§2) + Decisions (§3) — always fixed ── */}
      <div
        className="shrink-0 flex flex-col"
        style={{ borderBottom: "2px solid var(--border)", background: "var(--secondary)" }}
      >

        {/* Direction — §2 */}
        <SectionHeader label="Direction" sectionKey="DIRECTION" />
        <div className="px-4 pt-0 pb-3 flex flex-col gap-2" style={{ borderBottom: "1px solid var(--border)" }}>
          {/* Bar */}
          <div className="w-full flex rounded-full overflow-hidden" style={{ height: 5, background: "var(--accent)" }}>
            <div style={{ width: `${snap.youPct}%`, background: YOU_COLOR, transition: "width 0.35s ease" }} />
            <div style={{ width: `${snap.aiPct}%`, background: AI_COLOR, transition: "width 0.35s ease" }} />
          </div>
          {/* Readouts + pair badge — spec: "You — 59%" · "@P3" · "AI — 41%" */}
          <div className="flex items-center justify-between">
            <span style={{ fontSize: 11, color: YOU_COLOR, fontFamily: "'DM Mono', monospace", fontWeight: 500 }}>
              You — {snap.youPct}%
            </span>
            {!isLatest && (
              <span style={{ fontSize: 9, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace" }}>
                @ {pairs[safeIdx].id}
              </span>
            )}
            <span style={{ fontSize: 11, color: AI_COLOR, fontFamily: "'DM Mono', monospace", fontWeight: 500 }}>
              AI — {snap.aiPct}%
            </span>
          </div>
        </div>

        {/* Decisions — §3 */}
        <SectionHeader label="Decisions" sectionKey="DECISIONS" />
        <div className="px-4 pt-0 pb-3 flex flex-col gap-2">
          {/* Counter: "Decisions — N you · M AI" */}
          <div className="flex items-baseline gap-1.5 flex-wrap" style={{ fontFamily: "'DM Mono', monospace" }}>
            <span style={{ fontSize: 10, color: "var(--muted-foreground)" }}>Decisions —</span>
            <span style={{ fontSize: 11, color: YOU_COLOR, fontWeight: 600 }}>{snap.decisionsYou} you</span>
            <span style={{ fontSize: 10, color: "var(--muted-foreground)" }}>·</span>
            <span style={{ fontSize: 11, color: AI_COLOR, fontWeight: 600 }}>{snap.decisionsAI} AI</span>
          </div>
          {/* Latest AI-created decision text — clause-truncated, verbatim per §3 */}
          {snap.latestAIDecision && snap.decisionsAI > 0 && (
            <p
              className="leading-snug m-0"
              style={{
                fontSize: 10,
                color: "var(--muted-foreground)",
                fontStyle: "italic",
                borderLeft: `2px solid ${AI_COLOR}40`,
                paddingLeft: 8,
              }}
            >
              {snap.latestAIDecision}
            </p>
          )}
        </div>

      </div>{/* end direction+decisions fixed block */}

      {/* ── Middle section — scrollable ── */}
      <div className="flex-1 overflow-hidden relative">

        {/* Shimmer skeleton while loading */}
        {isLoading && (
          <div className="px-3 pt-3 pb-2 flex flex-col gap-2">
            {[88, 68, 76, 50, 72, 60, 44].map((w, i) => (
              <div
                key={i}
                className="rounded-sm shimmer-bar"
                style={{ height: 4, width: w, opacity: 0.5, animationDelay: `${i * 0.1}s` }}
              />
            ))}
            <div className="mt-1 flex gap-1.5">
              {[24, 36, 20].map((w, i) => (
                <div
                  key={i}
                  className="rounded-sm shimmer-bar"
                  style={{ height: 4, width: w, opacity: 0.3, animationDelay: `${0.7 + i * 0.1}s` }}
                />
              ))}
            </div>
          </div>
        )}

        {/* ── Pair timeline ── */}
        <PairTimeline pairs={pairs} selectedIdx={safeIdx} onSelectPair={onSelectPair} />
      </div>

      {/* ── Bottom panel — HOW axis, always visible ── */}
      <div
        className="shrink-0 flex flex-col"
        style={{ borderTop: "2px solid var(--border)", background: "var(--secondary)" }}
      >
        {/* HOW — §5 */}
        <SectionHeader label="How You're Working" sectionKey="HOW" />
        <div className="px-4 pt-0 pb-3 flex flex-col gap-1.5" style={{ borderBottom: "1px solid var(--border)" }}>
          <div className="flex items-center justify-between">
            {!isLatest && (
              <span style={{ fontSize: 8, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace" }}>
                @ {pairs[safeIdx].id}
              </span>
            )}
          </div>
          {(() => {
            const [line1, line2] = snap.analogy.split(" — ");
            return (
              <>
                <p className="leading-snug" style={{ fontSize: 11, color: "var(--foreground)", fontWeight: 500 }}>{line1} —</p>
                <p className="leading-snug" style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{line2}</p>
              </>
            );
          })()}
        </div>

        {/* Distribution strip */}
        <div className="px-4 pt-3 pb-4 flex flex-col gap-2">
          <span style={{ fontSize: 9, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", letterSpacing: "0.1em", textTransform: "uppercase" }}>
            Mode split
          </span>
          <div className="w-full rounded-full overflow-hidden flex" style={{ height: 5 }}>
            <div style={{ width: `${snap.modeSplit.driving}%`, background: YOU_COLOR, borderRadius: "9999px 0 0 9999px", opacity: 0.85 }} />
            <div style={{ width: `${snap.modeSplit.together}%`, background: "#8fbf8f" }} />
            <div style={{ width: `${snap.modeSplit.backseat}%`, background: AI_COLOR, borderRadius: "0 9999px 9999px 0", opacity: 0.85 }} />
          </div>
          <div className="flex flex-col gap-1">
            {[
              { color: YOU_COLOR, label: "You driving",       pct: `${snap.modeSplit.driving}%`   },
              { color: "#8fbf8f", label: "Figuring together", pct: `${snap.modeSplit.together}%`  },
              { color: AI_COLOR,  label: "AI driving",        pct: `${snap.modeSplit.backseat}%`  },
            ].map(({ color, label, pct }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="flex items-center gap-1.5" style={{ fontSize: 9, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace" }}>
                  <span className="rounded-sm" style={{ width: 6, height: 6, background: color, display: "inline-block", flexShrink: 0 }} />
                  {label}
                </span>
                <span style={{ fontSize: 9, color, fontFamily: "'DM Mono', monospace", fontWeight: 500 }}>{pct}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* First-visit onboarding tour */}
      {tourVisible && <OnboardingTour onDone={dismissTour} />}

    </div>
  );
}

/* ─── InfoPopover + SectionHeader ─────────────────────────────────────────── */

// SECTION_INFO_V4: structured entries so HOW renders bold+plain inline pairs.
type InfoLine = { text: string; bold?: boolean };
const SECTION_INFO_V4: Record<string, InfoLine[]> = {
  GOAL: [
    { text: "Gives you an idea what you are currently working on, and a bit of context on the goal you are working towards." },
    { text: "You can expand to see the full structure of your goals." },
  ],
  DIRECTION: [
    { text: "Shows how much of this chat's direction has come from you versus the AI, added up so far." },
    { text: "Updates as you keep talking." },
  ],
  DECISIONS: [
    { text: "A count of who introduced what." },
    { text: "Each time a new requirement or idea gets set for this chat, it's counted here under whoever introduced it first." },
  ],
  TIMELINE: [
    { text: "The record of what actually happened — one row per exchange." },
    { text: "Tap a row to see what was decided and why." },
  ],
  HOW: [
    { text: "Shows how you and the AI worked together this exchange." },
    { text: "You're driving", bold: true },
    { text: " — you're setting the direction, AI helps when asked." },
    { text: "Copiloting", bold: true },
    { text: " — you and the AI are shaping the work together." },
    { text: "Autopilot", bold: true },
    { text: " — the AI is mostly deciding and doing." },
  ],
};

// HOW lines render as pairs: bold label + em-dash description on the same line.
function renderInfoLines(key: string) {
  const lines = SECTION_INFO_V4[key] ?? [];
  if (key !== "HOW") {
    return lines.map((l, i) => (
      <p key={i} style={{ margin: 0, fontSize: 11, lineHeight: 1.6, color: i === 0 ? "var(--foreground)" : "var(--muted-foreground)" }}>
        {l.text}
      </p>
    ));
  }
  // HOW: first line plain, then 3 bold+description pairs
  const [intro, ...rest] = lines;
  const pairs: React.ReactNode[] = [];
  for (let i = 0; i < rest.length; i += 2) {
    const label = rest[i];
    const desc = rest[i + 1];
    pairs.push(
      <p key={i} style={{ margin: 0, fontSize: 11, lineHeight: 1.6, color: "var(--muted-foreground)" }}>
        <strong style={{ color: "var(--foreground)", fontWeight: 600 }}>{label?.text}</strong>
        {desc?.text}
      </p>
    );
  }
  return [
    <p key="intro" style={{ margin: 0, fontSize: 11, lineHeight: 1.6, color: "var(--foreground)" }}>{intro.text}</p>,
    ...pairs,
  ];
}

let _popoverUid = 0;
function InfoPopover({ sectionKey }: { sectionKey: string }) {
  const [open, setOpen] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const popId = useRef(`infopop-${sectionKey}-${++_popoverUid}`).current;

  // Close on click-outside
  useEffect(() => {
    if (!open) return;
    function onMouseDown(e: MouseEvent) {
      if (
        popRef.current && !popRef.current.contains(e.target as Node) &&
        btnRef.current && !btnRef.current.contains(e.target as Node)
      ) setOpen(false);
    }
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, [open]);

  // Close on Escape (spec §v4 accessibility)
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") { setOpen(false); btnRef.current?.focus(); } }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  function toggle() { setOpen((p) => !p); }

  return (
    <span className="relative" style={{ display: "inline-flex", alignItems: "center" }}>
      <button
        ref={btnRef}
        onClick={toggle}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } }}
        aria-label={`Learn more about ${sectionKey}`}
        aria-expanded={open}
        aria-controls={popId}
        style={{
          width: 14, height: 14, borderRadius: "50%",
          border: "1.5px solid var(--muted-foreground)",
          background: "transparent",
          color: "var(--muted-foreground)",
          fontSize: 8, fontWeight: 700,
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          cursor: "pointer", flexShrink: 0, lineHeight: 1,
          opacity: 0.5,
          transition: "opacity 0.15s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.5")}
        onFocus={(e) => (e.currentTarget.style.opacity = "1")}
        onBlur={(e) => (e.currentTarget.style.opacity = "0.5")}
      >
        i
      </button>

      {open && (
        <div
          id={popId}
          ref={popRef}
          role="dialog"
          aria-label={`Info: ${sectionKey}`}
          className="absolute z-50"
          style={{
            top: 20, right: 0,
            width: 216,
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 10,
            boxShadow: "0 6px 24px rgba(0,0,0,0.13)",
            padding: "11px 14px 12px",
          }}
        >
          {/* X close — accessible label */}
          <button
            onClick={() => { setOpen(false); btnRef.current?.focus(); }}
            aria-label="Close"
            style={{
              position: "absolute", top: 7, right: 9,
              background: "none", border: "none", cursor: "pointer",
              color: "var(--muted-foreground)", fontSize: 14, lineHeight: 1, opacity: 0.55,
            }}
          >×</button>
          <div className="flex flex-col gap-2" aria-describedby={popId}>
            {renderInfoLines(sectionKey)}
          </div>
        </div>
      )}
    </span>
  );
}

function SectionHeader({ label, sectionKey }: { label: string; sectionKey: string }) {
  return (
    <div className="flex items-center justify-between px-4 pt-3 pb-1.5">
      <span style={{
        fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase",
        color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", fontWeight: 500,
      }}>
        {label}
      </span>
      <InfoPopover sectionKey={sectionKey} />
    </div>
  );
}

/* ─── Pair timeline ───────────────────────────────────────────────────────── */

function PairTimeline({ pairs, selectedIdx, onSelectPair }: {
  pairs: PairRow[];
  selectedIdx: number;
  onSelectPair: (idx: number) => void;
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const activeIdx = selectedIdx;

  const hovered = hoveredId ? pairs.find(p => p.id === hoveredId) : null;

  return (
    <div className="flex-1 overflow-y-auto flex flex-col" style={{ scrollbarWidth: "none" }}>
      <SectionHeader label="Timeline" sectionKey="TIMELINE" />

      {pairs.length === 0 && (
        <p className="px-3 py-2 text-xs" style={{ color: "var(--muted-foreground)" }}>
          Your conversation map will build as you chat.
        </p>
      )}

      {pairs.map((pair, i) => {
        const isActive  = i === activeIdx;
        const isHovered = hoveredId === pair.id;
        const isFuture  = i > activeIdx; // hasn't happened yet from the current vantage point
        const isNewest  = i === pairs.length - 1; // the present / live pair
        const leftW = BAR_PX[pair.leftLen ?? pair.length];
        const rightW = BAR_PX[pair.rightLen ?? pair.length];
        const CANVAS = 40;
        const TICK_X = CANVAS / 2;
        const accentColor = pair.side === "AI" ? AI_COLOR : pair.side === "BOTH" ? "#9aa0a6" : YOU_COLOR;

        return (
          <div
            key={pair.id}
            id={`pairrow-${pair.id}`}
            onClick={() => onSelectPair(i)}
            onMouseEnter={() => setHoveredId(pair.id)}
            onMouseLeave={() => setHoveredId(null)}
            className="relative flex items-center gap-0"
            style={{
              height: 32,
              paddingLeft: 12,
              paddingRight: 12,
              cursor: "pointer",
              opacity: isFuture ? 0.38 : 1,
              filter: isFuture ? "grayscale(0.6)" : "none",
              background: isHovered ? "rgba(0,0,0,0.04)" : "transparent",
              borderLeft: isActive ? `2px solid ${accentColor}` : "2px solid transparent",
              transition: "background 0.1s, border-color 0.15s, opacity 0.2s, filter 0.2s",
            }}
          >
            {/* 1. Pair label */}
            <span
              style={{
                width: 24,
                fontSize: 9,
                color: "#aaa",
                fontFamily: "'DM Mono', monospace",
                flexShrink: 0,
              }}
            >
              {pair.id}
            </span>

            {/* 2. Agency bar canvas */}
            <svg width={CANVAS} height={16} style={{ flexShrink: 0, overflow: "visible" }}>
              {/* Center tick */}
              <line x1={TICK_X} y1={0} x2={TICK_X} y2={16} stroke="#111" strokeOpacity={0.2} strokeWidth={1} />
              {/* Bar */}
              {pair.side === "YOU" && (
                <rect
                  x={TICK_X - BAR_GAP - leftW}
                  y={4}
                  width={leftW}
                  height={8}
                  rx={2}
                  fill={YOU_COLOR}
                  opacity={0.9}
                />
              )}
              {pair.side === "AI" && (
                <rect
                  x={TICK_X + BAR_GAP}
                  y={4}
                  width={rightW}
                  height={8}
                  rx={2}
                  fill={AI_COLOR}
                  opacity={0.9}
                />
              )}
              {pair.side === "BOTH" && (
                <>
                  <rect x={TICK_X - BAR_GAP - leftW} y={4} width={leftW} height={8} rx={2} fill={YOU_COLOR} opacity={0.92} />
                  <rect x={TICK_X + BAR_GAP}          y={4} width={rightW} height={8} rx={2} fill={AI_COLOR}  opacity={0.92} />
                </>
              )}
            </svg>

            {/* 3. Gap + topic */}
            <span
              style={{
                flex: 1,
                marginLeft: 10,
                fontSize: 10,
                color: "var(--foreground)",
                fontFamily: "'Inter', sans-serif",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {pair.topic}
            </span>

            {/* LIVE tag on the newest / present pair */}
            {isNewest && (
              <span
                className="flex items-center gap-1 rounded-sm shrink-0"
                style={{
                  marginLeft: 6,
                  padding: "0 4px",
                  height: 13,
                  fontSize: 8,
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  fontFamily: "'DM Mono', monospace",
                  background: "rgba(34,160,90,0.12)",
                  color: "#1f8f4e",
                }}
              >
                <span className="live-dot" style={{ width: 4, height: 4, borderRadius: "50%", background: "#22a05a", display: "inline-block" }} />
                LIVE
              </span>
            )}

            {/* 4. Mode dot */}
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: pair.side === "YOU" ? YOU_COLOR : pair.side === "AI" ? AI_COLOR : `linear-gradient(90deg, ${YOU_COLOR} 50%, ${AI_COLOR} 50%)`,
                flexShrink: 0,
                marginLeft: 8,
                display: "inline-block",
              }}
            />
          </div>
        );
      })}

      {/* Hover tooltip */}
      {hovered && (
        <div
          className="mx-3 mb-2 mt-1 rounded-lg px-3 py-2"
          style={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          <p style={{ fontSize: 9, color: "var(--muted-foreground)", fontFamily: "'DM Mono', monospace", marginBottom: 3 }}>
            {hovered.id} · Shaped by: {hovered.shapedBy === "Both" ? "You + AI" : hovered.shapedBy}
          </p>
          <p style={{ fontSize: 10, color: "var(--foreground)", lineHeight: 1.5 }}>
            {hovered.topic}
          </p>
        </div>
      )}
    </div>
  );
}

/* ─── Input box ───────────────────────────────────────────────────────────── */

function InputBox({
  textareaRef,
  input,
  loading,
  onChange,
  onKeyDown,
  onSend,
}: {
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  input: string;
  loading: boolean;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onSend: () => void;
}) {
  return (
    <div className="w-full flex flex-col gap-2">
      <div
        className="flex items-end gap-2 md:gap-3 rounded-2xl px-3 md:px-4 py-2.5 md:py-3"
        style={{ background: "var(--card)", border: "1px solid var(--border)", boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder="Message…"
          className="flex-1 resize-none bg-transparent text-sm outline-none leading-relaxed"
          style={{ color: "var(--foreground)", minHeight: 24, maxHeight: 160, scrollbarWidth: "none" }}
        />
        <button
          onClick={onSend}
          disabled={!input.trim() || loading}
          className="shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all"
          style={{
            background: input.trim() && !loading ? "var(--primary)" : "var(--accent)",
            color: input.trim() && !loading ? "var(--primary-foreground)" : "var(--muted-foreground)",
            cursor: input.trim() && !loading ? "pointer" : "default",
          }}
        >
          <Send size={14} strokeWidth={2} />
        </button>
      </div>
      <p className="text-center hidden md:block" style={{ color: "var(--muted-foreground)", fontSize: 11 }}>
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}

/* ─── Typing dots ─────────────────────────────────────────────────────────── */

function TypingDots() {
  return (
    <div className="flex items-center gap-1" style={{ height: 18 }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="block w-1.5 h-1.5 rounded-full"
          style={{ background: "var(--muted-foreground)", animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
        />
      ))}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
