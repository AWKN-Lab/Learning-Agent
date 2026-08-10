import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_fd, _db = tempfile.mkstemp(prefix="learning-agent-smoke-", suffix=".db")
os.close(_fd)
os.environ["LEARNING_DB_PATH"] = _db

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.app import app  # noqa: E402

client = TestClient(app)
start = client.post("/api/v1/session/start").json()
sid = start["session"]["session_id"]

steps = [
    ("ANSWER_SUBMITTED", {"answer": "trapped"}),
    ("ANSWER_SUBMITTED", {"answer": "ruins"}),
    ("VERIFY_ANSWER", {"variant_id": "pointer-v1", "answer": "house"}),
    ("VERIFY_ANSWER", {"variant_id": "pointer-v2", "answer": "city"}),
    ("VERIFY_ANSWER", {"variant_id": "pointer-v3", "answer": "room"}),
    ("WORD_ANSWER", {"answer": "rupt"}),
]
for event, payload in steps:
    response = client.post(
        "/api/v1/learning/step",
        json={"session_id": sid, "event": event, "payload": payload},
    )
    response.raise_for_status()
    print(event, "->", response.json()["session"]["state"])

snapshot = client.get(f"/api/v1/session/{sid}").json()
assert snapshot["session"]["state"] == "DONE"
assert snapshot["session"]["node_status"] == "VERIFIED"
assert snapshot["session"]["word_status"] == "VERIFIED"
event_types = [event["event_type"] for event in snapshot["events"]]
for required in ["error_diagnosed", "patch_completed", "word_verified", "demo_completed"]:
    assert required in event_types, required
print("CLOSED_LOOP", sid, "events=", len(snapshot["events"]))
