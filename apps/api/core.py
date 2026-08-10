from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(name: str) -> dict[str, Any]:
    return json.loads((CONTENT_DIR / name).read_text(encoding="utf-8"))


GOLD = load_json("gold_relative_clause_pointer.json")
WORD = load_json("word_eruption.json")


@dataclass
class StepResult:
    session: dict[str, Any]
    ui_action: str
    message: str
    error_type: str | None = None
    hint: str | None = None
    current_task: dict[str, Any] | None = None
    topology_delta: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "ui_action": self.ui_action,
            "message": self.message,
            "error_type": self.error_type,
            "hint": self.hint,
            "current_task": self.current_task,
            "topology_delta": self.topology_delta,
        }


class Store:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("LEARNING_DB_PATH", "/tmp/learning-agent.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                  session_id TEXT PRIMARY KEY,
                  state_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS learning_events (
                  event_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                """
            )

    def save_session(self, state: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(session_id,state_json,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(session_id) DO UPDATE SET state_json=excluded.state_json, updated_at=excluded.updated_at",
                (state["session_id"], json.dumps(state, ensure_ascii=False), utc_now()),
            )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT state_json FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        return json.loads(row["state_json"]) if row else None

    def append_event(self, session_id: str, event_type: str, payload: dict[str, Any], event_id: str | None = None) -> str:
        event_id = event_id or str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO learning_events(event_id,session_id,event_type,payload_json,created_at) VALUES(?,?,?,?,?)",
                (event_id, session_id, event_type, json.dumps(payload, ensure_ascii=False), utc_now()),
            )
        return event_id

    def events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_id,event_type,payload_json,created_at FROM learning_events WHERE session_id=? ORDER BY rowid",
                (session_id,),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


class LearningController:
    """Deterministic learning loop. LLM is deliberately absent from correctness decisions."""

    def __init__(self, store: Store):
        self.store = store

    def start(self) -> StepResult:
        session_id = str(uuid.uuid4())
        state = {
            "session_id": session_id,
            "state": "TASK",
            "attempt": 0,
            "hint_level": 0,
            "variant_index": 0,
            "variant_passes": [],
            "node_status": "LEARNING",
            "word_status": "UNKNOWN",
            "agent_policy_version": "gold-loop-v1",
            "content_pack_version": GOLD["content_pack_version"],
        }
        self.store.save_session(state)
        self.store.append_event(session_id, "session_started", {"node_id": GOLD["node_id"]})
        self.store.append_event(session_id, "task_planned", {"task_id": GOLD["task"]["id"], "reason_code": "GOLD_NODE"})
        return StepResult(state, "SHOW_TASK", "先判断 which 指向谁。", current_task=GOLD["task"])

    def _load(self, session_id: str) -> dict[str, Any]:
        state = self.store.get_session(session_id)
        if not state:
            raise KeyError("session_not_found")
        return state

    def step(self, session_id: str, event: str, payload: dict[str, Any], event_id: str | None = None) -> StepResult:
        state = self._load(session_id)
        self.store.append_event(session_id, event.lower(), payload, event_id=event_id)

        if event == "ANSWER_SUBMITTED" and state["state"] in {"TASK", "RETRY"}:
            return self._answer_main(state, payload)
        if event == "VERIFY_ANSWER" and state["state"] == "VERIFY":
            return self._answer_variant(state, payload)
        if event == "WORD_ANSWER" and state["state"] == "WORD_TASK":
            return self._answer_word(state, payload)
        raise ValueError(f"invalid_transition:{state['state']}:{event}")

    def _answer_main(self, state: dict[str, Any], payload: dict[str, Any]) -> StepResult:
        answer = str(payload.get("answer", "")).strip().lower()
        expected = GOLD["task"]["expected"].lower()
        state["attempt"] += 1
        if answer == expected:
            state["state"] = "VERIFY"
            self.store.append_event(state["session_id"], "main_task_passed", {"attempt": state["attempt"]})
            self.store.save_session(state)
            return StepResult(
                state,
                "SHOW_VARIANT",
                "主任务已修正。现在换三道表面不同的新题验证。",
                current_task=GOLD["variants"][0],
            )

        state["state"] = "RETRY"
        state["hint_level"] = min(state["hint_level"] + 1, len(GOLD["hints"]))
        hint = GOLD["hints"][state["hint_level"] - 1]
        self.store.append_event(
            state["session_id"],
            "error_diagnosed",
            {"root_cause": "POINTER_ERROR", "evidence": {"expected": expected, "actual": answer}},
        )
        self.store.append_event(state["session_id"], "hint_given", {"level": state["hint_level"], "hint": hint})
        self.store.save_session(state)
        return StepResult(state, "RETRY_TASK", "定位到指向关系错误。", error_type="POINTER_ERROR", hint=hint, current_task=GOLD["task"])

    def _answer_variant(self, state: dict[str, Any], payload: dict[str, Any]) -> StepResult:
        index = state["variant_index"]
        if index >= len(GOLD["variants"]):
            raise ValueError("verification_already_complete")
        variant = GOLD["variants"][index]
        if payload.get("variant_id") != variant["id"]:
            raise ValueError("variant_id_mismatch")
        answer = str(payload.get("answer", "")).strip().lower()
        correct = answer == variant["expected"].lower()
        self.store.append_event(state["session_id"], "variant_answered", {"variant_id": variant["id"], "correct": correct})
        if not correct:
            self.store.save_session(state)
            return StepResult(state, "RETRY_VARIANT", "迁移题还没通过。只检查 which 的回指关系。", error_type="POINTER_ERROR", hint="先找 which 前面的先行词。", current_task=variant)

        state["variant_passes"].append(variant["id"])
        state["variant_index"] += 1
        if state["variant_index"] < len(GOLD["variants"]):
            self.store.save_session(state)
            return StepResult(state, "SHOW_VARIANT", f"迁移验证 {state['variant_index']}/3 通过。", current_task=GOLD["variants"][state["variant_index"]])

        old = state["node_status"]
        state["node_status"] = "VERIFIED"
        state["state"] = "WORD_TASK"
        self.store.append_event(state["session_id"], "patch_completed", {"node_id": GOLD["node_id"], "result": "VERIFIED", "evidence": state["variant_passes"]})
        self.store.append_event(state["session_id"], "learning_state_updated", {"node_id": GOLD["node_id"], "from": old, "to": "VERIFIED"})
        self.store.append_event(state["session_id"], "next_task_selected", {"task_id": WORD["task"]["id"], "reason_code": "SECOND_CAPABILITY"})
        self.store.save_session(state)
        return StepResult(
            state,
            "SHOW_WORD_TASK",
            "pointer 已通过 3/3 迁移验证。进入第二种能力：词根逻辑拆解。",
            current_task=WORD["task"],
            topology_delta={"node_id": GOLD["node_id"], "from": old, "to": "VERIFIED"},
        )

    def _answer_word(self, state: dict[str, Any], payload: dict[str, Any]) -> StepResult:
        answer = str(payload.get("answer", "")).strip().lower()
        if answer != WORD["task"]["expected"].lower():
            self.store.save_session(state)
            return StepResult(state, "RETRY_WORD", "再看哪个部分承载 break / burst 的核心意义。", hint="-ion 是名词后缀，先排除它。", current_task=WORD["task"])
        state["word_status"] = "VERIFIED"
        state["state"] = "DONE"
        self.store.append_event(state["session_id"], "word_verified", {"node_id": WORD["node_id"], "result": "VERIFIED"})
        self.store.append_event(state["session_id"], "demo_completed", {"result": "CLOSED_LOOP"})
        self.store.save_session(state)
        return StepResult(
            state,
            "SHOW_RESULT",
            WORD["explanation"],
            topology_delta={
                "nodes": [
                    {"node_id": GOLD["node_id"], "status": state["node_status"]},
                    {"node_id": WORD["node_id"], "status": state["word_status"]},
                ]
            },
        )
