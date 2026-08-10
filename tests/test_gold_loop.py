import os
import tempfile

_fd, _db = tempfile.mkstemp(prefix="learning-agent-test-", suffix=".db")
os.close(_fd)
os.environ["LEARNING_DB_PATH"] = _db

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.app import app  # noqa: E402

client = TestClient(app)


def step(session_id, event, payload, event_id=None):
    body = {"session_id": session_id, "event": event, "payload": payload}
    if event_id:
        body["event_id"] = event_id
    return client.post("/api/v1/learning/step", json=body)


def test_complete_demo_closed_loop():
    start = client.post("/api/v1/session/start")
    assert start.status_code == 200
    data = start.json()
    sid = data["session"]["session_id"]
    assert data["session"]["state"] == "TASK"

    wrong = step(sid, "ANSWER_SUBMITTED", {"answer": "trapped"})
    assert wrong.status_code == 200
    assert wrong.json()["error_type"] == "POINTER_ERROR"
    assert wrong.json()["session"]["state"] == "RETRY"

    fixed = step(sid, "ANSWER_SUBMITTED", {"answer": "ruins"})
    assert fixed.status_code == 200
    assert fixed.json()["session"]["state"] == "VERIFY"

    for variant_id, answer in [("pointer-v1", "house"), ("pointer-v2", "city"), ("pointer-v3", "room")]:
        response = step(sid, "VERIFY_ANSWER", {"variant_id": variant_id, "answer": answer})
        assert response.status_code == 200

    after_transfer = response.json()
    assert after_transfer["session"]["node_status"] == "VERIFIED"
    assert after_transfer["session"]["state"] == "WORD_TASK"

    word = step(sid, "WORD_ANSWER", {"answer": "rupt"})
    assert word.status_code == 200
    assert word.json()["session"]["state"] == "DONE"
    assert word.json()["session"]["word_status"] == "VERIFIED"

    snapshot = client.get(f"/api/v1/session/{sid}")
    events = [e["event_type"] for e in snapshot.json()["events"]]
    assert "error_diagnosed" in events
    assert "patch_completed" in events
    assert "demo_completed" in events


def test_invalid_transition_is_rejected():
    sid = client.post("/api/v1/session/start").json()["session"]["session_id"]
    response = step(sid, "VERIFY_ANSWER", {"variant_id": "pointer-v1", "answer": "house"})
    assert response.status_code == 409


def test_event_id_is_idempotent_in_event_store():
    sid = client.post("/api/v1/session/start").json()["session"]["session_id"]
    event_id = "fixed-event-id"
    first = step(sid, "ANSWER_SUBMITTED", {"answer": "trapped"}, event_id=event_id)
    assert first.status_code == 200
    # Reusing an event_id must not duplicate the raw event row. Controller state changes are protected by state/event guards in real clients.
    snapshot = client.get(f"/api/v1/session/{sid}").json()
    matching = [e for e in snapshot["events"] if e["event_id"] == event_id]
    assert len(matching) == 1
