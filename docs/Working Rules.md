# WORKING_RULES.md

How anyone works on this repository. Any role, now or later.

---

## The whole thing

```
The repo is the only shared memory. Write it down or it didn't happen.
One writer per path.
One step at a time. Say where we are, do the work, say what's next.
No code in the response. The files are in the editor.
Stuck twice? Stop and report.
```

---

## 1. Three principles

**The repo is the only shared memory.** No chat sees another chat. Specs, code,
`BUILDLOG.md`, `STATUS.md` and git are how anyone learns anything. Describe files, never
conversations.

**One writer per path.** Every directory has one role that writes it. Everyone else reads.

**One step at a time.** A step is one thing that can be run and seen to work. The owner has
to understand every part of this system well enough to defend it.

---

## 2. Roles

A role is five lines in `ROLES.md`. Not a document.

An agent reads four files before starting: `AGENTS.md`, this one, its entry in `ROLES.md`,
its brief. Then whatever its brief says to read.

---

## 3. A session

### Start

1. Pull, read `STATUS.md`
2. Read any new HANDOFF, BLOCKED or NOTICE from other roles
3. Read the repo itself before reading any brief. Then say what you found and what looks
   wrong, and wait.

Point 3 matters. Briefs are plans, code is evidence. Where they disagree, say so. That is
always welcome.

### Before a step

Five short things:

- **Where we are.** One line placing this step in the whole build. What the system can do
  now, and what this adds.
- **What this does.** Plain language.
- **Example.** A few lines using real project data. Input, and what comes out.
- **What you decide first.** Often nothing. Say so.
- **Size.** Roughly how many files and how much code.

Half a page. Then wait.

### After a step

Four short things:

- **Done.** Which files were written, and what to open and look at. **No code in the
  response** beyond a few lines if one specific bit is worth the owner's eye. The files
  are in the editor.
- **Ran.** The command and its actual output. Not a claim that it passed.
- **Check yourself.** A short list the owner can run.
- **What this unlocked.** What the system can now do that it could not, and what the next
  step is.

Then stop.

### Rhythm

`start task` begins. `Finish Step` advances. A question gets an answer, not a ritual.

This applies to work that changes files. A lookup is just a lookup.

### End

Log entry, regenerate `STATUS.md`, commit, push. Even if the session went badly,
especially then. A session with no entry did not happen.

---

## 4. The log

`BUILDLOG.md`, append only, newest at the bottom.

```
## 2026-09-19 — [ENGINE] WORK — E1.S2
Files: engine/pipeline.py, tests/test_step2.py
Did: Step 2, decision extraction
Decided: one model call per goal, not per pair
Ran: pytest -m tier1 -> 58 passed
Next: S3
```

| type | when |
|---|---|
| **WORK** | normal step |
| **HANDOFF** | something another role waited on is ready |
| **BLOCKED** | can't continue without someone else |
| **NOTICE** | changed something others read |

NOTICE matters most. Change the corpus, a schema or a spec and say so, or others find out
by breaking.

---

## 5. STATUS.md

Generated, never typed. Where each role is, what's blocked, what the owner still owes,
test and data health, open questions. Regenerate at the end of every session.

---

## 6. When stuck

Two attempts, then stop and report. Looping is not progress.

Spec unclear: log it in `SPEC_QUESTIONS.md` with what you chose and why, take the reading
that changes least, mark `REVISIT`, continue.

Anything touching a number or a sum: never guess. Stop and log it.

Need someone else's files: write BLOCKED, stop. Don't reach across.

---

## 7. As this grows

New roles are five lines. New phases are a brief. This file should not need to change.

If it starts growing, cut it back to the five lines at the top rather than adding a
section.
