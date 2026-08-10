from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .core import (
    CommandConflict,
    InvalidTransition,
    LearningController,
    SessionNotFound,
    StateConflict,
    Store,
)

APP_ENV = os.getenv("APP_ENV", "demo")
app = FastAPI(
    title="Learning-Agent Demo",
    version="0.2.0-demo",
    docs_url=None if APP_ENV == "production" else "/docs",
    redoc_url=None if APP_ENV == "production" else "/redoc",
)
store = Store()
controller = LearningController()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
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
    expected_version: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_event_namespace(self):
        prefix = f"{self.session_id}:"
        if not self.event_id.startswith(prefix):
            raise ValueError("event_id_must_be_namespaced_by_session")
        return self


@app.get("/api/v1/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/ready")
def ready() -> dict[str, Any]:
    try:
        checks = store.readiness()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="not_ready") from exc
    return {"status": "ok", **checks}


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    """Compatibility endpoint; /live and /ready are canonical probes."""
    return {
        "status": "ok",
        "mode": os.getenv("LEARNING_MODE", "deterministic"),
        "mutation_model": "sqlite-atomic-command",
        "app_env": APP_ENV,
    }


@app.post("/api/v1/session/start")
def start_session() -> dict[str, Any]:
    return store.create_session(controller).as_dict()


@app.get("/api/v1/session/{session_id}")
def get_session(session_id: UUID) -> dict[str, Any]:
    sid = str(session_id)
    state = store.get_session(sid)
    if not state:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {
        "session": state,
        "current_task": controller.current_task(state),
        "events": store.events(sid),
    }


@app.get("/api/v1/internal/session/{session_id}/integrity")
def session_integrity(session_id: UUID) -> dict[str, Any]:
    if APP_ENV == "production":
        raise HTTPException(status_code=404, detail="api_route_not_found")
    try:
        return store.integrity(controller, str(session_id))
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc


@app.post("/api/v1/learning/step")
def learning_step(request: StepRequest) -> dict[str, Any]:
    sid = str(request.session_id)
    payload = request.payload.model_dump(exclude_none=True)
    try:
        return store.execute_command(
            controller=controller,
            session_id=sid,
            command_id=request.event_id,
            event=request.event,
            payload=payload,
            expected_version=request.expected_version,
        ).as_dict()
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail=exc.code) from exc
    except (CommandConflict, StateConflict, InvalidTransition) as exc:
        raise HTTPException(status_code=409, detail=exc.code) from exc


ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = (ROOT / "apps" / "web").resolve()
if WEB_DIST.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
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
