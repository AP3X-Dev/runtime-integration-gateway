"""Test RIG v0 event logging system."""

import os
import tempfile
from pathlib import Path

import pytest

from rig_core.audit import AuditLog, compute_input_hash, now_event
from rig_core.policy import Policy
from rig_core.runtime import RegisteredTool, RigRuntime
from rig_core.rtp import CallContext, ToolDef
from rig_core.secrets import SecretsStore


class TestEventLogging:
    """Test event logging with v0 requirements."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def audit_log(self, temp_db):
        """Create an audit log instance."""
        return AuditLog(temp_db)

    @pytest.fixture
    def runtime(self, audit_log):
        """Create a runtime with audit logging."""
        policy = Policy(allowed_tools=None, require_approval_for=set(), timeout_seconds=30, retries=2)
        secrets = SecretsStore()
        runtime = RigRuntime(policy=policy, secrets=secrets, audit=audit_log)
        
        # Register a simple test tool
        def test_impl(args, secrets, ctx):
            return {"result": f"Hello {args.get('name', 'World')}"}
        
        tool_def = ToolDef(
            name="test.greet",
            description="A test greeting tool",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
            error_schema={"type": "object"},
            auth_slots=["env:TEST_API_KEY"],
            risk_class="read",
        )
        
        reg_tool = RegisteredTool(tool=tool_def, impl=test_impl, pack="test-pack", pack_version="1.0.0")
        runtime.register("test.greet", reg_tool)
        runtime.set_snapshot_meta("test-hash", "test-version")
        
        return runtime

    def test_compute_input_hash(self):
        """Test input hash computation."""
        args1 = {"name": "Alice", "age": 30}
        args2 = {"age": 30, "name": "Alice"}  # Different order
        args3 = {"name": "Bob", "age": 30}
        
        hash1 = compute_input_hash(args1)
        hash2 = compute_input_hash(args2)
        hash3 = compute_input_hash(args3)
        
        # Same data, different order should produce same hash
        assert hash1 == hash2
        # Different data should produce different hash
        assert hash1 != hash3
        # Hash should be 64 hex characters (SHA256)
        assert len(hash1) == 64

    def test_event_creation(self):
        """Test event creation with now_event helper."""
        event = now_event(
            tool_name="test.tool",
            tenant_id="tenant-123",
            run_id="run-456",
            input_hash="abc123",
            outcome="ok",
            duration_ms=150,
            redacted_auth_marker="env:API_KEY",
        )
        
        assert event.tool == "test.tool"
        assert event.tenant_id == "tenant-123"
        assert event.run_id == "run-456"
        assert event.input_hash == "abc123"
        assert event.outcome == "ok"
        assert event.duration_ms == 150
        assert event.redacted_auth_marker == "env:API_KEY"
        assert event.timestamp.endswith('Z')  # ISO 8601 UTC
        assert event.ts_unix is not None

    def test_event_storage_and_query(self, audit_log):
        """Test event storage and querying."""
        # Create and write events
        event1 = now_event(
            tool_name="test.tool1",
            tenant_id="tenant-123",
            run_id="run-1",
            input_hash="hash1",
            outcome="ok",
            duration_ms=100,
        )
        event2 = now_event(
            tool_name="test.tool2",
            tenant_id="tenant-123",
            run_id="run-2",
            input_hash="hash2",
            outcome="error",
            duration_ms=200,
        )
        event3 = now_event(
            tool_name="test.tool3",
            tenant_id="tenant-456",
            run_id="run-3",
            input_hash="hash3",
            outcome="ok",
            duration_ms=150,
        )
        
        audit_log.write(event1)
        audit_log.write(event2)
        audit_log.write(event3)
        
        # Query by run_id
        run1_events = audit_log.query_by_run_id("run-1")
        assert len(run1_events) == 1
        assert run1_events[0]["tool"] == "test.tool1"
        
        # Query by tenant_id
        tenant123_events = audit_log.query_by_tenant_id("tenant-123")
        assert len(tenant123_events) == 2
        
        tenant456_events = audit_log.query_by_tenant_id("tenant-456")
        assert len(tenant456_events) == 1

    def test_runtime_generates_events(self, runtime, audit_log):
        """Test that runtime generates exactly one event per tool call."""
        ctx = CallContext(tenant_id="tenant-123", request_id="run-abc")
        
        # Make a successful call
        result = runtime.call("test.greet", {"name": "Alice"}, ctx)
        
        assert result.ok is True
        
        # Query events
        events = audit_log.query_by_run_id("run-abc")
        assert len(events) == 1
        
        event = events[0]
        assert event["tool"] == "test.greet"
        assert event["tenant_id"] == "tenant-123"
        assert event["run_id"] == "run-abc"
        assert event["outcome"] == "ok"
        assert event["duration_ms"] > 0
        assert event["input_hash"] is not None
        assert event["redacted_auth_marker"] == "env:TEST_API_KEY"

    def test_event_outcomes(self, runtime, audit_log):
        """Test different event outcomes."""
        # Test policy_denied outcome
        runtime.policy = Policy(allowed_tools=set(), require_approval_for=set(), timeout_seconds=30, retries=2)
        ctx1 = CallContext(tenant_id="tenant-1", request_id="run-1")
        result1 = runtime.call("test.greet", {"name": "Alice"}, ctx1)
        
        assert result1.ok is False
        events1 = audit_log.query_by_run_id("run-1")
        assert events1[0]["outcome"] == "policy_denied"
        
        # Test approval_required outcome
        runtime.policy = Policy(allowed_tools=None, require_approval_for={"read"}, timeout_seconds=30, retries=2)
        ctx2 = CallContext(tenant_id="tenant-2", request_id="run-2")
        result2 = runtime.call("test.greet", {"name": "Bob"}, ctx2)
        
        assert result2.ok is False
        events2 = audit_log.query_by_run_id("run-2")
        assert events2[0]["outcome"] == "approval_required"

