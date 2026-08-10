from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import LearningController, Store

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
    return {"session": state, "events": store.events(session_id)}


@app.post("/api/v1/learning/step")
def learning_step(request: StepRequest) -> dict[str, Any]:
    try:
        return controller.step(request.session_id, request.event, request.payload, request.event_id).as_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "apps" / "web" / "dist"
if WEB_DIST.exists():
    assets = WEB_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = WEB_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
