"""
RGP Conformance Tests

Tests that the RGP server implementation conforms to the OpenAPI specification.
"""

import pytest
from fastapi.testclient import TestClient

from rig_core.audit import AuditLog
from rig_core.policy import Policy
from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime, RegisteredTool
from rig_core.rtp import ToolDef
from rig_core.secrets import SecretsStore
from rig_protocol_rgp.server import create_app


@pytest.fixture
def test_tool():
    """Create a test tool definition."""
    return ToolDef(
        name="test_echo",
        description="Echo back the input message",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        output_schema={
            "type": "object",
            "properties": {"echo": {"type": "string"}},
        },
        error_schema={"type": "object", "properties": {}},
        risk_class="read",
        tags=["test"],
    )


@pytest.fixture
def risky_tool():
    """Create a risky tool that requires approval."""
    return ToolDef(
        name="delete_database",
        description="Delete a database (destructive operation)",
        input_schema={
            "type": "object",
            "properties": {"database": {"type": "string"}},
            "required": ["database"],
        },
        output_schema={
            "type": "object",
            "properties": {"deleted": {"type": "boolean"}},
        },
        error_schema={"type": "object", "properties": {}},
        risk_class="destructive",
        tags=["database", "dangerous"],
    )


@pytest.fixture
def client(test_tool, risky_tool, tmp_path):
    """Create a test client with a registry and runtime."""
    registry = ToolRegistry()
    
    # Register test tool
    def echo_impl(args, secrets, ctx):
        return {"echo": args["message"]}
    
    registry.register_tools([test_tool, risky_tool])
    
    # Create runtime
    audit = AuditLog(str(tmp_path / "test_audit.db"))
    policy = Policy()
    secrets = SecretsStore()
    runtime = RigRuntime(policy=policy, secrets=secrets, audit=audit)
    
    # Register implementations
    runtime.register("test_echo", RegisteredTool(tool=test_tool, impl=echo_impl))
    runtime.register("delete_database", RegisteredTool(tool=risky_tool, impl=lambda a, s, c: {"deleted": True}))
    
    # Create app
    app = create_app(registry, runtime)
    return TestClient(app)


class TestHealthEndpoint:
    """Test /v1/health endpoint conformance."""

    def test_health_returns_ok(self, client):
        """Test that health endpoint returns status ok."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestToolsEndpoint:
    """Test /v1/tools endpoints conformance."""

    def test_list_tools_returns_array(self, client):
        """Test that list tools returns an array."""
        response = client.get("/v1/tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # test_echo and delete_database

    def test_list_tools_includes_required_fields(self, client):
        """Test that each tool has required fields."""
        response = client.get("/v1/tools")
        data = response.json()
        
        for tool in data:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "output_schema" in tool
            assert "error_schema" in tool
            assert "risk_class" in tool

    def test_get_tool_by_name(self, client):
        """Test getting a specific tool by name."""
        response = client.get("/v1/tools/test_echo")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_echo"
        assert data["description"] == "Echo back the input message"
        assert data["risk_class"] == "read"

    def test_get_nonexistent_tool_returns_404(self, client):
        """Test that getting a nonexistent tool returns 404."""
        response = client.get("/v1/tools/nonexistent")
        assert response.status_code == 404


class TestToolCallEndpoint:
    """Test /v1/tools/{name}:call endpoint conformance."""

    def test_call_tool_success(self, client):
        """Test successful tool call."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={"args": {"message": "hello"}},
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "ok" in data
        assert data["ok"] is True
        assert "output" in data
        assert data["output"]["echo"] == "hello"
        assert "correlation_id" in data

    def test_call_tool_with_context(self, client):
        """Test tool call with context headers."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={
                "args": {"message": "hello"},
                "context": {
                    "tenant_id": "tenant-123",
                    "request_id": "req-456",
                    "actor": "user@example.com",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_call_tool_validation_error(self, client):
        """Test tool call with invalid arguments."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={"args": {}},  # missing required 'message' field
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["ok"] is False
        assert "error" in data
        assert data["error"]["type"] == "validation_error"

    def test_call_nonexistent_tool_returns_error(self, client):
        """Test calling a nonexistent tool returns not_found error."""
        response = client.post(
            "/v1/tools/nonexistent:call",
            json={"args": {}},
        )
        # RGP returns 200 with error payload for tool execution errors
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error"]["type"] == "not_found"

    def test_call_risky_tool_requires_approval(self, client):
        """Test that risky tools require approval."""
        response = client.post(
            "/v1/tools/delete_database:call",
            json={"args": {"database": "production"}},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["ok"] is False
        assert "error" in data
        assert data["error"]["type"] == "approval_required"
        assert "remediation_hints" in data["error"]
        assert len(data["error"]["remediation_hints"]) > 0


class TestApprovalsEndpoint:
    """Test /v1/approvals endpoints conformance."""

    def test_approve_tool_call(self, client):
        """Test approving a risky tool call."""
        # First, trigger approval requirement
        response = client.post(
            "/v1/tools/delete_database:call",
            json={"args": {"database": "test"}},
        )
        data = response.json()
        assert data["error"]["type"] == "approval_required"

        # Extract token from remediation hints
        hints = data["error"]["remediation_hints"]
        token = None
        for hint in hints:
            if "approve token:" in hint:
                token = hint.split("approve token:")[1].strip()
                break

        assert token is not None

        # Approve the call
        response = client.post(f"/v1/approvals/{token}:approve")
        assert response.status_code == 200
        data = response.json()

        # Should now execute successfully
        assert data["ok"] is True
        assert "output" in data

    def test_approve_invalid_token_returns_error(self, client):
        """Test approving with invalid token returns not_found error."""
        response = client.post("/v1/approvals/invalid-token:approve")
        # RGP returns 200 with error payload
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error"]["type"] == "not_found"


class TestHeaderPropagation:
    """Test that RGP headers are properly propagated."""

    def test_correlation_id_in_response(self, client):
        """Test that correlation_id is included in response."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={
                "args": {"message": "test"},
                "context": {"request_id": "test-correlation-123"},
            },
        )
        data = response.json()
        assert "correlation_id" in data
        assert data["correlation_id"] == "test-correlation-123"

    def test_auto_generated_correlation_id(self, client):
        """Test that correlation_id is auto-generated if not provided."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={"args": {"message": "test"}},
        )
        data = response.json()
        assert "correlation_id" in data
        assert data["correlation_id"] is not None


class TestErrorResponseFormat:
    """Test that error responses conform to the spec."""

    def test_error_has_required_fields(self, client):
        """Test that errors have type and message."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={"args": {}},  # validation error
        )
        data = response.json()

        assert data["ok"] is False
        error = data["error"]
        assert "type" in error
        assert "message" in error
        assert error["type"] in [
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

    def test_error_includes_retryable_flag(self, client):
        """Test that errors include retryable flag."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={"args": {}},
        )
        data = response.json()
        error = data["error"]
        assert "retryable" in error
        assert isinstance(error["retryable"], bool)


class TestResultMetadata:
    """Test that results include proper metadata."""

    def test_result_includes_pack_metadata(self, client):
        """Test that results include pack and version info."""
        response = client.post(
            "/v1/tools/test_echo:call",
            json={"args": {"message": "test"}},
        )
        data = response.json()

        # These fields should be present (may be null in test environment)
        assert "pack" in data
        assert "pack_version" in data
        assert "interface_hash" in data
        assert "pack_set_version" in data

