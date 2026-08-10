import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_fd, _db = tempfile.mkstemp(
    prefix="learning-agent-smoke-",
    suffix=".db",
)
os.close(_fd)
os.environ["LEARNING_DB_PATH"] = _db
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.app import app  # noqa: E402

client = TestClient(app)
start = client.post("/api/v1/session/start").json()
session = start["session"]
token = start["session_token"]
headers = {"X-Session-Token": token}


def command_id(suffix: str) -> str:
    return f"{session['session_id']}:{suffix}-{uuid.uuid4()}"


steps = [
    ("ANSWER_SUBMITTED", {"answer": "trapped"}),
    ("ANSWER_SUBMITTED", {"answer": "ruins"}),
    (
        "VERIFY_ANSWER",
        {"variant_id": "pointer-v1", "answer": "house"},
    ),
    (
        "VERIFY_ANSWER",
        {"variant_id": "pointer-v2", "answer": "city"},
    ),
    (
        "VERIFY_ANSWER",
        {"variant_id": "pointer-v3", "answer": "room"},
    ),
    ("WORD_ANSWER", {"answer": "rupt"}),
]

for index, (event, payload) in enumerate(steps, start=1):
    response = client.post(
        "/api/v1/learning/step",
        headers=headers,
        json={
            "session_id": session["session_id"],
            "event": event,
            "payload": payload,
            "event_id": command_id(str(index)),
            "expected_version": session["version"],
        },
    )
    response.raise_for_status()
    session = response.json()["session"]
    print(event, "->", session["state"], "v", session["version"])

snapshot = client.get(
    f"/api/v1/session/{session['session_id']}",
    headers=headers,
).json()
assert snapshot["session"]["state"] == "DONE"
assert snapshot["session"]["node_status"] == "VERIFIED"
assert snapshot["session"]["word_status"] == "VERIFIED"

event_types = [event["event_type"] for event in snapshot["events"]]
for required in [
    "error_diagnosed",
    "patch_completed",
    "word_verified",
    "demo_completed",
]:
    assert required in event_types, required

integrity = client.get(
    f"/api/v1/internal/session/{session['session_id']}/integrity",
    headers=headers,
)
integrity.raise_for_status()
assert integrity.json()["consistent"] is True
assert integrity.json()["receipt_count"] == len(steps)

print(
    "CLOSED_LOOP",
    session["session_id"],
    "events=",
    len(snapshot["events"]),
    "receipts=",
    integrity.json()["receipt_count"],
)
