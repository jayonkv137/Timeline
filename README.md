<div align="center">
  <img src="docs/symbiot/logo/symbiot-lockup.png" alt="Symbiot Logo" width="340" />
  <p><strong>A live cognitive map for human–AI dialogue</strong></p>
  <p><em>See who shaped each goal, link every requirement to its exact words, and watch your dialogue graph form in real time.</em></p>

  <p>
    <a href="#-quick-start-3-steps"><img src="https://img.shields.io/badge/Quickstart-3_Commands-6366f1?style=flat-square" alt="Quickstart" /></a>
    <img src="https://img.shields.io/badge/Tests-323_passed-10b981?style=flat-square" alt="Tests" />
    <img src="https://img.shields.io/badge/Python-3.10+-3b82f6?style=flat-square" alt="Python" />
    <img src="https://img.shields.io/badge/React-18.x-06b6d4?style=flat-square" alt="React" />
    <img src="https://img.shields.io/badge/Course-Designing_for_Competence-8b5cf6?style=flat-square" alt="Course" />
    <img src="https://img.shields.io/badge/License-MIT-f59e0b?style=flat-square" alt="License" />
  </p>
</div>

---

![Symbiot Workspace Interface](docs/symbiot/website/jkv-symbiot-01.jpg)

## 🌟 What is Symbiot?

When we chat with AI assistants, the conversation scrolls away and it becomes difficult to answer three simple questions:
1. **Who actually introduced each requirement—me or the AI?**
2. **Where in the dialogue was each decision made?**
3. **How balanced is our collaboration across conversations?**

**Symbiot** acts as a live cognitive companion alongside your chats. It analyses conversations pair-by-pair, mapping them into an interactive goal tree where:
- **Blue nodes (`#38bdf8`)** represent requirements you introduced.
- **Orange nodes (`#fb923c`)** represent requirements introduced by the AI.
- **Click any node** to instantly jump to the exact quotation in the chat and highlight it.
- **Scrub the timeline** backward to see how the graph developed exchange by exchange.
- **The Brain view** brings all your mapped conversations together into a unified 3D landscape.

Built as a semester project for **Designing for Competence** (Lecturer: *Peter Von Maydell*, Student: *Jayon K Vinod*, 2026), extending the research foundation of **CoTrace** (*Kim et al., arXiv:2605.21363*).

---

## 🚀 Quick Start (3 Steps)

Anyone can get Symbiot up and running on macOS, Linux, or Windows (WSL) in under three minutes.

### 1. Prerequisites
- **Python**: 3.10+ installed ([python.org](https://www.python.org/downloads/))
- **Node.js**: 18+ installed ([nodejs.org](https://nodejs.org/))

### 2. Install
Open your terminal and run:

```bash
# 1. Clone repository
git clone https://github.com/jayonkv137/Timeline.git symbiot
cd symbiot

# 2. Setup Python environment & dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install frontend dependencies
npm --prefix web install
```

### 3. Launch
Run the unified launcher:

```bash
./cotrace start
```

That's it! Symbiot will:
- Check and compile the frontend workspace bundle automatically.
- Seed **10 curated reference chats** into your local library if empty.
- Start the server at `http://localhost:8765`.
- Automatically open your browser to the working interface.

---

## 🧭 Two Ways to Evaluate Symbiot

### Track A: Zero-Spend Evaluation ($0.00 · No API Key Required)
You **do not need an API key** to evaluate Symbiot's core interactions:
- **10 Reference Chats Ready Out-of-the-Box**: Spanning research, creative writing, and coding.
- **Interactive Graph**: Click nodes, hover over outcome clusters, and pan the canvas.
- **Word-Level Citations**: Click any requirement node; the chat scrolls immediately to the verbatim sentence and highlights it with a provenance badge (*"Introduced by the AI · exchange 3"*).
- **Timeline Scrubbing**: Drag the scrub bar or use arrow keys to replay previous exchanges.
- **Multi-Chat Brain Overview**: Click the Brain icon in the sidebar to view the 3D semantic canvas.

---

### Track B: Live Mapping with Your Own Chats & API Key
If you want to map your own conversations in real time, you can connect an API key and drop in any chat export.

#### 1. Connecting Your API Key (Safe & Isolated)
1. In the bottom-left sidebar, click the **Settings (gear icon)**.
2. Under **Provider & Authentication**, paste a Google Gemini API key (recommended; free tier available at [aistudio.google.com](https://aistudio.google.com)).
3. Click **Test Connection** (you will see a green checkmark confirming connectivity) and click **Save Settings**.

> **🔒 Zero-Leak Security Guarantee:**
> - Your API key is stored locally on your machine at `~/.Cotrace/secrets.json` with strict POSIX permissions `0600` (readable only by your user account).
> - It is **never** committed to Git, **never** bundled into frontend code, and **never** exposed over API endpoints (`GET /api/settings` returns only `has_api_key: true` and masked `••••••••`).
> - A configurable monthly budget cap (default: $20) guards against accidental overspend.

---

#### 2. Uploading Any Chat (Claude, ChatGPT, or Custom JSON)

Symbiot includes a universal chat importer that works with:
- **Claude.ai Data Exports**: Drag & drop `conversations.json` or your full `.zip` export (from Claude *Settings → Account → Export Data*).
- **ChatGPT Data Exports**: Drag & drop `conversations.json` or your `.zip` export (from ChatGPT *Settings → Data Controls → Export Data*).
- **Custom JSON Transcripts**: Drag & drop any `.json` containing an array of turns:
  ```json
  [
    { "pair": 1, "speaker": "user", "text": "I want to design an interactive museum kiosk." },
    { "pair": 1, "speaker": "assistant", "text": "Here is a conceptual framework with three areas..." }
  ]
  ```
- **Live In-App Chat**: Click the **`+` (New Chat)** icon in the sidebar header to chat directly inside Symbiot.

##### Step-by-Step Upload Workflow:
1. Click the **Upload (tray icon)** in the sidebar header.
2. Drop your `.zip` or `.json` file into the dashed dropzone.
3. Symbiot scans the archive locally and displays a summary table with conversation titles, message counts, and platform badges.
4. Select the conversation you want and click **Import & Map** (or click **"Map this conversation"** from the workspace header at any time).
5. Watch the **live synaptogenesis**:
   - The map grows exchange by exchange in the background.
   - New branches form directly from the central root node with orbiting Sky (`#38bdf8`) and Ember (`#fb923c`) particles.
   - Requirement dots crystallize as each turn is classified, and the agency balance donut updates dynamically.

---

## 📸 Key Features in Action

| 1. Live Synaptogenesis & Mapping | 2. Word-Level Exact Citations |
| :---: | :---: |
| ![Mapping](docs/symbiot/website/jkv-symbiot-03.jpg) | ![Citations](docs/symbiot/website/jkv-symbiot-05.jpg) |
| *Background analysis adds new requirements pair by pair.* | *Clicking any dot highlights the verbatim sentence in the chat.* |

| 3. Replay & Timeline Scrubbing | 4. 3D Multi-Chat Brain Canvas |
| :---: | :---: |
| ![Timeline Replay](docs/symbiot/website/jkv-symbiot-06.jpg) | ![Brain Canvas](docs/symbiot/website/jkv-symbiot-07.jpg) |
| *Step back to exchange 1 to see where the AI took over.* | *All chats clustered into semantic territories with agency balance.* |

---

## 🏗️ Architecture

```
Timeline/
├── cotrace                    # Unified CLI launcher (./cotrace start | dev | seed)
├── web/                       # Frontend application
│   ├── src/workspace/         # React workspace (LocalGraph, Timeline, Chat, ImportModal)
│   ├── src/design-system/     # Design tokens (colors, typography, spacing, shadows)
│   └── vite.workspace.config.ts # Single-file workspace bundler
├── server/                    # Local FastAPI backend
│   ├── app.py                 # REST & SSE endpoints (/api/chats, /api/imports, /api/events)
│   ├── library.py             # File-based library manager ($COTRACE_HOME/chats)
│   ├── jobs.py                # Asynchronous background job queue
│   └── pipeline_runner.py     # Sequential pair-by-pair pipeline coordinator
├── engine/                    # Cognitive extraction engine
│   ├── importer.py            # Claude / ChatGPT archive scanner & parser
│   ├── models.py              # Schema contracts & token cost calculation
│   └── llm.py                 # OpenAI-compatible multi-provider client (Gemini default)
├── scripts/
│   └── seed_library.py        # Deterministic 10-chat library seeder ($0 LLM calls)
└── docs/                      # Architectural specifications & documentation
    └── symbiot/               # Symbiot documentation, screenshots, and identity assets
```

---

## 🧪 Testing & Verification

The backend and frontend are strictly tested for reproducibility and product invariants:

```bash
# Run the complete test suite (323 unit & integration tests)
.venv/bin/pytest tests/ -q

# Recompile the workspace bundle
npm --prefix web run build:workspace
```

---

## 📚 Credits & Academic Context

- **Author**: Jayon K Vinod
- **Course**: *Designing for Competence* (October 2026)
- **Lecturer / Evaluator**: Peter Von Maydell
- **Research Foundation**: Built on **CoTrace**: *Kim, Mindel, Kim and Wu*, [Measuring AI Contributions to Goal Shaping](https://arxiv.org/abs/2605.21363) (arXiv:2605.21363).
- **Detailed Documentation**: See [docs/symbiot/symbiot-documentation.md](docs/symbiot/symbiot-documentation.md) for full project walkthrough, limitations, and prompt logs.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
