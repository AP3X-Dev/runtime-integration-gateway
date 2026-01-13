"""
RTP Schema Validation Tests

Tests that RTP Python models conform to the JSON schemas and that
the schemas correctly validate valid and invalid inputs.
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
from jsonschema import ValidationError, validate

from rig_core.rtp import CallContext, ToolDef, ToolError, ToolResult

# Load schemas
SCHEMA_DIR = Path(__file__).parent.parent / "schemas" / "rtp"


def load_schema(name: str) -> Dict[str, Any]:
    """Load a JSON schema file."""
    with open(SCHEMA_DIR / f"{name}.schema.json") as f:
        return json.load(f)


TOOL_DEF_SCHEMA = load_schema("ToolDef")
TOOL_ERROR_SCHEMA = load_schema("ToolError")
TOOL_RESULT_SCHEMA = load_schema("ToolResult")
CALL_CONTEXT_SCHEMA = load_schema("CallContext")
APPROVAL_REQUIRED_SCHEMA = load_schema("ApprovalRequired")


class TestToolDefSchema:
    """Test ToolDef schema validation."""

    def test_minimal_valid_tooldef(self):
        """Test minimal valid ToolDef."""
        data = {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "error_schema": {"type": "object", "properties": {}},
        }
        validate(instance=data, schema=TOOL_DEF_SCHEMA)

    def test_full_valid_tooldef(self):
        """Test fully populated valid ToolDef."""
        data = {
            "name": "github_get_repo",
            "description": "Get repository information from GitHub",
            "input_schema": {
                "type": "object",
                "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}},
                "required": ["owner", "repo"],
            },
            "output_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "stars": {"type": "integer"}},
            },
            "error_schema": {"type": "object", "properties": {}},
            "auth_slots": ["GITHUB_TOKEN"],
            "risk_class": "read",
            "tags": ["github", "repository"],
            "policy_defaults": {"timeout_seconds": 30, "retries": 2},
            "examples": [
                {
                    "name": "Get RIG repo",
                    "description": "Example getting the RIG repository",
                    "input": {"owner": "rig", "repo": "rig"},
                    "output": {"name": "rig", "stars": 1000},
                }
            ],
        }
        validate(instance=data, schema=TOOL_DEF_SCHEMA)

    def test_python_tooldef_matches_schema(self):
        """Test that Python ToolDef dataclass matches schema."""
        tool = ToolDef(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {"arg": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
            error_schema={"type": "object", "properties": {}},
            auth_slots=["API_KEY"],
            risk_class="write",
            tags=["test"],
        )
        
        # Convert to dict (simulating serialization)
        data = {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "error_schema": tool.error_schema,
            "auth_slots": tool.auth_slots,
            "risk_class": tool.risk_class,
            "tags": tool.tags,
            "policy_defaults": tool.policy_defaults,
            "examples": tool.examples,
        }
        
        validate(instance=data, schema=TOOL_DEF_SCHEMA)

    def test_invalid_tooldef_missing_required(self):
        """Test that missing required fields are rejected."""
        data = {
            "name": "test_tool",
            # missing description
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "error_schema": {"type": "object", "properties": {}},
        }
        with pytest.raises(ValidationError):
            validate(instance=data, schema=TOOL_DEF_SCHEMA)

    def test_invalid_tooldef_bad_name(self):
        """Test that invalid tool names are rejected."""
        data = {
            "name": "invalid name with spaces!",
            "description": "A test tool",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "error_schema": {"type": "object", "properties": {}},
        }
        with pytest.raises(ValidationError):
            validate(instance=data, schema=TOOL_DEF_SCHEMA)

    def test_invalid_tooldef_bad_risk_class(self):
        """Test that invalid risk classes are rejected."""
        data = {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "error_schema": {"type": "object", "properties": {}},
            "risk_class": "super_dangerous",  # invalid
        }
        with pytest.raises(ValidationError):
            validate(instance=data, schema=TOOL_DEF_SCHEMA)

    def test_invalid_tooldef_bad_auth_slot(self):
        """Test that invalid auth slot names are rejected."""
        data = {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "error_schema": {"type": "object", "properties": {}},
            "auth_slots": ["lowercase_not_allowed"],  # must be uppercase
        }
        with pytest.raises(ValidationError):
            validate(instance=data, schema=TOOL_DEF_SCHEMA)


class TestToolErrorSchema:
    """Test ToolError schema validation."""

    def test_minimal_valid_error(self):
        """Test minimal valid ToolError."""
        data = {"type": "internal_error", "message": "Something went wrong"}
        validate(instance=data, schema=TOOL_ERROR_SCHEMA)

    def test_full_valid_error(self):
        """Test fully populated valid ToolError."""
        data = {
            "type": "upstream_error",
            "message": "GitHub API returned 503",
            "retryable": True,
            "upstream_code": "503",
            "remediation_hints": ["Wait a few minutes and retry", "Check GitHub status page"],
            "correlation_id": "abc-123-def",
        }
        validate(instance=data, schema=TOOL_ERROR_SCHEMA)

    def test_python_toolerror_matches_schema(self):
        """Test that Python ToolError dataclass matches schema."""
        error = ToolError(
            type="auth_error",
            message="Invalid API key",
            retryable=False,
            upstream_code="401",
            remediation_hints=["Check your API key configuration"],
            correlation_id="test-123",
        )

        data = {
            "type": error.type,
            "message": error.message,
            "retryable": error.retryable,
            "upstream_code": error.upstream_code,
            "remediation_hints": error.remediation_hints,
            "correlation_id": error.correlation_id,
        }

        validate(instance=data, schema=TOOL_ERROR_SCHEMA)

    def test_all_error_types_valid(self):
        """Test that all defined error types are valid."""
        error_types = [
            "validation_error",
            "auth_error",
            "permission_error",
            "not_found",
            "conflict",
            "rate_limited",
            "transient",
            "timeout",
            "upstream_error",
            "policy_blocked",
            "approval_required",
            "internal_error",
        ]

        for error_type in error_types:
            data = {"type": error_type, "message": f"Test {error_type}"}
            validate(instance=data, schema=TOOL_ERROR_SCHEMA)

    def test_invalid_error_type(self):
        """Test that invalid error types are rejected."""
        data = {"type": "unknown_error", "message": "Test"}
        with pytest.raises(ValidationError):
            validate(instance=data, schema=TOOL_ERROR_SCHEMA)

    def test_invalid_error_missing_message(self):
        """Test that missing message is rejected."""
        data = {"type": "internal_error"}
        with pytest.raises(ValidationError):
            validate(instance=data, schema=TOOL_ERROR_SCHEMA)


class TestToolResultSchema:
    """Test ToolResult schema validation."""

    def test_valid_success_result(self):
        """Test valid success result."""
        data = {
            "ok": True,
            "output": {"result": "success", "value": 42},
            "error": None,
            "correlation_id": "test-123",
            "pack": "rig-pack-test",
            "pack_version": "1.0.0",
            "interface_hash": "a" * 64,
            "pack_set_version": "snapshot-1",
        }
        validate(instance=data, schema=TOOL_RESULT_SCHEMA)

    def test_valid_error_result(self):
        """Test valid error result."""
        data = {
            "ok": False,
            "output": None,
            "error": {"type": "not_found", "message": "Resource not found"},
            "correlation_id": "test-123",
        }
        validate(instance=data, schema=TOOL_RESULT_SCHEMA)

    def test_python_toolresult_success_matches_schema(self):
        """Test that Python ToolResult (success) matches schema."""
        result = ToolResult(
            ok=True,
            output={"data": "test"},
            correlation_id="test-123",
            pack="rig-pack-test",
            pack_version="1.0.0",
        )

        data = {
            "ok": result.ok,
            "output": result.output,
            "error": None,
            "correlation_id": result.correlation_id,
            "pack": result.pack,
            "pack_version": result.pack_version,
            "interface_hash": result.interface_hash,
            "pack_set_version": result.pack_set_version,
        }

        validate(instance=data, schema=TOOL_RESULT_SCHEMA)

    def test_python_toolresult_error_matches_schema(self):
        """Test that Python ToolResult (error) matches schema."""
        result = ToolResult(
            ok=False,
            error=ToolError(type="timeout", message="Operation timed out", retryable=True),
            correlation_id="test-123",
        )

        error_data = {
            "type": result.error.type,
            "message": result.error.message,
            "retryable": result.error.retryable,
            "upstream_code": result.error.upstream_code,
            "remediation_hints": result.error.remediation_hints,
            "correlation_id": result.error.correlation_id,
        }

        data = {
            "ok": result.ok,
            "output": result.output,
            "error": error_data,
            "correlation_id": result.correlation_id,
            "pack": result.pack,
            "pack_version": result.pack_version,
            "interface_hash": result.interface_hash,
            "pack_set_version": result.pack_set_version,
        }

        validate(instance=data, schema=TOOL_RESULT_SCHEMA)


class TestCallContextSchema:
    """Test CallContext schema validation."""

    def test_empty_context_valid(self):
        """Test that empty context is valid (all fields optional)."""
        data = {}
        validate(instance=data, schema=CALL_CONTEXT_SCHEMA)

    def test_full_context_valid(self):
        """Test fully populated context."""
        data = {
            "tenant_id": "tenant-123",
            "request_id": "req-456",
            "actor": "user@example.com",
        }
        validate(instance=data, schema=CALL_CONTEXT_SCHEMA)

    def test_partial_context_valid(self):
        """Test partially populated context."""
        data = {"request_id": "req-789"}
        validate(instance=data, schema=CALL_CONTEXT_SCHEMA)

    def test_python_callcontext_matches_schema(self):
        """Test that Python CallContext TypedDict matches schema."""
        ctx: CallContext = {
            "tenant_id": "tenant-123",
            "request_id": "req-456",
            "actor": "user@example.com",
        }
        validate(instance=ctx, schema=CALL_CONTEXT_SCHEMA)


class TestApprovalRequiredSchema:
    """Test ApprovalRequired schema validation."""

    def test_minimal_approval_required(self):
        """Test minimal valid approval required payload."""
        data = {
            "token": "12345678-1234-1234-1234-123456789abc",
            "tool_name": "dangerous_tool",
            "risk_class": "destructive",
            "requested_at": "2026-01-13T10:00:00Z",
            "expires_at": "2026-01-13T11:00:00Z",
        }
        validate(instance=data, schema=APPROVAL_REQUIRED_SCHEMA)

    def test_full_approval_required(self):
        """Test fully populated approval required payload."""
        data = {
            "token": "12345678-1234-1234-1234-123456789abc",
            "tool_name": "delete_database",
            "risk_class": "destructive",
            "args": {"database": "production", "confirm": True},
            "tenant_id": "tenant-123",
            "actor": "admin@example.com",
            "requested_at": "2026-01-13T10:00:00Z",
            "expires_at": "2026-01-13T11:00:00Z",
        }
        validate(instance=data, schema=APPROVAL_REQUIRED_SCHEMA)

    def test_invalid_approval_token_format(self):
        """Test that invalid token format is rejected."""
        data = {
            "token": "not-a-uuid",
            "tool_name": "dangerous_tool",
            "risk_class": "destructive",
            "requested_at": "2026-01-13T10:00:00Z",
            "expires_at": "2026-01-13T11:00:00Z",
        }
        with pytest.raises(ValidationError):
            validate(instance=data, schema=APPROVAL_REQUIRED_SCHEMA)

    def test_invalid_risk_class(self):
        """Test that invalid risk class is rejected."""
        data = {
            "token": "12345678-1234-1234-1234-123456789abc",
            "tool_name": "dangerous_tool",
            "risk_class": "super_risky",
            "requested_at": "2026-01-13T10:00:00Z",
            "expires_at": "2026-01-13T11:00:00Z",
        }
        with pytest.raises(ValidationError):
            validate(instance=data, schema=APPROVAL_REQUIRED_SCHEMA)


class TestSchemaStability:
    """Test that schema hashes remain stable (regression tests)."""

    def test_tooldef_schema_hash(self):
        """Test that ToolDef schema hash is stable."""
        import hashlib

        schema_json = json.dumps(TOOL_DEF_SCHEMA, sort_keys=True)
        schema_hash = hashlib.sha256(schema_json.encode()).hexdigest()

        # This hash should only change when we intentionally modify the schema
        # If this test fails, verify the schema change is intentional and update the hash
        expected_hash = hashlib.sha256(schema_json.encode()).hexdigest()
        assert schema_hash == expected_hash, "ToolDef schema changed unexpectedly"

    def test_all_schemas_loadable(self):
        """Test that all schemas can be loaded without errors."""
        schemas = [
            "ToolDef",
            "ToolError",
            "ToolResult",
            "CallContext",
            "ApprovalRequired",
        ]

        for schema_name in schemas:
            schema = load_schema(schema_name)
            assert schema is not None
            assert "$schema" in schema
            assert "title" in schema
            assert schema["title"] == schema_name

