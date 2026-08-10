import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from apps.api.app import settings, store
from apps.api.core import LearningController, RateLimitExceeded, Store
from apps.api.security import hash_session_token
from apps.api.settings import AppSettings


def fresh_db(prefix: str) -> str:
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".db")
    os.close(fd)
    return path


def test_session_token_required_and_not_stored_in_plaintext(client):
    start = client.post("/api/v1/session/start")
    assert start.status_code == 200
    data = start.json()
    sid = data["session"]["session_id"]
    token = data["session_token"]

    missing = client.get(f"/api/v1/session/{sid}")
    assert missing.status_code == 401

    wrong = client.get(
        f"/api/v1/session/{sid}",
        headers={"X-Session-Token": "wrong-token"},
    )
    assert wrong.status_code == 401

    ok = client.get(
        f"/api/v1/session/{sid}",
        headers={"X-Session-Token": token},
    )
    assert ok.status_code == 200

    with sqlite3.connect(store.db_path) as conn:
        stored_hash = conn.execute(
            "SELECT token_hash FROM sessions WHERE session_id=?",
            (sid,),
        ).fetchone()[0]
    assert stored_hash == hash_session_token(token)
    assert stored_hash != token


def test_expired_session_is_rejected(client):
    start = client.post("/api/v1/session/start").json()
    sid = start["session"]["session_id"]
    token = start["session_token"]
    past = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()

    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE sessions SET expires_at=? WHERE session_id=?",
            (past, sid),
        )

    response = client.get(
        f"/api/v1/session/{sid}",
        headers={"X-Session-Token": token},
    )
    assert response.status_code == 410
    assert response.json()["detail"] == "session_expired"


def test_sqlite_rate_limit_is_shared_and_windowed():
    path = fresh_db("learning-agent-rate-")
    first = Store(path)
    second = Store(path)

    assert first.consume_rate_limit(
        "same-client",
        limit=2,
        window_seconds=60,
        now_ts=120,
    ) == 1
    assert second.consume_rate_limit(
        "same-client",
        limit=2,
        window_seconds=60,
        now_ts=120,
    ) == 2
    with pytest.raises(RateLimitExceeded):
        first.consume_rate_limit(
            "same-client",
            limit=2,
            window_seconds=60,
            now_ts=120,
        )

    assert second.consume_rate_limit(
        "same-client",
        limit=2,
        window_seconds=60,
        now_ts=180,
    ) == 1


def test_cleanup_removes_expired_sessions_and_cascades():
    path = fresh_db("learning-agent-cleanup-")
    local_store = Store(path)
    controller = LearningController()
    expired = local_store.create_session(controller).session
    active = local_store.create_session(controller).session
    past = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE sessions SET expires_at=? WHERE session_id=?",
            (past, expired["session_id"]),
        )

    dry = local_store.cleanup_sessions(dry_run=True)
    assert dry["candidates"] == 1
    assert dry["deleted"] == 0
    assert local_store.get_session(expired["session_id"]) is not None

    actual = local_store.cleanup_sessions()
    assert actual["deleted"] == 1
    assert local_store.get_session(expired["session_id"]) is None
    assert local_store.events(expired["session_id"]) == []
    assert local_store.get_session(active["session_id"]) is not None


def test_cleanup_enforces_max_session_capacity():
    path = fresh_db("learning-agent-capacity-")
    local_store = Store(path)
    controller = LearningController()
    sessions = [
        local_store.create_session(controller).session
        for _ in range(3)
    ]

    result = local_store.cleanup_sessions(max_sessions=2)
    assert result["overflow"] == 1
    remaining = sum(
        local_store.get_session(item["session_id"]) is not None
        for item in sessions
    )
    assert remaining == 2


def test_large_request_rejected_before_json_parsing(client):
    response = client.post(
        "/api/v1/learning/step",
        content=b"x" * (settings.max_body_bytes + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_production_settings_require_explicit_hosts(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("TRUSTED_HOSTS", raising=False)
    with pytest.raises(RuntimeError, match="TRUSTED_HOSTS_required"):
        AppSettings.from_env()

    monkeypatch.setenv("TRUSTED_HOSTS", "*")
    with pytest.raises(RuntimeError, match="wildcard_TRUSTED_HOSTS"):
        AppSettings.from_env()

    monkeypatch.setenv("TRUSTED_HOSTS", "demo.example.com")
    loaded = AppSettings.from_env()
    assert loaded.trusted_hosts == ("demo.example.com",)
