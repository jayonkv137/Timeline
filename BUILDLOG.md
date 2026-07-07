# BUILDLOG — append-only session journal
Every AI session on this repo ends by appending one entry below. Newest at the bottom.
This file is the context bridge to the command center (the planning chat): after each
session, the latest entry (+ test output, + screenshot if visual) is what gets reported
back. Never paste chat transcripts anywhere.

---
ENTRY TEMPLATE (copy, fill, append):

## [YYYY-MM-DD HH:MM] · <tool: Claude Code | Antigravity> · <model>
- **Phase/Step:** P0.S2 (example)
- **Did:** files created/changed, one line each
- **Decisions made:** anything not literally dictated by the specs (and why)
- **Spec contradictions/gaps flagged:** none | description (→ goes to command center)
- **Verification:** tests run + results, or "not applicable"
- **Next:** the exact next step
---
