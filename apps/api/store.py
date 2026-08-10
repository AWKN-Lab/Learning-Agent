from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .domain import (
    CommandConflict,
    GOLD,
    LearningController,
    SessionNotFound,
    StateConflict,
    StepResult,
    canonical_json,
    utc_now,
)
from .runtime_errors import RateLimitExceeded, SessionExpired, SessionUnauthorized

FaultInjector = Callable[[str], None]


class Store:
    """SQLite persistence and runtime governance for the demo."""

    def __init__(
        self,
        db_path: str | None = None,
        fault_injector: FaultInjector | None = None,
    ):
        self.db_path = db_path or os.getenv(
            "LEARNING_DB_PATH",
            "/tmp/learning-agent.db",
        )
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.fault_injector = fault_injector
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=5.0,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    @staticmethod
    def _table_columns(
        conn: sqlite3.Connection,
        table: str,
    ) -> set[str]:
        return {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                  session_id TEXT PRIMARY KEY,
                  state_json TEXT NOT NULL,
                  version INTEGER NOT NULL DEFAULT 0,
                  token_hash TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  last_accessed_at TEXT,
                  expires_at TEXT
                );
                CREATE TABLE IF NOT EXISTS learning_events (
                  event_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  command_id TEXT,
                  event_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                    ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS command_receipts (
                  command_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  request_hash TEXT NOT NULL,
                  response_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                    ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS rate_limits (
                  key_hash TEXT PRIMARY KEY,
                  window_start INTEGER NOT NULL,
                  count INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_session
                  ON learning_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_expiry
                  ON sessions(expires_at);
                """
            )
            self._migrate_legacy_schema(conn)

    def _migrate_legacy_schema(self, conn: sqlite3.Connection) -> None:
        session_columns = self._table_columns(conn, "sessions")
        additions = {
            "version": "INTEGER NOT NULL DEFAULT 0",
            "created_at": "TEXT",
            "token_hash": "TEXT",
            "last_accessed_at": "TEXT",
            "expires_at": "TEXT",
        }
        for column, definition in additions.items():
            if column not in session_columns:
                conn.execute(
                    f"ALTER TABLE sessions ADD COLUMN {column} {definition}"
                )
        conn.execute(
            """
            UPDATE sessions
            SET created_at=COALESCE(created_at, updated_at),
                last_accessed_at=COALESCE(last_accessed_at, updated_at)
            """
        )

        event_columns = self._table_columns(conn, "learning_events")
        if "command_id" not in event_columns:
            conn.execute(
                "ALTER TABLE learning_events ADD COLUMN command_id TEXT"
            )

    def _fault(self, point: str) -> None:
        if self.fault_injector:
            self.fault_injector(point)

    @staticmethod
    def _request_hash(
        session_id: str,
        command_id: str,
        event: str,
        payload: dict[str, Any],
        expected_version: int,
    ) -> str:
        encoded = canonical_json(
            {
                "session_id": session_id,
                "command_id": command_id,
                "event": event,
                "payload": payload,
                "expected_version": expected_version,
            }
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _insert_event(
        conn: sqlite3.Connection,
        event_id: str,
        session_id: str,
        command_id: str | None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO learning_events(
              event_id, session_id, command_id, event_type, payload_json, created_at
            ) VALUES(?,?,?,?,?,?)
            """,
            (
                event_id,
                session_id,
                command_id,
                event_type,
                canonical_json(payload),
                utc_now(),
            ),
        )

    @staticmethod
    def _expiry(ttl_seconds: int) -> str:
        return (
            datetime.now(timezone.utc)
            + timedelta(seconds=ttl_seconds)
        ).isoformat()

    @staticmethod
    def _is_expired(expires_at: str | None) -> bool:
        if not expires_at:
            return False
        return datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc)

    @staticmethod
    def _authorize_row(
        row: sqlite3.Row,
        supplied_token_hash: str | None,
    ) -> None:
        stored_hash = row["token_hash"]
        if stored_hash:
            if not supplied_token_hash or not hmac.compare_digest(
                stored_hash,
                supplied_token_hash,
            ):
                raise SessionUnauthorized()
        if Store._is_expired(row["expires_at"]):
            raise SessionExpired()

    def create_session(
        self,
        controller: LearningController,
        *,
        token_hash: str | None = None,
        ttl_seconds: int = 7200,
    ) -> StepResult:
        session_id = str(uuid.uuid4())
        state = controller.initial_state(session_id)
        result = controller.initial_result(state)
        now = utc_now()
        expires_at = self._expiry(ttl_seconds)

        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """
                    INSERT INTO sessions(
                      session_id, state_json, version, token_hash,
                      created_at, updated_at, last_accessed_at, expires_at
                    ) VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        session_id,
                        canonical_json(state),
                        0,
                        token_hash,
                        now,
                        now,
                        now,
                        expires_at,
                    ),
                )
                for index, event in enumerate(
                    controller.initial_events(),
                    start=1,
                ):
                    self._insert_event(
                        conn,
                        f"{session_id}:init:{index}",
                        session_id,
                        None,
                        event.event_type,
                        event.payload,
                    )
                conn.execute("COMMIT")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        return result

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT state_json, version
                FROM sessions
                WHERE session_id=?
                """,
                (session_id,),
            ).fetchone()
        if not row:
            return None
        state = json.loads(row["state_json"])
        state["version"] = row["version"]
        return state

    def get_authorized_session(
        self,
        session_id: str,
        token_hash: str | None,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    """
                    SELECT state_json, version, token_hash, expires_at
                    FROM sessions
                    WHERE session_id=?
                    """,
                    (session_id,),
                ).fetchone()
                if not row:
                    raise SessionNotFound(session_id)
                self._authorize_row(row, token_hash)
                conn.execute(
                    """
                    UPDATE sessions
                    SET last_accessed_at=?
                    WHERE session_id=?
                    """,
                    (utc_now(), session_id),
                )
                conn.execute("COMMIT")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

        state = json.loads(row["state_json"])
        state["version"] = row["version"]
        return state

    def events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT event_id, command_id, event_type, payload_json, created_at
                FROM learning_events
                WHERE session_id=?
                ORDER BY rowid
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "command_id": row["command_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def receipt_count(self, session_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM command_receipts
                WHERE session_id=?
                """,
                (session_id,),
            ).fetchone()
        return int(row["n"])

    def execute_command(
        self,
        controller: LearningController,
        session_id: str,
        command_id: str,
        event: str,
        payload: dict[str, Any],
        expected_version: int,
        *,
        token_hash: str | None = None,
    ) -> StepResult:
        request_hash = self._request_hash(
            session_id,
            command_id,
            event,
            payload,
            expected_version,
        )

        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")

                row = conn.execute(
                    """
                    SELECT state_json, version, token_hash, expires_at
                    FROM sessions
                    WHERE session_id=?
                    """,
                    (session_id,),
                ).fetchone()
                if not row:
                    raise SessionNotFound(session_id)
                self._authorize_row(row, token_hash)

                receipt = conn.execute(
                    """
                    SELECT session_id, request_hash, response_json
                    FROM command_receipts
                    WHERE command_id=?
                    """,
                    (command_id,),
                ).fetchone()
                if receipt:
                    if (
                        receipt["session_id"] != session_id
                        or receipt["request_hash"] != request_hash
                    ):
                        raise CommandConflict(command_id)
                    conn.execute(
                        """
                        UPDATE sessions
                        SET last_accessed_at=?
                        WHERE session_id=?
                        """,
                        (utc_now(), session_id),
                    )
                    conn.execute("COMMIT")
                    return StepResult.from_dict(
                        json.loads(receipt["response_json"])
                    )

                version = int(row["version"])
                if version != expected_version:
                    raise StateConflict(
                        f"expected={expected_version}, actual={version}"
                    )

                state = json.loads(row["state_json"])
                state["version"] = version
                transition = controller.reduce(state, event, payload)
                next_version = version + 1
                transition.result.session["version"] = next_version

                self._insert_event(
                    conn,
                    command_id,
                    session_id,
                    command_id,
                    event,
                    payload,
                )
                self._fault("after_command_event")

                for index, domain_event in enumerate(
                    transition.events,
                    start=1,
                ):
                    self._insert_event(
                        conn,
                        f"{command_id}#{index}",
                        session_id,
                        command_id,
                        domain_event.event_type,
                        domain_event.payload,
                    )
                self._fault("after_events")
                self._fault("before_session_update")

                now = utc_now()
                update = conn.execute(
                    """
                    UPDATE sessions
                    SET state_json=?, version=?, updated_at=?, last_accessed_at=?
                    WHERE session_id=? AND version=?
                    """,
                    (
                        canonical_json(transition.result.session),
                        next_version,
                        now,
                        now,
                        session_id,
                        version,
                    ),
                )
                if update.rowcount != 1:
                    raise StateConflict("optimistic_update_failed")

                self._fault("before_receipt")
                response_json = canonical_json(
                    transition.result.as_dict()
                )
                conn.execute(
                    """
                    INSERT INTO command_receipts(
                      command_id, session_id, request_hash, response_json, created_at
                    ) VALUES(?,?,?,?,?)
                    """,
                    (
                        command_id,
                        session_id,
                        request_hash,
                        response_json,
                        utc_now(),
                    ),
                )
                conn.execute("COMMIT")
                return transition.result
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def rebuild_session(
        self,
        controller: LearningController,
        session_id: str,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if not exists:
                raise SessionNotFound(session_id)

            commands = conn.execute(
                """
                SELECT event_type, payload_json
                FROM learning_events
                WHERE session_id=? AND command_id IS NOT NULL
                  AND event_id=command_id
                ORDER BY rowid
                """,
                (session_id,),
            ).fetchall()

        state = controller.initial_state(session_id)
        for version, row in enumerate(commands, start=1):
            transition = controller.reduce(
                state,
                row["event_type"],
                json.loads(row["payload_json"]),
            )
            state = transition.result.session
            state["version"] = version
        return state

    def integrity(
        self,
        controller: LearningController,
        session_id: str,
    ) -> dict[str, Any]:
        stored = self.get_session(session_id)
        if not stored:
            raise SessionNotFound(session_id)
        baseline = controller.initial_state(session_id)
        replay_supported = (
            stored.get("agent_policy_version")
            == baseline.get("agent_policy_version")
            and stored.get("content_pack_version")
            == baseline.get("content_pack_version")
        )
        if not replay_supported:
            return {
                "consistent": None,
                "replay_supported": False,
                "stored_version": stored["version"],
                "replayed_version": None,
                "event_count": len(self.events(session_id)),
                "receipt_count": self.receipt_count(session_id),
            }

        rebuilt = self.rebuild_session(controller, session_id)
        return {
            "consistent": canonical_json(stored) == canonical_json(rebuilt),
            "replay_supported": True,
            "stored_version": stored["version"],
            "replayed_version": rebuilt["version"],
            "event_count": len(self.events(session_id)),
            "receipt_count": self.receipt_count(session_id),
        }

    def consume_rate_limit(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now_ts: int | None = None,
    ) -> int:
        now_ts = int(
            datetime.now(timezone.utc).timestamp()
            if now_ts is None
            else now_ts
        )
        window_start = now_ts - (now_ts % window_seconds)
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()

        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    """
                    SELECT window_start, count
                    FROM rate_limits
                    WHERE key_hash=?
                    """,
                    (key_hash,),
                ).fetchone()

                if not row or row["window_start"] != window_start:
                    count = 1
                    conn.execute(
                        """
                        INSERT INTO rate_limits(key_hash, window_start, count)
                        VALUES(?,?,?)
                        ON CONFLICT(key_hash) DO UPDATE
                        SET window_start=excluded.window_start,
                            count=excluded.count
                        """,
                        (key_hash, window_start, count),
                    )
                else:
                    if int(row["count"]) >= limit:
                        raise RateLimitExceeded()
                    count = int(row["count"]) + 1
                    conn.execute(
                        """
                        UPDATE rate_limits
                        SET count=?
                        WHERE key_hash=?
                        """,
                        (count, key_hash),
                    )

                conn.execute(
                    "DELETE FROM rate_limits WHERE window_start < ?",
                    (window_start - 2 * window_seconds,),
                )
                conn.execute("COMMIT")
                return count
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def cleanup_sessions(
        self,
        *,
        now_iso: str | None = None,
        max_sessions: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        now_iso = now_iso or utc_now()
        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                expired = [
                    row["session_id"]
                    for row in conn.execute(
                        """
                        SELECT session_id
                        FROM sessions
                        WHERE expires_at IS NOT NULL AND expires_at <= ?
                        ORDER BY expires_at
                        """,
                        (now_iso,),
                    ).fetchall()
                ]

                overflow: list[str] = []
                if max_sessions is not None and max_sessions >= 0:
                    active_count = int(
                        conn.execute(
                            """
                            SELECT COUNT(*) AS n
                            FROM sessions
                            WHERE expires_at IS NULL OR expires_at > ?
                            """,
                            (now_iso,),
                        ).fetchone()["n"]
                    )
                    extra = max(0, active_count - max_sessions)
                    if extra:
                        overflow = [
                            row["session_id"]
                            for row in conn.execute(
                                """
                                SELECT session_id
                                FROM sessions
                                WHERE expires_at IS NULL OR expires_at > ?
                                ORDER BY COALESCE(last_accessed_at, updated_at)
                                LIMIT ?
                                """,
                                (now_iso, extra),
                            ).fetchall()
                        ]

                targets = list(dict.fromkeys(expired + overflow))
                if targets and not dry_run:
                    conn.executemany(
                        "DELETE FROM sessions WHERE session_id=?",
                        [(session_id,) for session_id in targets],
                    )
                if dry_run:
                    conn.execute("ROLLBACK")
                else:
                    conn.execute("COMMIT")
                return {
                    "deleted": 0 if dry_run else len(targets),
                    "candidates": len(targets),
                    "expired": len(expired),
                    "overflow": len(overflow),
                    "dry_run": dry_run,
                }
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def readiness(self) -> dict[str, Any]:
        with self._connect() as conn:
            conn.execute("SELECT 1").fetchone()
            tables = {
                row["name"]
                for row in conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    """
                ).fetchall()
            }
        required = {
            "sessions",
            "learning_events",
            "command_receipts",
            "rate_limits",
        }
        if not required.issubset(tables):
            raise RuntimeError("database_schema_incomplete")
        return {
            "database": "ok",
            "content_pack": GOLD["content_pack_version"],
            "policy": "gold-loop-v2",
        }
