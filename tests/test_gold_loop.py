import os
import tempfile
import uuid

_fd, _db = tempfile.mkstemp(prefix="learning-agent-test-", suffix=".db")
os.close(_fd)
os.environ["LEARNING_DB_PATH"] = _db
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from apps.api.app import app  # noqa: E402

client = TestClient(app)


def request_id(session_id: str, suffix: str | None = None) -> str:
    return f"{session_id}:{suffix or uuid.uuid4()}"


def start() -> dict:
    response = client.post("/api/v1/session/start")
    assert response.status_code == 200
    return response.json()


def step(
    session: dict,
    event: str,
    payload: dict,
    *,
    event_id: str | None = None,
    expected_version: int | None = None,
):
    return client.post(
        "/api/v1/learning/step",
        json={
            "session_id": session["session_id"],
            "event": event,
            "payload": payload,
            "event_id": event_id or request_id(session["session_id"]),
            "expected_version": (
                session["version"]
                if expected_version is None
                else expected_version
            ),
        },
    )


def test_complete_demo_closed_loop_and_replay_integrity():
    session = start()["session"]

    wrong = step(session, "ANSWER_SUBMITTED", {"answer": "trapped"})
    assert wrong.status_code == 200
    session = wrong.json()["session"]
    assert session["version"] == 1
    assert wrong.json()["error_type"] == "POINTER_ERROR"

    fixed = step(session, "ANSWER_SUBMITTED", {"answer": "ruins"})
    assert fixed.status_code == 200
    session = fixed.json()["session"]
    assert session["state"] == "VERIFY"

    for variant_id, answer in [
        ("pointer-v1", "house"),
        ("pointer-v2", "city"),
        ("pointer-v3", "room"),
    ]:
        response = step(
            session,
            "VERIFY_ANSWER",
            {"variant_id": variant_id, "answer": answer},
        )
        assert response.status_code == 200
        session = response.json()["session"]

    assert session["node_status"] == "VERIFIED"
    assert session["state"] == "WORD_TASK"

    word = step(session, "WORD_ANSWER", {"answer": "rupt"})
    assert word.status_code == 200
    session = word.json()["session"]
    assert session["state"] == "DONE"
    assert session["word_status"] == "VERIFIED"

    snapshot = client.get(
        f"/api/v1/session/{session['session_id']}"
    ).json()
    event_types = [event["event_type"] for event in snapshot["events"]]
    assert "error_diagnosed" in event_types
    assert "patch_completed" in event_types
    assert "demo_completed" in event_types

    integrity = client.get(
        f"/api/v1/internal/session/{session['session_id']}/integrity"
    )
    assert integrity.status_code == 200
    assert integrity.json()["consistent"] is True
    assert integrity.json()["stored_version"] == 6
    assert integrity.json()["receipt_count"] == 6


def test_receipt_replays_exact_response_and_rejects_command_reuse():
    session = start()["session"]
    command_id = request_id(session["session_id"], "receipt")

    first = step(
        session,
        "ANSWER_SUBMITTED",
        {"answer": "trapped"},
        event_id=command_id,
    )
    assert first.status_code == 200

    replay = step(
        session,
        "ANSWER_SUBMITTED",
        {"answer": "trapped"},
        event_id=command_id,
    )
    assert replay.status_code == 200
    assert replay.json() == first.json()

    conflict = step(
        session,
        "ANSWER_SUBMITTED",
        {"answer": "ruins"},
        event_id=command_id,
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "command_id_conflict"


def test_stale_version_rejected_without_event_or_state_change():
    session = start()["session"]
    first = step(session, "ANSWER_SUBMITTED", {"answer": "trapped"})
    assert first.status_code == 200

    sid = session["session_id"]
    before = client.get(f"/api/v1/session/{sid}").json()
    stale = step(
        session,
        "ANSWER_SUBMITTED",
        {"answer": "ruins"},
        event_id=request_id(sid, "stale"),
        expected_version=0,
    )
    assert stale.status_code == 409
    assert stale.json()["detail"] == "state_conflict"
    after = client.get(f"/api/v1/session/{sid}").json()
    assert after == before


def test_invalid_transition_and_input_contracts():
    session = start()["session"]
    sid = session["session_id"]
    before = client.get(f"/api/v1/session/{sid}").json()

    invalid = step(
        session,
        "VERIFY_ANSWER",
        {"variant_id": "pointer-v1", "answer": "house"},
    )
    assert invalid.status_code == 409
    assert invalid.json()["detail"] == "invalid_transition"
    assert client.get(f"/api/v1/session/{sid}").json() == before

    missing_version = client.post(
        "/api/v1/learning/step",
        json={
            "session_id": sid,
            "event": "ANSWER_SUBMITTED",
            "event_id": request_id(sid),
            "payload": {"answer": "trapped"},
        },
    )
    assert missing_version.status_code == 422

    wrong_namespace = client.post(
        "/api/v1/learning/step",
        json={
            "session_id": sid,
            "event": "ANSWER_SUBMITTED",
            "event_id": "00000000-0000-0000-0000-000000000000:bad",
            "expected_version": 0,
            "payload": {"answer": "trapped"},
        },
    )
    assert wrong_namespace.status_code == 422

    oversized = client.post(
        "/api/v1/learning/step",
        json={
            "session_id": sid,
            "event": "ANSWER_SUBMITTED",
            "event_id": request_id(sid),
            "expected_version": 0,
            "payload": {"answer": "x" * 65},
        },
    )
    assert oversized.status_code == 422


def test_spa_security_and_health_contracts():
    missing_api = client.get("/api/v1/does-not-exist")
    assert missing_api.status_code == 404
    assert "application/json" in missing_api.headers.get("content-type", "")

    traversal = client.get("/%2e%2e/README.md")
    assert traversal.status_code == 404

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"

    live = client.get("/api/v1/live")
    ready = client.get("/api/v1/ready")
    assert live.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["database"] == "ok"
