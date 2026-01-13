"""Test RIG adapters - OpenAI and MCP."""

import json
import tempfile
import os

import pytest

from rig_core.adapters import openai_tools, openai_tools_schema_only, OpenAIToolHandler
from rig_core.audit import AuditLog
from rig_core.policy import Policy
from rig_core.registry import ToolRegistry
from rig_core.runtime import RegisteredTool, RigRuntime
from rig_core.rtp import ToolDef
from rig_core.secrets import SecretsStore


class TestOpenAIAdapter:
    """Test OpenAI tools adapter."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def registry(self):
        """Create a test registry with sample tools."""
        registry = ToolRegistry()
        
        # Add test tools
        tools = [
            ToolDef(
                name="test.greet",
                description="Greet a person by name",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Person's name"},
                    },
                    "required": ["name"],
                },
                output_schema={"type": "object", "properties": {"message": {"type": "string"}}},
                error_schema={"type": "object"},
                risk_class="read",
            ),
            ToolDef(
                name="test.calculate",
                description="Calculate sum of two numbers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
                output_schema={"type": "object", "properties": {"result": {"type": "number"}}},
                error_schema={"type": "object"},
                risk_class="read",
            ),
        ]
        
        registry.register_tools(tools)
        return registry

    @pytest.fixture
    def runtime(self, temp_db, registry):
        """Create a runtime with test tools registered."""
        audit = AuditLog(temp_db)
        policy = Policy(allowed_tools=None, require_approval_for=set(), timeout_seconds=30, retries=2)
        secrets = SecretsStore()
        runtime = RigRuntime(policy=policy, secrets=secrets, audit=audit)
        
        # Register implementations
        def greet_impl(args, secrets, ctx):
            return {"message": f"Hello, {args['name']}!"}
        
        def calc_impl(args, secrets, ctx):
            return {"result": args["a"] + args["b"]}
        
        for tool_def in registry.list_tools():
            if tool_def.name == "test.greet":
                reg = RegisteredTool(tool=tool_def, impl=greet_impl, pack="test", pack_version="1.0.0")
            else:
                reg = RegisteredTool(tool=tool_def, impl=calc_impl, pack="test", pack_version="1.0.0")
            runtime.register(tool_def.name, reg)
        
        runtime.set_snapshot_meta("test-hash", "test-version")
        return runtime

    def test_openai_tools_returns_list(self, registry, runtime):
        """Test that openai_tools returns a list of tool definitions."""
        tools = openai_tools(registry, runtime)
        
        assert isinstance(tools, list)
        assert len(tools) == 2

    def test_openai_tool_structure(self, registry, runtime):
        """Test that each tool has correct OpenAI structure."""
        tools = openai_tools(registry, runtime)
        
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "handler" in tool
            assert isinstance(tool["parameters"], dict)
            assert callable(tool["handler"])

    def test_openai_tool_handler_execution(self, registry, runtime):
        """Test that tool handlers execute correctly."""
        tools = openai_tools(registry, runtime)
        
        # Find the greet tool
        greet_tool = next(t for t in tools if t["name"] == "test.greet")
        handler = greet_tool["handler"]
        
        # Execute the handler
        result = handler(arguments={"name": "Alice"}, tenant_id="test-tenant", run_id="test-run")
        
        # Parse result
        result_data = json.loads(result)
        assert result_data["message"] == "Hello, Alice!"

    def test_openai_tool_filter(self, registry, runtime):
        """Test tool filtering."""
        tools = openai_tools(registry, runtime, tool_filter=["test.greet"])
        
        assert len(tools) == 1
        assert tools[0]["name"] == "test.greet"

    def test_openai_tools_schema_only(self, registry):
        """Test schema-only output for OpenAI API."""
        schemas = openai_tools_schema_only(registry)
        
        assert len(schemas) == 2
        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
            # Should NOT have handler
            assert "handler" not in schema

    def test_handler_error_response(self, registry, runtime):
        """Test handler returns proper error for policy-blocked tools."""
        # Block all tools
        runtime.policy = Policy(allowed_tools=set(), require_approval_for=set(), timeout_seconds=30, retries=2)
        
        tools = openai_tools(registry, runtime)
        greet_tool = next(t for t in tools if t["name"] == "test.greet")
        handler = greet_tool["handler"]
        
        result = handler(arguments={"name": "Alice"}, tenant_id="test", run_id="test-run")
        result_data = json.loads(result)
        
        assert result_data["error"] is True
        assert result_data["type"] == "policy_blocked"

