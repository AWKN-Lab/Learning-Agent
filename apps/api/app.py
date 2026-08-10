from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import GOLD, WORD, LearningController, Store

app = FastAPI(title="Learning-Agent Demo", version="0.1.0-demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = Store()
controller = LearningController(store)


class StepRequest(BaseModel):
    session_id: str
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)
    event_id: str | None = None


def current_task(state: dict[str, Any]) -> dict[str, Any] | None:
    if state["state"] in {"TASK", "RETRY"}:
        return GOLD["task"]
    if state["state"] == "VERIFY":
        index = state["variant_index"]
        return GOLD["variants"][index] if index < len(GOLD["variants"]) else None
    if state["state"] == "WORD_TASK":
        return WORD["task"]
    return None


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": os.getenv("LEARNING_MODE", "deterministic")}


@app.post("/api/v1/session/start")
def start_session() -> dict[str, Any]:
    return controller.start().as_dict()


@app.get("/api/v1/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    state = store.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session": state, "current_task": current_task(state), "events": store.events(session_id)}


@app.post("/api/v1/learning/step")
def learning_step(request: StepRequest) -> dict[str, Any]:
    try:
        return controller.step(request.session_id, request.event, request.payload, request.event_id).as_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
if WEB_ROOT.exists():
    app.mount("/", StaticFiles(directory=WEB_ROOT, html=True), name="web")
