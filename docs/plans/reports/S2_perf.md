# S2 Performance & Budget Report

**Generated:** 2026-10-09 18:55:41 UTC  
**Branch:** `s/standalone-v1` | **Commit:** `1844ac9`  
**Platform:** Darwin 25.6.0 (arm64)  
**Python:** 3.10.18  

---

## 1. §6A T3 Budget Scorecard

| Metric | §6A T3 Budget | Measured | Margin / Factor | Status |
|---|---|---|---|---|
| **App first load** | $\le 2.0\text{ s}$ ($2000\text{ ms}$) | **305.1 ms** (0.31 s) | **6.6× faster** than budget | **PASS** |
| **Open a chat** | $\le 500\text{ ms}$ | **50.1 ms** (mean: 62.1 ms) | **10.0× faster** than budget | **PASS** |
| **Brain frame rate** | $\ge 45\text{ fps}$ | **59.8 fps** | **+14.8 fps** over target | **PASS** |
| **API /health latency** | $\le 50\text{ ms}$ | **2.40 ms** | Under 5 ms | **PASS** |
| **API /chats latency** | $\le 100\text{ ms}$ | **2.43 ms** | Under 10 ms | **PASS** |
| **API /chats/{id} bundle** | $\le 100\text{ ms}$ | **1.35 ms** | Under 10 ms | **PASS** |

> **Scorecard Verdict:** **100% OF PERFORMANCE BUDGETS MET.** Zero budget misses.

---

## 2. API Latency Benchmarks (Local FastAPI Backend)

Measurements over 50 HTTP requests per endpoint against `http://127.0.0.1:8765`:

| Endpoint | Count | Mean (ms) | p50 (ms) | p90 (ms) | p95 (ms) | Max (ms) |
|---|---|---|---|---|---|---|
| `/api/health` | 50 | 2.43 | 2.40 | 2.56 | 2.64 | 2.77 |
| `/api/chats` | 50 | 2.43 | 2.43 | 2.51 | 2.55 | 2.63 |
| `/api/chats/c05_research_medium` | 50 | 1.37 | 1.35 | 1.44 | 1.46 | 1.97 |
| `/api/chats/c04_writing_short` | 50 | 1.13 | 1.12 | 1.18 | 1.18 | 1.30 |

---

## 3. Frontend & Workspace Interaction (Playwright)

Measured in automated browser session against live server with hardware GPU:

- **First Load Time:** `305.1 ms` (DOM ready, conversation scroll attached, canvas initialized)
- **Chat Open / Tab Switch Latency:**
  - **p50:** `50.1 ms`
  - **Mean:** `62.1 ms`
  - **p95:** `110.7 ms`
  - **Individual sample switches:** 130.1ms, 52.5ms, 43.3ms, 49.6ms, 46.4ms, 50.6ms
- **3D Brain Frame Rate:** `59.8 fps` (Metal ANGLE hardware accelerated WebGL canvas loop)

---

## 4. Phase-over-Phase Comparison

| Phase | App First Load | Open Chat | Brain FPS | API Latency (p50) |
|---|---|---|---|---|
| **S0** (Prototype) | ~300 ms (static file) | ~80 ms (in-memory) | ~55 fps | N/A (no server) |
| **S1** (Engine Projections) | ~290 ms (static file) | ~80 ms (in-memory) | ~55 fps | N/A (no server) |
| **S2** (Local Server & Library) | **305.1 ms** | **50.1 ms** | **59.8 fps** | **2.43 ms** |

---

*Report committed as part of STANDALONE_V1_PLAN Step S2.7 Definition of Done.*
