import json
import os
import sqlite3
import tempfile
from concurrent.futures import ThreadPoolExecutor

from apps.api.core import LearningController, StateConflict, Store


def request_id(session_id: str, suffix: str) -> str:
    return f"{session_id}:{suffix}"


def fresh_db(prefix: str) -> str:
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".db")
    os.close(fd)
    return path


def test_atomic_fault_injection_rolls_back_all_artifacts():
    controller = LearningController()
    for point in [
        "after_command_event",
        "after_events",
        "before_session_update",
        "before_receipt",
    ]:
        path = fresh_db(f"learning-agent-{point}-")

        def fault(name: str, expected: str = point):
            if name == expected:
                raise RuntimeError(f"fault:{name}")

        store = Store(path, fault_injector=fault)
        session = store.create_session(controller).session
        sid = session["session_id"]
        before_state = store.get_session(sid)
        before_events = store.events(sid)

        try:
            store.execute_command(
                controller,
                sid,
                request_id(sid, point),
                "ANSWER_SUBMITTED",
                {"answer": "trapped"},
                expected_version=0,
            )
            raise AssertionError("fault was not triggered")
        except RuntimeError as exc:
            assert str(exc) == f"fault:{point}"

        assert store.get_session(sid) == before_state
        assert store.events(sid) == before_events
        assert store.receipt_count(sid) == 0


def test_two_store_instances_enforce_optimistic_concurrency():
    path = fresh_db("learning-agent-concurrency-")
    controller = LearningController()
    store_a = Store(path)
    store_b = Store(path)
    session = store_a.create_session(controller).session
    sid = session["session_id"]

    def execute(store: Store, suffix: str):
        try:
            return store.execute_command(
                controller,
                sid,
                request_id(sid, suffix),
                "ANSWER_SUBMITTED",
                {"answer": "trapped"},
                expected_version=0,
            )
        except StateConflict:
            return "STATE_CONFLICT"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda item: execute(*item),
                [(store_a, "a"), (store_b, "b")],
            )
        )

    assert sum(result == "STATE_CONFLICT" for result in results) == 1
    assert store_a.get_session(sid)["version"] == 1
    command_events = [
        event
        for event in store_a.events(sid)
        if event["command_id"] is not None
        and event["event_id"] == event["command_id"]
    ]
    assert len(command_events) == 1
    assert store_a.receipt_count(sid) == 1


def test_concurrent_duplicate_command_returns_same_receipt():
    path = fresh_db("learning-agent-duplicate-")
    controller = LearningController()
    store_a = Store(path)
    store_b = Store(path)
    session = store_a.create_session(controller).session
    sid = session["session_id"]
    command_id = request_id(sid, "same")

    def execute(store: Store):
        return store.execute_command(
            controller,
            sid,
            command_id,
            "ANSWER_SUBMITTED",
            {"answer": "trapped"},
            expected_version=0,
        ).as_dict()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execute, [store_a, store_b]))

    assert results[0] == results[1]
    assert store_a.get_session(sid)["version"] == 1
    assert store_a.receipt_count(sid) == 1


def test_integrity_detects_snapshot_tampering():
    path = fresh_db("learning-agent-integrity-")
    controller = LearningController()
    store = Store(path)
    session = store.create_session(controller).session
    sid = session["session_id"]

    result = store.execute_command(
        controller,
        sid,
        request_id(sid, "one"),
        "ANSWER_SUBMITTED",
        {"answer": "trapped"},
        expected_version=0,
    )
    assert result.session["version"] == 1
    assert store.integrity(controller, sid)["consistent"] is True

    with sqlite3.connect(path) as conn:
        raw = conn.execute(
            "SELECT state_json FROM sessions WHERE session_id=?",
            (sid,),
        ).fetchone()[0]
        state = json.loads(raw)
        state["hint_level"] = 99
        conn.execute(
            "UPDATE sessions SET state_json=? WHERE session_id=?",
            (json.dumps(state), sid),
        )

    integrity = store.integrity(controller, sid)
    assert integrity["consistent"] is False
