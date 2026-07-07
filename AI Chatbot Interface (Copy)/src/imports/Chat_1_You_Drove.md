# CHAT 1 — "YOU DROVE"  (human-led)

SCENARIO: a developer debugging their OWN code. They bring the code, form the
hypotheses, reject suggestions they don't like, catch the AI being wrong, and make
every final call. The AI only answers narrow questions.

EXPECTED WAVEFORM SILHOUETTE: a steady BLUE column hugging the LEFT, top to bottom.
Even medium lengths. A couple of tiny orange stubs at most. Reads as: "I was in
control the whole way; the AI was answering, not steering."

------------------------------------------------------------------------
User: my form input isn't updating when i type. the value just stays empty. here's the component:

function ProfileForm() {
  const [formData, setFormData] = useState({ name: "", email: "", bio: "" });
  const handleChange = (e) => {
    formData[e.target.name] = e.target.value;
    setFormData(formData);
  };
  return <input name="name" value={formData.name} onChange={handleChange} />;
}

what am i missing?

Assistant: A couple of things could cause this. The most common is that the input isn't wired as a controlled component — make sure each input has both `value` and `onChange`. Can you confirm the `onChange` is firing at all (drop a console.log in `handleChange`)?

User: no the onChange is there, look at the code — `onChange={handleChange}` is on the input. and yeah the log fires, i see it on every keystroke. the handler runs, the value just doesn't change on screen.

Assistant: Got it — then it's not a controlled-component wiring issue, it's the state update itself. Two bugs in `handleChange`: you're mutating the existing `formData` object directly (`formData[e.target.name] = ...`) and then passing the *same* object reference to `setFormData`. React compares by reference, sees the same object, and skips the re-render. You need a new object:

```
const handleChange = (e) => {
  setFormData({ ...formData, [e.target.name]: e.target.value });
};
```

User: ok that makes sense, the reference thing. but i don't love spreading the whole object on every keystroke — this form actually has like 30 fields, not 3. is there a cleaner pattern or is spread fine?

Assistant: Spread is genuinely fine performance-wise even at 30 fields — it's a shallow copy, it's cheap. But if you want it cleaner, two options: (1) `useReducer` with a single `UPDATE_FIELD` action, or (2) keep the functional update so you're not closing over stale state: `setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))`. That last one is the smallest change and also fixes a stale-closure bug you'd hit with rapid typing.

User: yeah give me the functional one, i don't want to bring in a reducer for this. let me try it. ... ok that works now for the text fields. but my checkbox is broken now — it's sending "on" instead of true/false.

Assistant: Right — checkboxes don't use `e.target.value`, they use `e.target.checked`. You'll need to branch on the input type:

```
const handleChange = (e) => {
  const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
  setFormData(prev => ({ ...prev, [e.target.name]: value }));
};
```

User: that's it, fixed. though just noting — your first answer about it being a controlled-component issue was a red herring, it was never that, it was the mutation. would've saved a step if we'd looked at the handler first.

Assistant: Fair point — you're right, I should have read the handler before suggesting the controlled-component check. The mutation was the actual bug from the start.

User: one more thing then i'm done — should i debounce the onChange, or is that overkill for a form this size?

Assistant: For a form that's just updating local state on keystroke, debouncing is overkill — it adds latency to the typing feel for no real benefit. You'd only want it if each change triggered something expensive (a network call, a heavy re-render of a big tree). Is anything firing off the change beyond the state update?

User: nope, just local state, it's an internal admin tool. then i'll skip it, perf doesn't matter here. thanks, all sorted.

------------------------------------------------------------------------
AGENCY MAP (for drawing the waveform — pair = one user msg + the AI reply):

P1  YOU led · medium    — you defined the problem + brought the code
P2  YOU led · medium    — you corrected the AI ("no, look again"), redirected the diagnosis
P3  YOU led · medium    — you rejected the spread approach, set the constraint (30 fields, no reducer); tiny AI seed (offered options)
P4  YOU led · medium    — you chose the functional update, reported the checkbox bug
P5  YOU led · small      — you caught the AI's earlier wrong diagnosis
P6  YOU led · small      — you made the final call to skip debouncing

NET: ~95% YOU. Almost pure blue, left side, even heights. No large orange anywhere.
