"""FastAPI Web UI backend for Vaani AI."""

import json
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from vaani.config import get_settings
from vaani.agent import VaaniAgent

logger = logging.getLogger("vaani.web")

app = FastAPI(title="Vaani AI - Web Interface", version="1.0.0")

# Initialize central agent
settings = get_settings()
agent = VaaniAgent(settings=settings)

STATIC_DIR = Path(__file__).parent / "static"


class MentionRequest(BaseModel):
    text: str
    author: Optional[str] = "hackathon_judge"


@app.get("/api/stats")
async def get_system_stats():
    """Retrieve runtime stats, dataset size, and SQLite state."""
    total_live = agent.dataset_collector.count_samples()
    recent = agent.storage.get_recent_history(limit=8)

    large_ds_path = Path("data/train_large.jsonl")
    large_count = 0
    large_size_mb = 0.0
    if large_ds_path.exists():
        with open(large_ds_path, "r", encoding="utf-8") as f:
            large_count = sum(1 for _ in f)
        large_size_mb = round(large_ds_path.stat().st_size / (1024 * 1024), 2)

    return {
        "bot_handle": settings.bot_handle,
        "hf_mode": settings.hf_mode,
        "hf_model_id": settings.hf_model_id,
        "hf_lora_path": settings.hf_lora_path or "None (Base Model)",
        "lora_active": bool(settings.hf_lora_path and Path(settings.hf_lora_path).exists()),
        "base_dataset_count": large_count,
        "base_dataset_size_mb": large_size_mb,
        "live_dataset_count": total_live,
        "recent_history": recent,
    }


@app.get("/api/dataset")
async def get_dataset_stream(limit: int = 15):
    """Retrieve recent fine-tuning samples logged to dataset.jsonl."""
    ds_path = Path(settings.dataset_path)
    if not ds_path.exists():
        return {"samples": []}

    samples = []
    with open(ds_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    samples.append(json.loads(line))
                except Exception:
                    pass

    return {
        "total": len(samples),
        "samples": samples[-limit:][::-1]  # Return newest first
    }


@app.post("/api/mention")
async def handle_web_mention(req: MentionRequest):
    """Process a mention query through Vaani AI's local Hugging Face + LoRA pipeline."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    author = req.author.strip() if req.author else "hackathon_judge"
    author = author.lstrip("@")

    start_time = time.time()

    # 1. Run local LLM inference + tweet formatting + dataset logging
    full_response, chunks = agent.solve_mention_query(
        raw_text=req.text,
        author=author,
        source="web_simulator"
    )

    elapsed = round(time.time() - start_time, 2)

    # 2. Record to SQLite state
    simulated_tweet_id = f"sim_{int(time.time() * 1000)}"
    simulated_reply_id = f"reply_{int(time.time() * 1000)}"
    agent.storage.record_mention(
        tweet_id=simulated_tweet_id,
        author_id="999999",
        author_username=author,
        query_text=req.text,
        response_text=full_response,
        reply_tweet_id=simulated_reply_id,
        created_at=None
    )

    return {
        "tweet_id": simulated_tweet_id,
        "author": author,
        "query": req.text,
        "full_response": full_response,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "latency_sec": elapsed,
        "live_samples_total": agent.dataset_collector.count_samples()
    }


# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "Vaani AI Web UI - static files initializing..."})
