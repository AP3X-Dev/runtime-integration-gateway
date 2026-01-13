from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Literal, Optional


# Event outcome types
EventOutcome = Literal["ok", "error", "approval_required", "policy_denied"]


@dataclass
class AuditEvent:
    """Enhanced audit event for RIG v0.

    Fields:
        timestamp: ISO 8601 UTC timestamp
        tenant_id: Required tenant identifier
        run_id: Required run identifier (correlation_id)
        tool: Tool name (e.g., stripe.customers.create)
        input_hash: SHA256 hash of normalized input JSON
        outcome: One of ok, error, approval_required, policy_denied
        duration_ms: Execution duration in milliseconds
        redacted_auth_marker: Auth slot indicator (never the secret value)

    Legacy fields (for backward compatibility):
        ts_unix: Unix timestamp
        error_type: Error type if outcome is error
        pack: Pack name
        pack_version: Pack version
        interface_hash: Interface hash
        args_sanitized: Sanitized arguments (optional)
    """
    # v0 required fields
    timestamp: str  # ISO 8601 UTC
    tenant_id: str
    run_id: str
    tool: str
    input_hash: str
    outcome: EventOutcome
    duration_ms: int
    redacted_auth_marker: Optional[str] = None

    # Legacy/additional fields
    ts_unix: Optional[float] = None
    error_type: Optional[str] = None
    pack: Optional[str] = None
    pack_version: Optional[str] = None
    interface_hash: Optional[str] = None
    args_sanitized: Optional[Dict[str, Any]] = None


class AuditLog:
    """SQLite audit sink for RIG v0.

    v0 default path: .rig/rig_audit.sqlite

    Events are append-only and queryable by run_id and tenant_id.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            # Create v0 events table with all required fields
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    redacted_auth_marker TEXT,
                    ts_unix REAL,
                    error_type TEXT,
                    pack TEXT,
                    pack_version TEXT,
                    interface_hash TEXT,
                    args_json TEXT
                )
                """
            )

            # Create indices for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_run_id ON audit_events(run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant_id ON audit_events(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tool ON audit_events(tool)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)")

            conn.commit()
        finally:
            conn.close()

    def write(self, event: AuditEvent) -> None:
        """Write an event to the audit log (append-only)."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO audit_events (
                    timestamp, tenant_id, run_id, tool, input_hash, outcome, duration_ms,
                    redacted_auth_marker, ts_unix, error_type, pack, pack_version,
                    interface_hash, args_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp,
                    event.tenant_id,
                    event.run_id,
                    event.tool,
                    event.input_hash,
                    event.outcome,
                    event.duration_ms,
                    event.redacted_auth_marker,
                    event.ts_unix,
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

    def query_by_run_id(self, run_id: str) -> list[Dict[str, Any]]:
        """Query events by run_id."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT * FROM audit_events WHERE run_id = ? ORDER BY timestamp",
                (run_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def query_by_tenant_id(self, tenant_id: str, limit: int = 100) -> list[Dict[str, Any]]:
        """Query events by tenant_id."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT * FROM audit_events WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?",
                (tenant_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


def compute_input_hash(args: Dict[str, Any]) -> str:
    """Compute SHA256 hash of normalized input JSON.

    Args:
        args: Input arguments dictionary

    Returns:
        SHA256 hex digest
    """
    # Normalize by sorting keys and using compact JSON
    normalized = json.dumps(args, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode()).hexdigest()


def now_event(
    tool_name: str,
    tenant_id: str,
    run_id: str,
    input_hash: str,
    outcome: EventOutcome,
    duration_ms: int,
    redacted_auth_marker: Optional[str] = None,
    **kwargs: Any
) -> AuditEvent:
    """Create an audit event with current timestamp.

    Args:
        tool_name: Tool name
        tenant_id: Tenant identifier
        run_id: Run identifier
        input_hash: SHA256 hash of input
        outcome: Event outcome
        duration_ms: Duration in milliseconds
        redacted_auth_marker: Auth slot marker (optional)
        **kwargs: Additional fields

    Returns:
        AuditEvent instance
    """
    now = datetime.utcnow()
    return AuditEvent(
        timestamp=now.isoformat() + 'Z',
        tenant_id=tenant_id,
        run_id=run_id,
        tool=tool_name,
        input_hash=input_hash,
        outcome=outcome,
        duration_ms=duration_ms,
        redacted_auth_marker=redacted_auth_marker,
        ts_unix=time.time(),
        **kwargs
    )
