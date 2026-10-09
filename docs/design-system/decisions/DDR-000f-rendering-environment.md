# DDR-000f: Visual Rendering & Preview Environment (Settlement A6)

- **Status:** Ratified
- **Date:** 2026-10-08
- **Decider:** Owner (via D Track Brief §5 Settlement A6)
- **Phase / Step:** D0.S3
- **Affects:** Tooling, Testing Harness, Mockups

---

## 1. Context
`ui-craft` references an optional `drive-local-webapp` skill for browser rendering that is not installed in this repository.

## 2. Decision
1. In Claude Code, mockups are served via `.claude/launch.json` and previewed directly in the integrated browser pane.
2. In other AI tools (Codex, Antigravity), preview is served via `python3 -m http.server 4178 --directory mockups`.
3. Automated render verification and headless screenshot capture will be executed via Playwright scripts located in `scripts/design_system/`.
