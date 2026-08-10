from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .core import GOLD, WORD, LearningController, Store

app = FastAPI(title="Learning-Agent Demo", version="0.1.1-demo")
store = Store()
controller = LearningController(store)

# P0 deploys one Uvicorn process. Serialize mutations so concurrent requests
# cannot advance the same SQLite-backed state from the same snapshot.
_mutation_lock = threading.RLock()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


class StepPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=64)
    variant_id: str | None = Field(default=None, min_length=1, max_length=64)


class StepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    event: Literal["ANSWER_SUBMITTED", "VERIFY_ANSWER", "WORD_ANSWER"]
    payload: StepPayload
    event_id: str = Field(min_length=16, max_length=128)

    @model_validator(mode="after")
    def validate_event_namespace(self):
        prefix = f"{self.session_id}:"
        if not self.event_id.startswith(prefix):
            raise ValueError("event_id_must_be_namespaced_by_session")
        return self


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
    return {
        "status": "ok",
        "mode": os.getenv("LEARNING_MODE", "deterministic"),
        "mutation_model": "single-process-serialized",
    }


@app.post("/api/v1/session/start")
def start_session() -> dict[str, Any]:
    with _mutation_lock:
        return controller.start().as_dict()


@app.get("/api/v1/session/{session_id}")
def get_session(session_id: UUID) -> dict[str, Any]:
    sid = str(session_id)
    state = store.get_session(sid)
    if not state:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session": state, "current_task": current_task(state), "events": store.events(sid)}


@app.post("/api/v1/learning/step")
def learning_step(request: StepRequest) -> dict[str, Any]:
    sid = str(request.session_id)
    payload = request.payload.model_dump(exclude_none=True)
    with _mutation_lock:
        state = store.get_session(sid)
        if not state:
            raise HTTPException(status_code=404, detail="session_not_found")

        # Detect the crash window where the request event was persisted but the
        # session snapshot did not record it. Fail closed instead of replaying
        # a mutation against stale state.
        event_already_logged = any(
            event["event_id"] == request.event_id for event in store.events(sid)
        )
        if event_already_logged and request.event_id not in state.get("processed_event_ids", []):
            raise HTTPException(status_code=409, detail="incomplete_previous_request")

        try:
            return controller.step(
                sid,
                request.event,
                payload,
                request.event_id,
            ).as_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc


ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = (ROOT / "apps" / "web").resolve()
if WEB_DIST.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        # Never let the SPA fallback hide a missing API route.
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="api_route_not_found")

        candidate = (WEB_DIST / full_path).resolve()
        try:
            candidate.relative_to(WEB_DIST)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="file_not_found") from exc

        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
