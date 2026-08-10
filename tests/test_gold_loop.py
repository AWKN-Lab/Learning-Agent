import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor

_fd, _db = tempfile.mkstemp(prefix="learning-agent-test-", suffix=".db")
os.close(_fd)
os.environ["LEARNING_DB_PATH"] = _db

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.app import StepRequest, app, learning_step  # noqa: E402

client = TestClient(app)


def request_id(session_id: str, suffix: str | None = None) -> str:
    return f"{session_id}:{suffix or uuid.uuid4()}"


def step(session_id, event, payload, event_id=None, include_event_id=True):
    body = {"session_id": session_id, "event": event, "payload": payload}
    if include_event_id:
        body["event_id"] = event_id or request_id(session_id)
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

    assert response.json()["session"]["node_status"] == "VERIFIED"
    assert response.json()["session"]["state"] == "WORD_TASK"

    word = step(sid, "WORD_ANSWER", {"answer": "rupt"})
    assert word.status_code == 200
    assert word.json()["session"]["state"] == "DONE"
    assert word.json()["session"]["word_status"] == "VERIFIED"

    snapshot = client.get(f"/api/v1/session/{sid}")
    events = [e["event_type"] for e in snapshot.json()["events"]]
    assert "error_diagnosed" in events
    assert "patch_completed" in events
    assert "demo_completed" in events


def test_invalid_transition_is_rejected_without_writing_event():
    sid = client.post("/api/v1/session/start").json()["session"]["session_id"]
    before = client.get(f"/api/v1/session/{sid}").json()["events"]
    response = step(sid, "VERIFY_ANSWER", {"variant_id": "pointer-v1", "answer": "house"}, event_id=request_id(sid, "bad-transition"))
    assert response.status_code == 409
    after = client.get(f"/api/v1/session/{sid}").json()["events"]
    assert len(after) == len(before)


def test_duplicate_request_is_controller_idempotent():
    sid = client.post("/api/v1/session/start").json()["session"]["session_id"]
    event_id = request_id(sid, "fixed-event-id")
    first = step(sid, "ANSWER_SUBMITTED", {"answer": "trapped"}, event_id=event_id)
    assert first.status_code == 200
    first_state = first.json()["session"]
    second = step(sid, "ANSWER_SUBMITTED", {"answer": "trapped"}, event_id=event_id)
    assert second.status_code == 200
    second_state = second.json()["session"]
    assert second.json()["ui_action"] == "NOOP"
    assert second_state["attempt"] == first_state["attempt"]
    assert second_state["hint_level"] == first_state["hint_level"]
    snapshot = client.get(f"/api/v1/session/{sid}").json()
    matching = [e for e in snapshot["events"] if e["event_id"] == event_id]
    assert len(matching) == 1


def test_concurrent_duplicate_request_advances_state_once():
    sid = client.post("/api/v1/session/start").json()["session"]["session_id"]
    event_id = request_id(sid, "concurrent")
    request = StepRequest(
        session_id=sid,
        event="ANSWER_SUBMITTED",
        event_id=event_id,
        payload={"answer": "trapped"},
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: learning_step(request), range(2)))

    actions = sorted(result["ui_action"] for result in results)
    assert actions == ["NOOP", "RETRY_TASK"]
    snapshot = client.get(f"/api/v1/session/{sid}").json()
    assert snapshot["session"]["attempt"] == 1
    assert snapshot["session"]["hint_level"] == 1
    matching = [e for e in snapshot["events"] if e["event_id"] == event_id]
    assert len(matching) == 1


def test_mutation_requires_namespaced_event_id_and_bounded_payload():
    sid = client.post("/api/v1/session/start").json()["session"]["session_id"]

    missing = step(sid, "ANSWER_SUBMITTED", {"answer": "trapped"}, include_event_id=False)
    assert missing.status_code == 422

    wrong_namespace = step(sid, "ANSWER_SUBMITTED", {"answer": "trapped"}, event_id="00000000-0000-0000-0000-000000000000:bad")
    assert wrong_namespace.status_code == 422

    oversized = step(sid, "ANSWER_SUBMITTED", {"answer": "x" * 65})
    assert oversized.status_code == 422


def test_spa_does_not_swallow_missing_api_route_or_escape_web_root():
    missing_api = client.get("/api/v1/does-not-exist")
    assert missing_api.status_code == 404
    assert "application/json" in missing_api.headers.get("content-type", "")

    traversal = client.get("/%2e%2e/README.md")
    assert traversal.status_code == 404
    assert "Learning-Agent" not in traversal.text


def test_security_headers_are_present():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]

    api_response = client.get("/api/v1/health")
    assert api_response.headers["cache-control"] == "no-store"
