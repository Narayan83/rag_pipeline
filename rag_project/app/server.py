"""Chat API and static frontend."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

ROOT = Path(__file__).resolve().parents[1]
YUKTA = ROOT / "yukta"
if str(YUKTA) not in sys.path:
    sys.path.insert(0, str(YUKTA))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agents import ask
from app.config import load_config
from app.db import ensure_database
from app.ingest import ingest_all
from app.retrieval import list_documents

app = FastAPI(title="Audit document assistant")
FRONTEND = ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def _init_tracing() -> None:
    cfg = load_config().get("tracing") or {}
    if not cfg.get("enabled", True):
        return
    from yukta.instrumentation import init_tracing

    project = cfg.get("project_name", "narayan_yukta")
    url = cfg.get("opik_url", "http://192.168.200.29:28173")
    if init_tracing(backends=[f"opik={url}"], project_name=project):
        logger.info("Question traces go to Opik project %s at %s", project, url)
    else:
        logger.warning("Opik tracing did not start; questions will not appear in %s", project)


@app.on_event("startup")
def startup() -> None:
    ensure_database()
    _init_tracing()


@app.get("/")
def index():
    return FileResponse(
        FRONTEND / "index.html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/health")
def health():
    cfg = load_config()
    return {
        "database": cfg["database"]["name"],
        "top_k": cfg["retrieval"]["top_k"],
        "max_context_length": cfg["retrieval"]["max_context_length"],
    }


@app.get("/api/documents")
def documents():
    return {"documents": list_documents()}


@app.post("/api/ingest")
def ingest():
    try:
        return {"results": ingest_all()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _flush_traces() -> None:
    try:
        from yukta.instrumentation import flush_tracing

        flush_tracing()
    except Exception:
        pass


@app.post("/api/chat")
def chat(body: ChatRequest):
    try:
        return ask(body.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        _flush_traces()
