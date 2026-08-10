from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .core import (
    CommandConflict,
    InvalidTransition,
    LearningController,
    RateLimitExceeded,
    SessionExpired,
    SessionNotFound,
    SessionUnauthorized,
    StateConflict,
    Store,
)
from .security import hash_session_token, new_session_token
from .settings import AppSettings

settings = AppSettings.from_env()
logger = logging.getLogger("learning_agent")

app = FastAPI(
    title="Learning-Agent Demo",
    version="0.3.0-demo",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(settings.trusted_hosts),
)
store = Store()
controller = LearningController()


@app.middleware("http")
async def body_size_limit(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"}:
        raw_length = request.headers.get("content-length")
        if raw_length:
            try:
                content_length = int(raw_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "invalid_content_length"},
                )
            if content_length > settings.max_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "request_too_large"},
                )
    return await call_next(request)


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


def require_token(token: str | None) -> str:
    if not token or len(token) > 256:
        raise HTTPException(status_code=401, detail="session_unauthorized")
    return hash_session_token(token)


def map_session_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SessionNotFound):
        return HTTPException(status_code=404, detail=exc.code)
    if isinstance(exc, SessionExpired):
        return HTTPException(status_code=410, detail=exc.code)
    if isinstance(exc, SessionUnauthorized):
        return HTTPException(status_code=401, detail=exc.code)
    raise exc


def client_identity(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


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
    return {
        "status": "ok",
        "mode": "deterministic",
        "mutation_model": "sqlite-atomic-command",
        "app_env": settings.app_env,
    }


@app.post("/api/v1/session/start")
def start_session(request: Request) -> dict[str, Any]:
    try:
        store.consume_rate_limit(
            f"start:{client_identity(request)}",
            limit=settings.start_rate_limit,
            window_seconds=settings.rate_window_seconds,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.code,
        ) from exc

    token = new_session_token()
    result = store.create_session(
        controller,
        token_hash=hash_session_token(token),
        ttl_seconds=settings.session_ttl_seconds,
    ).as_dict()
    result["session_token"] = token
    return result


@app.get("/api/v1/session/{session_id}")
def get_session(
    session_id: UUID,
    x_session_token: str | None = Header(
        default=None,
        alias="X-Session-Token",
    ),
) -> dict[str, Any]:
    sid = str(session_id)
    token_hash = require_token(x_session_token)
    try:
        state = store.get_authorized_session(sid, token_hash)
    except (SessionNotFound, SessionExpired, SessionUnauthorized) as exc:
        raise map_session_error(exc) from exc

    return {
        "session": state,
        "current_task": controller.current_task(state),
        "events": store.events(sid),
    }


@app.get("/api/v1/internal/session/{session_id}/integrity")
def session_integrity(
    session_id: UUID,
    x_session_token: str | None = Header(
        default=None,
        alias="X-Session-Token",
    ),
) -> dict[str, Any]:
    if settings.app_env == "production":
        raise HTTPException(status_code=404, detail="api_route_not_found")

    sid = str(session_id)
    token_hash = require_token(x_session_token)
    try:
        store.get_authorized_session(sid, token_hash)
        return store.integrity(controller, sid)
    except (SessionNotFound, SessionExpired, SessionUnauthorized) as exc:
        raise map_session_error(exc) from exc


@app.post("/api/v1/learning/step")
def learning_step(
    command: StepRequest,
    x_session_token: str | None = Header(
        default=None,
        alias="X-Session-Token",
    ),
) -> dict[str, Any]:
    started = time.perf_counter()
    sid = str(command.session_id)
    token_hash = require_token(x_session_token)

    try:
        store.consume_rate_limit(
            f"step:{token_hash}",
            limit=settings.step_rate_limit,
            window_seconds=settings.rate_window_seconds,
        )
        result = store.execute_command(
            controller=controller,
            session_id=sid,
            command_id=command.event_id,
            event=command.event,
            payload=command.payload.model_dump(exclude_none=True),
            expected_version=command.expected_version,
            token_hash=token_hash,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=exc.code) from exc
    except (SessionNotFound, SessionExpired, SessionUnauthorized) as exc:
        raise map_session_error(exc) from exc
    except (CommandConflict, StateConflict, InvalidTransition) as exc:
        raise HTTPException(status_code=409, detail=exc.code) from exc

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        json.dumps(
            {
                "event": "learning_command",
                "command_id": command.event_id,
                "session_id": sid,
                "learning_event": command.event,
                "state_after": result.session["state"],
                "version_after": result.session["version"],
                "duration_ms": duration_ms,
                "result": "ok",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return result.as_dict()


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
