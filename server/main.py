import json
import logging
from pathlib import Path
import uuid
import os
import datetime
import asyncio
import shutil
from typing import Dict, Set, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

from engine.state import State
from engine.artifacts import write_json_artifact, read_ledger
from engine.quant import compute_stage4, write_stage4_artifacts
from engine.config import load_config, _load_dotenv, REPO_ROOT

config = load_config()
dotenv = _load_dotenv(REPO_ROOT / ".env")
CHAT_MODEL = os.environ.get("CHAT_MODEL") or dotenv.get("CHAT_MODEL") or config.model_main

async_client = None
if config.llm_api_key:
    async_client = AsyncOpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI(title="Timeline Web Server")

# In-memory registries for chat-level execution and events
chat_locks: Dict[str, asyncio.Lock] = {}
chat_event_listeners: Dict[str, Set[asyncio.Queue]] = {}

def broadcast_event(chat_id: str, payload: str):
    """Sends SSE payload to all active queues for this chat_id."""
    if chat_id in chat_event_listeners:
        for q in list(chat_event_listeners[chat_id]):
            q.put_nowait(payload)

def send_pipeline_status(chat_id: str, phase: str, pair: int):
    """Broadcasts pipeline status change."""
    data = json.dumps({"phase": phase, "pair": pair})
    msg = f"event: pipeline_status\ndata: {data}\n\n"
    broadcast_event(chat_id, msg)

def send_pair_ready(chat_id: str, pair: int):
    """Broadcasts pair completion event."""
    msg = f"event: pair_ready\ndata: {json.dumps({'pair': pair})}\n\n"
    broadcast_event(chat_id, msg)

def write_run_status(chat_dir: Path, status: str, pair: int, error: str = None):
    """Saves persistent execution status to run/status.json."""
    status_path = chat_dir / "run" / "status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with open(status_path, "w") as f:
        json.dump({
            "status": status,
            "pair": pair,
            "error": error
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")

# CORS middleware for Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHATS_DIR = Path(__file__).resolve().parent.parent / "data" / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)

class TitleUpdate(BaseModel):
    title: str

def get_chat_title_from_state(chat_dir: Path) -> str:
    state_path = chat_dir / "state.json"
    if not state_path.exists():
        return "New Chat"
    try:
        with open(state_path) as f:
            data = json.load(f)
        outcomes = data.get("outcomes", [])
        # Find root outcome (parent is None)
        for outcome in outcomes:
            if outcome.get("parent") is None:
                return outcome.get("text", "New Chat")
        if outcomes:
            return outcomes[0].get("text", "New Chat")
    except Exception as e:
        logger.error(f"Error reading state.json for title: {e}")
    return "New Chat"

@app.get("/chats")
def list_chats():
    chats = []
    for item in CHATS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Check if state.json exists, otherwise it's just "New Chat"
            title = get_chat_title_from_state(item)
            chats.append({
                "id": item.name,
                "title": title
            })
    # Sort by directory name
    chats.sort(key=lambda x: x["id"])
    return chats

class ChatCreateRequest(BaseModel):
    template: Optional[str] = None

@app.post("/chats")
def create_chat(payload: ChatCreateRequest = ChatCreateRequest()):
    template = payload.template
    chat_id = str(uuid.uuid4())
    chat_dir = CHATS_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if template == "website":
            # Copy all files from fixture_pair1 if it exists
            fixture_dir = CHATS_DIR / "fixture_pair1"
            if fixture_dir.exists():
                for item in fixture_dir.iterdir():
                    if item.is_file():
                        shutil.copy(item, chat_dir)
            else:
                # Default empty creation if fixture doesn't exist
                write_json_artifact(chat_dir / "dialogue.json", [], "dialogue")
                write_json_artifact(chat_dir / "snapshots.json", [], "snapshots")
                write_json_artifact(chat_dir / "panel_bundle.json", {"pairs": []}, "panel_bundle")
                state = State()
                state.save(chat_dir)
                (chat_dir / "ledger.jsonl").touch(exist_ok=True)
        elif template == "trip":
            # Write 2-pair trip plan templates
            dialogue_data = [
                {
                    "pair": 1,
                    "speaker": "user",
                    "text": "I want to help you plan a trip to Tokyo.",
                    "attachments": [],
                    "ts": "2026-07-08T08:00:00Z"
                },
                {
                    "pair": 1,
                    "speaker": "ai",
                    "text": "Excellent! Goal: Tokyo Exploration Itinerary. We require Shinjuku visits and a day-trip to Mount Fuji.",
                    "attachments": [],
                    "ts": "2026-07-08T08:01:00Z"
                },
                {
                    "pair": 2,
                    "speaker": "user",
                    "text": "Add a Tsukiji food tour to the itinerary.",
                    "attachments": [],
                    "ts": "2026-07-08T08:02:00Z"
                },
                {
                    "pair": 2,
                    "speaker": "ai",
                    "text": "Added Tsukiji food tour and selected fresh sushi stalls.",
                    "attachments": [],
                    "ts": "2026-07-08T08:03:00Z"
                }
            ]
            write_json_artifact(chat_dir / "dialogue.json", dialogue_data, "dialogue")
            
            panel_bundle_data = {
              "pairs": [
                {
                  "pair": 1,
                  "direction": {
                    "you_pct": 30.0,
                    "ai_pct": 70.0
                  },
                  "decisions": {
                    "you_count": 1,
                    "ai_count": 2,
                    "latest_ai_example": "Mount Fuji day-trip"
                  },
                  "timeline": {
                    "pair": 1,
                    "delta_you": 10.0,
                    "delta_ai": 30.0,
                    "summary": "added Mount Fuji day-trip requirement",
                    "drawer": {
                      "requirements": [
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 1",
                          "label": "R1",
                          "op": "create",
                          "delta_you": 10.0,
                          "delta_ai": 0.0,
                          "chip": "blue"
                        },
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 2",
                          "label": "R2",
                          "op": "create",
                          "delta_you": 0.0,
                          "delta_ai": 30.0,
                          "chip": "orange"
                        }
                      ],
                      "slots": []
                    }
                  },
                  "goal": {
                    "default_view": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Tokyo Exploration Itinerary",
                        "depth": 0,
                        "is_current": true
                      }
                    ],
                    "full_tree": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Tokyo Exploration Itinerary",
                        "depth": 0,
                        "parent": None,
                        "children": []
                      }
                    ]
                  },
                  "how": {
                    "mode": "COPILOT",
                    "signals": {
                      "w_you": 1,
                      "w_ai": 2,
                      "h_you": 10.0,
                      "h_ai": 30.0,
                      "substantive_user": True
                    },
                    "split": {
                      "centaur_pct": 0.0,
                      "copilot_pct": 100.0,
                      "autopilot_pct": 0.0
                    }
                  }
                },
                {
                  "pair": 2,
                  "direction": {
                    "you_pct": 45.0,
                    "ai_pct": 55.0
                  },
                  "decisions": {
                    "you_count": 2,
                    "ai_count": 3,
                    "latest_ai_example": "Tsukiji Food Tour selection"
                  },
                  "timeline": {
                    "pair": 2,
                    "delta_you": 20.0,
                    "delta_ai": 15.0,
                    "summary": "added Tsukiji food tour",
                    "drawer": {
                      "requirements": [
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 3",
                          "label": "R3",
                          "op": "create",
                          "delta_you": 20.0,
                          "delta_ai": 0.0,
                          "chip": "blue"
                        },
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 4",
                          "label": "R4",
                          "op": "create",
                          "delta_you": 0.0,
                          "delta_ai": 15.0,
                          "chip": "orange"
                        }
                      ],
                      "slots": []
                    }
                  },
                  "goal": {
                    "default_view": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Tokyo Exploration Itinerary",
                        "depth": 0,
                        "is_current": true
                      }
                    ],
                    "full_tree": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Tokyo Exploration Itinerary",
                        "depth": 0,
                        "parent": None,
                        "children": []
                      }
                    ]
                  },
                  "how": {
                    "mode": "COPILOT",
                    "signals": {
                      "w_you": 2,
                      "w_ai": 3,
                      "h_you": 30.0,
                      "h_ai": 45.0,
                      "substantive_user": True
                    },
                    "split": {
                      "centaur_pct": 0.0,
                      "copilot_pct": 100.0,
                      "autopilot_pct": 0.0
                    }
                  }
                }
              ]
            }
            write_json_artifact(chat_dir / "panel_bundle.json", panel_bundle_data, "panel_bundle")
            
            snapshots_data = [
                {"t": 1, "delta_you": 10.0, "delta_ai": 30.0, "c_you": 10.0, "c_ai": 30.0},
                {"t": 2, "delta_you": 20.0, "delta_ai": 15.0, "c_you": 30.0, "c_ai": 45.0}
            ]
            write_json_artifact(chat_dir / "snapshots.json", snapshots_data, "snapshots")
            
            state_data = {
              "actions": [
                {"id": "U(1,1)", "type": "Request", "text": "Plan trip", "role": "SHAPER", "evidence_quote": "plan"},
                {"id": "A(1,1)", "type": "Accept", "text": "Will do", "role": "EXECUTOR", "evidence_quote": "Exploration"},
                {"id": "U(2,1)", "type": "Request", "text": "Add food tour", "role": "SHAPER", "evidence_quote": "food tour"},
                {"id": "A(2,1)", "type": "Accept", "text": "Added Tsukiji", "role": "EXECUTOR", "evidence_quote": "Added Tsukiji"}
              ],
              "outcomes": [
                {
                  "id": "outcome 1",
                  "text": "Tokyo Exploration Itinerary",
                  "turn_id": "U(1,1)",
                  "parent": None,
                  "children": [],
                  "related": []
                }
              ],
              "intentions": [
                {"intention_id": "I1", "intention": "Tokyo Trip Plan", "outcome_ids": ["outcome 1"]}
              ],
              "requirements": [
                {"outcome_id": "outcome 1", "req_id": "req 1", "text": "Visit Shinjuku", "type": "other", "status": "active", "creation_action_ids": ["U(1,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "essential", "created_at_pair": 1},
                {"outcome_id": "outcome 1", "req_id": "req 2", "text": "Mount Fuji day-trip", "type": "other", "status": "active", "creation_action_ids": ["A(1,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "popular request", "created_at_pair": 1},
                {"outcome_id": "outcome 1", "req_id": "req 3", "text": "Tsukiji Food Tour", "type": "other", "status": "active", "creation_action_ids": ["U(2,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "explore local food", "created_at_pair": 2},
                {"outcome_id": "outcome 1", "req_id": "req 4", "text": "Fresh Sushi stalls", "type": "other", "status": "active", "creation_action_ids": ["A(2,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "Tsukiji specialty", "created_at_pair": 2}
              ],
              "slots": [],
              "operations_log": [
                {"pair": 1, "outcome_id": "outcome 1", "op": "create", "target_id": "req 1", "target_type": "requirement"},
                {"pair": 1, "outcome_id": "outcome 1", "op": "create", "target_id": "req 2", "target_type": "requirement"},
                {"pair": 2, "outcome_id": "outcome 1", "op": "create", "target_id": "req 3", "target_type": "requirement"},
                {"pair": 2, "outcome_id": "outcome 1", "op": "create", "target_id": "req 4", "target_type": "requirement"}
              ]
            }
            write_json_artifact(chat_dir / "state.json", state_data, "state")
            
            ledger_lines = [
                {"pair_added": 1, "action_id": "U(1,1)", "speaker": "U", "role": "SHAPER", "outcome_id": "outcome 1", "req_id": "req 1", "score": 10.0, "kind": "creation"},
                {"pair_added": 1, "action_id": "A(1,1)", "speaker": "A", "role": "EXECUTOR", "outcome_id": "outcome 1", "req_id": "req 2", "score": 30.0, "kind": "creation"},
                {"pair_added": 2, "action_id": "U(2,1)", "speaker": "U", "role": "SHAPER", "outcome_id": "outcome 1", "req_id": "req 3", "score": 20.0, "kind": "creation"},
                {"pair_added": 2, "action_id": "A(2,1)", "speaker": "A", "role": "EXECUTOR", "outcome_id": "outcome 1", "req_id": "req 4", "score": 15.0, "kind": "creation"}
            ]
            with open(chat_dir / "ledger.jsonl", "w") as f:
                for line in ledger_lines:
                    f.write(json.dumps(line) + "\n")
        elif template == "fantasy":
            # Write 3-pair fantasy story templates
            dialogue_data = [
                {
                    "pair": 1,
                    "speaker": "user",
                    "text": "I want to write a fantasy story about a floating island.",
                    "attachments": [],
                    "ts": "2026-07-08T08:00:00Z"
                },
                {
                    "pair": 1,
                    "speaker": "ai",
                    "text": "Excellent. Goal: Floating Island Worldbuilding. We require that the island is powered by glowing crystals.",
                    "attachments": [],
                    "ts": "2026-07-08T08:01:00Z"
                },
                {
                    "pair": 2,
                    "speaker": "user",
                    "text": "Add a faction of sky pirates.",
                    "attachments": [],
                    "ts": "2026-07-08T08:02:00Z"
                },
                {
                    "pair": 2,
                    "speaker": "ai",
                    "text": "Added sky pirate faction as requested under worldbuilding.",
                    "attachments": [],
                    "ts": "2026-07-08T08:03:00Z"
                },
                {
                    "pair": 3,
                    "speaker": "user",
                    "text": "Let's require a giant leviathan monster in the clouds.",
                    "attachments": [],
                    "ts": "2026-07-08T08:04:00Z"
                },
                {
                    "pair": 3,
                    "speaker": "ai",
                    "text": "Added Cloud Leviathan as a legendary creature requirement.",
                    "attachments": [],
                    "ts": "2026-07-08T08:05:00Z"
                }
            ]
            write_json_artifact(chat_dir / "dialogue.json", dialogue_data, "dialogue")
            
            panel_bundle_data = {
              "pairs": [
                {
                  "pair": 1,
                  "direction": {
                    "you_pct": 50.0,
                    "ai_pct": 50.0
                  },
                  "decisions": {
                    "you_count": 1,
                    "ai_count": 1,
                    "latest_ai_example": "glowing crystal power source"
                  },
                  "timeline": {
                    "pair": 1,
                    "delta_you": 10.0,
                    "delta_ai": 10.0,
                    "summary": "crystal power source",
                    "drawer": {
                      "requirements": [
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 1",
                          "label": "R1",
                          "op": "create",
                          "delta_you": 10.0,
                          "delta_ai": 0.0,
                          "chip": "blue"
                        },
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 2",
                          "label": "R2",
                          "op": "create",
                          "delta_you": 0.0,
                          "delta_ai": 10.0,
                          "chip": "orange"
                        }
                      ],
                      "slots": []
                    }
                  },
                  "goal": {
                    "default_view": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Floating Island Worldbuilding",
                        "depth": 0,
                        "is_current": true
                      }
                    ],
                    "full_tree": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Floating Island Worldbuilding",
                        "depth": 0,
                        "parent": None,
                        "children": []
                      }
                    ]
                  },
                  "how": {
                    "mode": "COPILOT",
                    "signals": {
                      "w_you": 1,
                      "w_ai": 1,
                      "h_you": 10.0,
                      "h_ai": 10.0,
                      "substantive_user": True
                    },
                    "split": {
                      "centaur_pct": 0.0,
                      "copilot_pct": 100.0,
                      "autopilot_pct": 0.0
                    }
                  }
                },
                {
                  "pair": 2,
                  "direction": {
                    "you_pct": 45.0,
                    "ai_pct": 55.0
                  },
                  "decisions": {
                    "you_count": 2,
                    "ai_count": 2,
                    "latest_ai_example": "sky pirate faction"
                  },
                  "timeline": {
                    "pair": 2,
                    "delta_you": 10.0,
                    "delta_ai": 15.0,
                    "summary": "sky pirate faction",
                    "drawer": {
                      "requirements": [
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 3",
                          "label": "R3",
                          "op": "create",
                          "delta_you": 10.0,
                          "delta_ai": 0.0,
                          "chip": "blue"
                        },
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 4",
                          "label": "R4",
                          "op": "create",
                          "delta_you": 0.0,
                          "delta_ai": 15.0,
                          "chip": "orange"
                        }
                      ],
                      "slots": []
                    }
                  },
                  "goal": {
                    "default_view": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Floating Island Worldbuilding",
                        "depth": 0,
                        "is_current": true
                      }
                    ],
                    "full_tree": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Floating Island Worldbuilding",
                        "depth": 0,
                        "parent": None,
                        "children": []
                      }
                    ]
                  },
                  "how": {
                    "mode": "COPILOT",
                    "signals": {
                      "w_you": 2,
                      "w_ai": 2,
                      "h_you": 20.0,
                      "h_ai": 25.0,
                      "substantive_user": True
                    },
                    "split": {
                      "centaur_pct": 0.0,
                      "copilot_pct": 100.0,
                      "autopilot_pct": 0.0
                    }
                  }
                },
                {
                  "pair": 3,
                  "direction": {
                    "you_pct": 40.0,
                    "ai_pct": 60.0
                  },
                  "decisions": {
                    "you_count": 3,
                    "ai_count": 3,
                    "latest_ai_example": "cloud leviathan"
                  },
                  "timeline": {
                    "pair": 3,
                    "delta_you": 10.0,
                    "delta_ai": 20.0,
                    "summary": "cloud leviathan",
                    "drawer": {
                      "requirements": [
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 5",
                          "label": "R5",
                          "op": "create",
                          "delta_you": 10.0,
                          "delta_ai": 0.0,
                          "chip": "blue"
                        },
                        {
                          "outcome_id": "outcome 1",
                          "req_id": "req 6",
                          "label": "R6",
                          "op": "create",
                          "delta_you": 0.0,
                          "delta_ai": 20.0,
                          "chip": "orange"
                        }
                      ],
                      "slots": []
                    }
                  },
                  "goal": {
                    "default_view": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Floating Island Worldbuilding",
                        "depth": 0,
                        "is_current": true
                      }
                    ],
                    "full_tree": [
                      {
                        "outcome_id": "outcome 1",
                        "text": "Floating Island Worldbuilding",
                        "depth": 0,
                        "parent": None,
                        "children": []
                      }
                    ]
                  },
                  "how": {
                    "mode": "COPILOT",
                    "signals": {
                      "w_you": 3,
                      "w_ai": 3,
                      "h_you": 30.0,
                      "h_ai": 45.0,
                      "substantive_user": True
                    },
                    "split": {
                      "centaur_pct": 0.0,
                      "copilot_pct": 100.0,
                      "autopilot_pct": 0.0
                    }
                  }
                }
              ]
            }
            write_json_artifact(chat_dir / "panel_bundle.json", panel_bundle_data, "panel_bundle")
            
            snapshots_data = [
                {"t": 1, "delta_you": 10.0, "delta_ai": 10.0, "c_you": 10.0, "c_ai": 10.0},
                {"t": 2, "delta_you": 10.0, "delta_ai": 15.0, "c_you": 20.0, "c_ai": 25.0},
                {"t": 3, "delta_you": 10.0, "delta_ai": 20.0, "c_you": 30.0, "c_ai": 45.0}
            ]
            write_json_artifact(chat_dir / "snapshots.json", snapshots_data, "snapshots")
            
            state_data = {
              "actions": [
                {"id": "U(1,1)", "type": "Request", "text": "Float story", "role": "SHAPER", "evidence_quote": "floating island"},
                {"id": "A(1,1)", "type": "Accept", "text": "glowing crystal requirement", "role": "EXECUTOR", "evidence_quote": "crystals"},
                {"id": "U(2,1)", "type": "Request", "text": "Sky pirates", "role": "SHAPER", "evidence_quote": "sky pirates"},
                {"id": "A(2,1)", "type": "Accept", "text": "Added sky pirate faction", "role": "EXECUTOR", "evidence_quote": "Added sky pirate"},
                {"id": "U(3,1)", "type": "Request", "text": "leviathan monster", "role": "SHAPER", "evidence_quote": "leviathan monster"},
                {"id": "A(3,1)", "type": "Accept", "text": "Added Cloud Leviathan", "role": "EXECUTOR", "evidence_quote": "Added Cloud Leviathan"}
              ],
              "outcomes": [
                {
                  "id": "outcome 1",
                  "text": "Floating Island Worldbuilding",
                  "turn_id": "U(1,1)",
                  "parent": None,
                  "children": [],
                  "related": []
                }
              ],
              "intentions": [
                {"intention_id": "I1", "intention": "Floating Island Worldbuilding", "outcome_ids": ["outcome 1"]}
              ],
              "requirements": [
                {"outcome_id": "outcome 1", "req_id": "req 1", "text": "Floating Island", "type": "other", "status": "active", "creation_action_ids": ["U(1,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "essential setting", "created_at_pair": 1},
                {"outcome_id": "outcome 1", "req_id": "req 2", "text": "Glowing Crystal power source", "type": "other", "status": "active", "creation_action_ids": ["A(1,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "unique energy", "created_at_pair": 1},
                {"outcome_id": "outcome 1", "req_id": "req 3", "text": "Sky Pirate Faction", "type": "other", "status": "active", "creation_action_ids": ["U(2,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "adds conflict", "created_at_pair": 2},
                {"outcome_id": "outcome 1", "req_id": "req 4", "text": "Sky pirate rules", "type": "other", "status": "active", "creation_action_ids": ["A(2,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "faction logic", "created_at_pair": 2},
                {"outcome_id": "outcome 1", "req_id": "req 5", "text": "Cloud Leviathan", "type": "other", "status": "active", "creation_action_ids": ["U(3,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "legendary beast", "created_at_pair": 3},
                {"outcome_id": "outcome 1", "req_id": "req 6", "text": "Monster behavior", "type": "other", "status": "active", "creation_action_ids": ["A(3,1)"], "contributing_action_ids": [], "implementation_action_ids": [], "revise_action_ids": [], "related_to": [], "explicit_or_implicit": "explicit", "rationale": "Cloud leviathan lore", "created_at_pair": 3}
              ],
              "slots": [],
              "operations_log": [
                {"pair": 1, "outcome_id": "outcome 1", "op": "create", "target_id": "req 1", "target_type": "requirement"},
                {"pair": 1, "outcome_id": "outcome 1", "op": "create", "target_id": "req 2", "target_type": "requirement"},
                {"pair": 2, "outcome_id": "outcome 1", "op": "create", "target_id": "req 3", "target_type": "requirement"},
                {"pair": 2, "outcome_id": "outcome 1", "op": "create", "target_id": "req 4", "target_type": "requirement"},
                {"pair": 3, "outcome_id": "outcome 1", "op": "create", "target_id": "req 5", "target_type": "requirement"},
                {"pair": 3, "outcome_id": "outcome 1", "op": "create", "target_id": "req 6", "target_type": "requirement"}
              ]
            }
            write_json_artifact(chat_dir / "state.json", state_data, "state")
            
            ledger_lines = [
                {"pair_added": 1, "action_id": "U(1,1)", "speaker": "U", "role": "SHAPER", "outcome_id": "outcome 1", "req_id": "req 1", "score": 10.0, "kind": "creation"},
                {"pair_added": 1, "action_id": "A(1,1)", "speaker": "A", "role": "EXECUTOR", "outcome_id": "outcome 1", "req_id": "req 2", "score": 10.0, "kind": "creation"},
                {"pair_added": 2, "action_id": "U(2,1)", "speaker": "U", "role": "SHAPER", "outcome_id": "outcome 1", "req_id": "req 3", "score": 10.0, "kind": "creation"},
                {"pair_added": 2, "action_id": "A(2,1)", "speaker": "A", "role": "EXECUTOR", "outcome_id": "outcome 1", "req_id": "req 4", "score": 15.0, "kind": "creation"},
                {"pair_added": 3, "action_id": "U(3,1)", "speaker": "U", "role": "SHAPER", "outcome_id": "outcome 1", "req_id": "req 5", "score": 10.0, "kind": "creation"},
                {"pair_added": 3, "action_id": "A(3,1)", "speaker": "A", "role": "EXECUTOR", "outcome_id": "outcome 1", "req_id": "req 6", "score": 20.0, "kind": "creation"}
            ]
            with open(chat_dir / "ledger.jsonl", "w") as f:
                for line in ledger_lines:
                    f.write(json.dumps(line) + "\n")
        else:
            # Default empty creation
            write_json_artifact(chat_dir / "dialogue.json", [], "dialogue")
            write_json_artifact(chat_dir / "snapshots.json", [], "snapshots")
            write_json_artifact(chat_dir / "panel_bundle.json", {"pairs": []}, "panel_bundle")
            state = State()
            state.save(chat_dir)
            (chat_dir / "ledger.jsonl").touch(exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating chat folder/artifacts: {e}")
        # Cleanup folder on failure
        try:
            shutil.rmtree(chat_dir)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")
    
    return {
        "id": chat_id,
        "title": get_chat_title_from_state(chat_dir)
    }

@app.get("/chats/{chat_id}/bundle")
def get_chat_bundle(chat_id: str):
    chat_dir = CHATS_DIR / chat_id
    if not chat_dir.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
        
    dialogue_path = chat_dir / "dialogue.json"
    bundle_path = chat_dir / "panel_bundle.json"
    
    if not dialogue_path.exists() or not bundle_path.exists():
        raise HTTPException(status_code=404, detail="Chat artifacts not found")
        
    try:
        with open(dialogue_path) as f:
            dialogue = json.load(f)
        with open(bundle_path) as f:
            panel_bundle = json.load(f)
    except Exception as e:
        logger.error(f"Error loading bundle/dialogue for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error loading chat data")
        
    return {
        "dialogue": dialogue,
        "panel_bundle": panel_bundle
    }

@app.patch("/chats/{chat_id}/title")
def update_chat_title(chat_id: str, payload: TitleUpdate):
    chat_dir = CHATS_DIR / chat_id
    if not chat_dir.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
        
    new_title = payload.title
    
    try:
        # Load state.json
        state = State.load(chat_dir)
        
        # Find root outcome (parent is None/null)
        root_outcome = None
        for outcome in state.outcomes:
            if outcome.get("parent") is None:
                root_outcome = outcome
                break
        
        if root_outcome:
            root_outcome["text"] = new_title
        else:
            # Create a new root outcome if it was empty
            root_outcome = {
                "id": "outcome 1",
                "text": new_title,
                "turn_id": "",
                "parent": None,
                "children": [],
                "related": []
            }
            state.outcomes.append(root_outcome)
            
        state.save(chat_dir)
        
        # Re-compute Stage 4
        ledger_path = chat_dir / "ledger.jsonl"
        rows = []
        if ledger_path.exists():
            try:
                rows = read_ledger(ledger_path)
            except Exception as e:
                logger.error(f"Error reading ledger rows for title update: {e}")
                
        snapshots, panel_bundle = compute_stage4(state, rows)
        write_stage4_artifacts(chat_dir, snapshots, panel_bundle)
        
    except Exception as e:
        logger.error(f"Error updating title for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update title: {str(e)}")
        
    return {
        "id": chat_id,
        "title": new_title
    }

class MessageRequest(BaseModel):
    text: str
    attachments: list[str] = []

@app.post("/chats/{chat_id}/messages")
async def post_message(chat_id: str, request: MessageRequest):
    global async_client
    chat_dir = CHATS_DIR / chat_id
    if not chat_dir.exists():
        raise HTTPException(status_code=404, detail="Chat not found")

    dialogue_path = chat_dir / "dialogue.json"
    if not dialogue_path.exists():
        raise HTTPException(status_code=404, detail="Dialogue file not found")

    # Load existing dialogue
    try:
        with open(dialogue_path) as f:
            dialogue = json.load(f)
    except Exception as e:
        logger.error(f"Error reading dialogue.json: {e}")
        raise HTTPException(status_code=500, detail="Failed to read dialogue history")

    # Calculate new pair number
    max_pair = 0
    last_speaker = None
    for turn in dialogue:
        max_pair = max(max_pair, turn["pair"])
        last_speaker = turn["speaker"]

    if last_speaker == "ai":
        pair_number = max_pair + 1
    elif last_speaker == "user":
        pair_number = max_pair
    else:
        pair_number = 1

    # Create user turn
    user_turn = {
        "pair": pair_number,
        "speaker": "user",
        "text": request.text,
        "attachments": request.attachments,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    dialogue.append(user_turn)
    
    # Save dialogue with user turn (validated)
    try:
        write_json_artifact(dialogue_path, dialogue, "dialogue")
    except Exception as e:
        logger.error(f"Failed to save user turn: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save user turn: {str(e)}")

    if not async_client:
        if config.llm_api_key:
            async_client = AsyncOpenAI(api_key=config.llm_api_key, base_url=config.llm_base_url)
        else:
            raise HTTPException(status_code=500, detail="LLM_API_KEY is not set (check .env at repo root)")

    async def sse_generator():
        # Map dialogue turns to OpenAI message roles
        messages = []
        for turn in dialogue:
            role = "user" if turn["speaker"] == "user" else "assistant"
            messages.append({"role": role, "content": turn["text"]})

        ai_response_text = ""
        try:
            response_stream = await async_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.7,
                stream=True
            )
            async for chunk in response_stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    ai_response_text += content
                    yield f"data: {json.dumps({'token': content})}\n\n"
        except Exception as e:
            logger.error(f"Error during stream generation: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return
        
        # Stream completed successfully. Now save the AI turn.
        ai_turn = {
            "pair": pair_number,
            "speaker": "ai",
            "text": ai_response_text,
            "attachments": [],
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # Load dialogue again to prevent concurrency overwrites, append, and save
        try:
            with open(dialogue_path) as f:
                current_dialogue = json.load(f)
            current_dialogue.append(ai_turn)
            write_json_artifact(dialogue_path, current_dialogue, "dialogue")
        except Exception as e:
            logger.error(f"Error saving AI turn: {e}")
            
        # Trigger pipeline job in the background
        asyncio.create_task(run_pipeline_job(chat_id, pair_number))
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

async def run_pipeline_job(chat_id: str, pair: int):
    # Get/Create lock for chat_id
    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()
    lock = chat_locks[chat_id]

    async with lock:
        chat_dir = CHATS_DIR / chat_id
        write_run_status(chat_dir, "running", pair, None)
        send_pipeline_status(chat_id, "running", pair)
        
        try:
            from engine.runner import run_pipeline
            
            # Load dialogue
            dialogue_path = chat_dir / "dialogue.json"
            with open(dialogue_path) as f:
                dialogue = json.load(f)
                
            # Run the pipeline synchronously in a thread pool to not block event loop
            await asyncio.to_thread(
                run_pipeline,
                config=config,
                dialogue=dialogue,
                out_dir=chat_dir,
                limit_pairs=pair,
                resume=True
            )
            
            write_run_status(chat_dir, "done", pair, None)
            send_pipeline_status(chat_id, "done", pair)
            send_pair_ready(chat_id, pair)
            
        except Exception as e:
            logger.error(f"Pipeline failed for chat {chat_id} pair {pair}: {e}")
            write_run_status(chat_dir, "failed", pair, str(e))
            send_pipeline_status(chat_id, "failed", pair)

@app.get("/chats/{chat_id}/events")
async def get_events(chat_id: str):
    chat_dir = CHATS_DIR / chat_id
    if not chat_dir.exists():
        raise HTTPException(status_code=404, detail="Chat not found")

    queue = asyncio.Queue()
    chat_event_listeners.setdefault(chat_id, set()).add(queue)

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            if chat_id in chat_event_listeners:
                chat_event_listeners[chat_id].discard(queue)
                if not chat_event_listeners[chat_id]:
                    del chat_event_listeners[chat_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/chats/{chat_id}/pairs/{pair}/rerun")
async def rerun_pair(chat_id: str, pair: int):
    chat_dir = CHATS_DIR / chat_id
    if not chat_dir.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
        
    # Queue task in background
    asyncio.create_task(run_pipeline_job(chat_id, pair))
    return {"status": "queued", "pair": pair}
