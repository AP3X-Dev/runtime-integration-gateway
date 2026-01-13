from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AuditEvent:
    ts_unix: float
    tenant_id: Optional[str]
    tool_name: str
    correlation_id: Optional[str]
    ok: bool
    error_type: Optional[str] = None
    pack: Optional[str] = None
    pack_version: Optional[str] = None
    interface_hash: Optional[str] = None
    args_sanitized: Optional[Dict[str, Any]] = None


class AuditLog:
    """SQLite audit sink.

    v0 default path: .rig/rig_audit.sqlite
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_unix REAL NOT NULL,
                    tenant_id TEXT,
                    tool_name TEXT NOT NULL,
                    correlation_id TEXT,
                    ok INTEGER NOT NULL,
                    error_type TEXT,
                    pack TEXT,
                    pack_version TEXT,
                    interface_hash TEXT,
                    args_json TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def write(self, event: AuditEvent) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO audit_events (
                    ts_unix, tenant_id, tool_name, correlation_id, ok, error_type,
                    pack, pack_version, interface_hash, args_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.ts_unix,
                    event.tenant_id,
                    event.tool_name,
                    event.correlation_id,
                    1 if event.ok else 0,
                    event.error_type,
                    event.pack,
                    event.pack_version,
                    event.interface_hash,
                    json.dumps(event.args_sanitized) if event.args_sanitized is not None else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def now_event(tool_name: str, ok: bool, **kwargs: Any) -> AuditEvent:
    return AuditEvent(ts_unix=time.time(), tool_name=tool_name, ok=ok, **kwargs)
