import json
import logging
from pathlib import Path
import uuid
import os
import datetime
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

@app.post("/chats")
def create_chat():
    chat_id = str(uuid.uuid4())
    chat_dir = CHATS_DIR / chat_id
    chat_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Empty artifacts matching schemas
        # 1. dialogue.json -> []
        write_json_artifact(chat_dir / "dialogue.json", [], "dialogue")
        # 2. snapshots.json -> []
        write_json_artifact(chat_dir / "snapshots.json", [], "snapshots")
        # 3. panel_bundle.json -> {"pairs": []}
        write_json_artifact(chat_dir / "panel_bundle.json", {"pairs": []}, "panel_bundle")
        
        # 4. state.json -> empty State
        state = State()
        state.save(chat_dir)
        
        # 5. ledger.jsonl -> touch it empty
        ledger_path = chat_dir / "ledger.jsonl"
        ledger_path.touch(exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating chat folder/artifacts: {e}")
        # Cleanup folder on failure
        try:
            import shutil
            shutil.rmtree(chat_dir)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")
    
    return {
        "id": chat_id,
        "title": "New Chat"
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
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
