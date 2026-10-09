# DDR-000g: Degraded Critique Mode for Non-Claude Agents (Settlement A7)

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5 Settlement A7)
- **Phase / Step:** D0.S3
- **Affects:** Multi-Agent Protocols, QA, Critique Mode

---

## 1. Context
`ui-craft critique` normally invokes two isolated sub-agents to avoid confirmation bias during heuristic reviews. Some agent environments lack isolated sub-agent spawning mechanisms.

## 2. Decision
1. Formal phase-gate critiques run in Claude Code where isolated sub-agents and persona panels operate at full fidelity.
2. When critique runs in other agent environments without isolated sub-agents, it executes with the skill's `⚠️ DEGRADED` banner, permitted strictly between phase gates for rapid feedback.
