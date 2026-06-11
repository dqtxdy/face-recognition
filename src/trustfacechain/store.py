"""SQLite persistence for the product prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
import time
from typing import Any


@dataclass(frozen=True)
class StoredIdentity:
    subject_id: str
    model_version: str
    template_commitment: str
    template_salt: str
    consent_hash: str
    encrypted_embedding: bytes
    revoked: bool
    created_at: int
    updated_at: int
    revoked_at: int | None


@dataclass(frozen=True)
class StoredEvent:
    event_id: int
    event_type: str
    subject_id: str
    payload: dict[str, Any]
    created_at: int


class ProductStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS identities (
                    subject_id TEXT PRIMARY KEY,
                    model_version TEXT NOT NULL,
                    template_commitment TEXT NOT NULL,
                    template_salt TEXT NOT NULL,
                    consent_hash TEXT NOT NULL,
                    encrypted_embedding BLOB NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    revoked_at INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_events_subject
                ON audit_events(subject_id, event_id)
                """
            )

    def get_identity(self, subject_id: str) -> StoredIdentity | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM identities WHERE subject_id = ?",
                (subject_id,),
            ).fetchone()
        return _identity_from_row(row) if row else None

    def create_identity(
        self,
        *,
        subject_id: str,
        model_version: str,
        template_commitment: str,
        template_salt: str,
        consent_hash: str,
        encrypted_embedding: bytes,
    ) -> StoredIdentity:
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO identities (
                    subject_id,
                    model_version,
                    template_commitment,
                    template_salt,
                    consent_hash,
                    encrypted_embedding,
                    revoked,
                    created_at,
                    updated_at,
                    revoked_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, NULL)
                """,
                (
                    subject_id,
                    model_version,
                    template_commitment,
                    template_salt,
                    consent_hash,
                    encrypted_embedding,
                    now,
                    now,
                ),
            )
        identity = self.get_identity(subject_id)
        if identity is None:
            raise RuntimeError("identity insert failed")
        return identity

    def replace_identity(
        self,
        *,
        subject_id: str,
        model_version: str,
        template_commitment: str,
        template_salt: str,
        consent_hash: str,
        encrypted_embedding: bytes,
    ) -> StoredIdentity:
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE identities
                SET model_version = ?,
                    template_commitment = ?,
                    template_salt = ?,
                    consent_hash = ?,
                    encrypted_embedding = ?,
                    revoked = 0,
                    updated_at = ?,
                    revoked_at = NULL
                WHERE subject_id = ?
                """,
                (
                    model_version,
                    template_commitment,
                    template_salt,
                    consent_hash,
                    encrypted_embedding,
                    now,
                    subject_id,
                ),
            )
        identity = self.get_identity(subject_id)
        if identity is None:
            raise RuntimeError("identity update failed")
        return identity

    def revoke_identity(self, subject_id: str) -> StoredIdentity:
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE identities
                SET revoked = 1,
                    revoked_at = ?,
                    updated_at = ?
                WHERE subject_id = ?
                """,
                (now, now, subject_id),
            )
        identity = self.get_identity(subject_id)
        if identity is None:
            raise KeyError(subject_id)
        return identity

    def add_event(
        self,
        *,
        event_type: str,
        subject_id: str,
        payload: dict[str, Any],
    ) -> StoredEvent:
        now = _now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_events (event_type, subject_id, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event_type,
                    subject_id,
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                    now,
                ),
            )
            event_id = int(cursor.lastrowid)
        return StoredEvent(
            event_id=event_id,
            event_type=event_type,
            subject_id=subject_id,
            payload=payload,
            created_at=now,
        )

    def list_events(
        self,
        *,
        subject_id: str | None = None,
        limit: int = 100,
    ) -> list[StoredEvent]:
        query = "SELECT * FROM audit_events"
        params: tuple[Any, ...]
        if subject_id:
            query += " WHERE subject_id = ?"
            params = (subject_id, limit)
        else:
            params = (limit,)
        query += " ORDER BY event_id DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_event_from_row(row) for row in rows]

    def metrics(self) -> dict[str, int]:
        with self._connect() as conn:
            identities = conn.execute("SELECT COUNT(*) FROM identities").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM identities WHERE revoked = 0"
            ).fetchone()[0]
            revoked = conn.execute(
                "SELECT COUNT(*) FROM identities WHERE revoked = 1"
            ).fetchone()[0]
            events = conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        return {
            "identities": int(identities),
            "activeIdentities": int(active),
            "revokedIdentities": int(revoked),
            "auditEvents": int(events),
        }


def _identity_from_row(row: sqlite3.Row) -> StoredIdentity:
    return StoredIdentity(
        subject_id=row["subject_id"],
        model_version=row["model_version"],
        template_commitment=row["template_commitment"],
        template_salt=row["template_salt"],
        consent_hash=row["consent_hash"],
        encrypted_embedding=row["encrypted_embedding"],
        revoked=bool(row["revoked"]),
        created_at=int(row["created_at"]),
        updated_at=int(row["updated_at"]),
        revoked_at=int(row["revoked_at"]) if row["revoked_at"] is not None else None,
    )


def _event_from_row(row: sqlite3.Row) -> StoredEvent:
    return StoredEvent(
        event_id=int(row["event_id"]),
        event_type=row["event_type"],
        subject_id=row["subject_id"],
        payload=json.loads(row["payload_json"]),
        created_at=int(row["created_at"]),
    )


def _now() -> int:
    return int(time.time())

