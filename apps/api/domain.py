from __future__ import annotations

import copy
import json
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


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


GOLD = load_json("gold_relative_clause_pointer.json")
WORD = load_json("word_eruption.json")


class DomainError(Exception):
    code = "domain_error"


class SessionNotFound(DomainError):
    code = "session_not_found"


class InvalidTransition(DomainError):
    code = "invalid_transition"


class CommandConflict(DomainError):
    code = "command_id_conflict"


class StateConflict(DomainError):
    code = "state_conflict"


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: dict[str, Any]


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

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "StepResult":
        return cls(
            session=value["session"],
            ui_action=value["ui_action"],
            message=value["message"],
            error_type=value.get("error_type"),
            hint=value.get("hint"),
            current_task=value.get("current_task"),
            topology_delta=value.get("topology_delta"),
        )


@dataclass
class Transition:
    result: StepResult
    events: list[DomainEvent]


class LearningController:
    """Pure deterministic reducer. It never performs persistence."""

    @staticmethod
    def initial_state(session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "state": "TASK",
            "version": 0,
            "attempt": 0,
            "hint_level": 0,
            "variant_index": 0,
            "variant_passes": [],
            "node_status": "LEARNING",
            "word_status": "UNKNOWN",
            "agent_policy_version": "gold-loop-v2",
            "content_pack_version": GOLD["content_pack_version"],
        }

    @staticmethod
    def initial_result(state: dict[str, Any]) -> StepResult:
        return StepResult(
            session=copy.deepcopy(state),
            ui_action="SHOW_TASK",
            message="先判断 which 指向谁。",
            current_task=GOLD["task"],
        )

    @staticmethod
    def initial_events() -> list[DomainEvent]:
        return [
            DomainEvent("session_started", {"node_id": GOLD["node_id"]}),
            DomainEvent(
                "task_planned",
                {"task_id": GOLD["task"]["id"], "reason_code": "GOLD_NODE"},
            ),
        ]

    @staticmethod
    def current_task(state: dict[str, Any]) -> dict[str, Any] | None:
        state_name = state["state"]
        if state_name in {"TASK", "RETRY"}:
            return GOLD["task"]
        if state_name == "VERIFY":
            index = state["variant_index"]
            return GOLD["variants"][index] if index < len(GOLD["variants"]) else None
        if state_name == "WORD_TASK":
            return WORD["task"]
        return None

    @staticmethod
    def _event_allowed(state_name: str, event: str) -> bool:
        return (
            (state_name in {"TASK", "RETRY"} and event == "ANSWER_SUBMITTED")
            or (state_name == "VERIFY" and event == "VERIFY_ANSWER")
            or (state_name == "WORD_TASK" and event == "WORD_ANSWER")
        )

    def reduce(
        self,
        state: dict[str, Any],
        event: str,
        payload: dict[str, Any],
    ) -> Transition:
        if not self._event_allowed(state["state"], event):
            raise InvalidTransition(f"{state['state']}:{event}")

        next_state = copy.deepcopy(state)
        if event == "ANSWER_SUBMITTED":
            return self._answer_main(next_state, payload)
        if event == "VERIFY_ANSWER":
            return self._answer_variant(next_state, payload)
        return self._answer_word(next_state, payload)

    def _answer_main(
        self,
        state: dict[str, Any],
        payload: dict[str, Any],
    ) -> Transition:
        answer = str(payload.get("answer", "")).strip().lower()
        expected = GOLD["task"]["expected"].lower()
        state["attempt"] += 1

        if answer == expected:
            state["state"] = "VERIFY"
            result = StepResult(
                session=state,
                ui_action="SHOW_VARIANT",
                message="主任务已修正。现在换三道表面不同的新题验证。",
                current_task=GOLD["variants"][0],
            )
            return Transition(
                result,
                [DomainEvent("main_task_passed", {"attempt": state["attempt"]})],
            )

        state["state"] = "RETRY"
        state["hint_level"] = min(state["hint_level"] + 1, len(GOLD["hints"]))
        hint = GOLD["hints"][state["hint_level"] - 1]
        result = StepResult(
            session=state,
            ui_action="RETRY_TASK",
            message="定位到指向关系错误。",
            error_type="POINTER_ERROR",
            hint=hint,
            current_task=GOLD["task"],
        )
        return Transition(
            result,
            [
                DomainEvent(
                    "error_diagnosed",
                    {
                        "root_cause": "POINTER_ERROR",
                        "evidence": {"expected": expected, "actual": answer},
                    },
                ),
                DomainEvent(
                    "hint_given",
                    {"level": state["hint_level"], "hint": hint},
                ),
            ],
        )

    def _answer_variant(
        self,
        state: dict[str, Any],
        payload: dict[str, Any],
    ) -> Transition:
        index = state["variant_index"]
        if index >= len(GOLD["variants"]):
            raise InvalidTransition("verification_already_complete")

        variant = GOLD["variants"][index]
        if payload.get("variant_id") != variant["id"]:
            raise InvalidTransition("variant_id_mismatch")

        answer = str(payload.get("answer", "")).strip().lower()
        correct = answer == variant["expected"].lower()
        events = [
            DomainEvent(
                "variant_answered",
                {"variant_id": variant["id"], "correct": correct},
            )
        ]

        if not correct:
            return Transition(
                StepResult(
                    session=state,
                    ui_action="RETRY_VARIANT",
                    message="迁移题还没通过。只检查 which 的回指关系。",
                    error_type="POINTER_ERROR",
                    hint="先找 which 前面的先行词。",
                    current_task=variant,
                ),
                events,
            )

        state["variant_passes"].append(variant["id"])
        state["variant_index"] += 1
        if state["variant_index"] < len(GOLD["variants"]):
            return Transition(
                StepResult(
                    session=state,
                    ui_action="SHOW_VARIANT",
                    message=f"迁移验证 {state['variant_index']}/3 通过。",
                    current_task=GOLD["variants"][state["variant_index"]],
                ),
                events,
            )

        old_status = state["node_status"]
        state["node_status"] = "VERIFIED"
        state["state"] = "WORD_TASK"
        events.extend(
            [
                DomainEvent(
                    "patch_completed",
                    {
                        "node_id": GOLD["node_id"],
                        "result": "VERIFIED",
                        "evidence": state["variant_passes"],
                    },
                ),
                DomainEvent(
                    "learning_state_updated",
                    {
                        "node_id": GOLD["node_id"],
                        "from": old_status,
                        "to": "VERIFIED",
                    },
                ),
                DomainEvent(
                    "next_task_selected",
                    {
                        "task_id": WORD["task"]["id"],
                        "reason_code": "SECOND_CAPABILITY",
                    },
                ),
            ]
        )
        return Transition(
            StepResult(
                session=state,
                ui_action="SHOW_WORD_TASK",
                message="pointer 已通过 3/3 迁移验证。进入第二种能力：词根逻辑拆解。",
                current_task=WORD["task"],
                topology_delta={
                    "node_id": GOLD["node_id"],
                    "from": old_status,
                    "to": "VERIFIED",
                },
            ),
            events,
        )

    def _answer_word(
        self,
        state: dict[str, Any],
        payload: dict[str, Any],
    ) -> Transition:
        answer = str(payload.get("answer", "")).strip().lower()
        if answer != WORD["task"]["expected"].lower():
            return Transition(
                StepResult(
                    session=state,
                    ui_action="RETRY_WORD",
                    message="再看哪个部分承载 break / burst 的核心意义。",
                    hint="-ion 是名词后缀，先排除它。",
                    current_task=WORD["task"],
                ),
                [],
            )

        state["word_status"] = "VERIFIED"
        state["state"] = "DONE"
        events = [
            DomainEvent(
                "word_verified",
                {"node_id": WORD["node_id"], "result": "VERIFIED"},
            ),
            DomainEvent("demo_completed", {"result": "CLOSED_LOOP"}),
        ]
        return Transition(
            StepResult(
                session=state,
                ui_action="SHOW_RESULT",
                message=WORD["explanation"],
                topology_delta={
                    "nodes": [
                        {
                            "node_id": GOLD["node_id"],
                            "status": state["node_status"],
                        },
                        {
                            "node_id": WORD["node_id"],
                            "status": state["word_status"],
                        },
                    ]
                },
            ),
            events,
        )
