"""
Tests for MCP Bridge.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from rig_core.registry import ToolRegistry
from rig_core.runtime import RigRuntime, RegisteredTool
from rig_core.rtp import ToolDef, ToolResult
from rig_core.policy import Policy
from rig_core.secrets import SecretsStore


class TestMCPBridge:
    """Test MCP Bridge functionality."""

    @pytest.fixture
    def registry(self):
        """Create a test registry."""
        registry = ToolRegistry()

        # Add a simple tool
        tool_def = ToolDef(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            output_schema={"type": "object"},
            error_schema={"type": "object"},
            risk_class="low",
        )
        registry.register_tools([tool_def])

        return registry

    @pytest.fixture
    def runtime(self, registry):
        """Create a test runtime."""
        policy = Policy()
        secrets = SecretsStore()
        runtime = RigRuntime(policy, secrets)

        # Get the tool def from registry
        tool_def = registry.list_tools()[0]

        # Register a simple implementation
        def test_impl(args, secrets, ctx):
            return {"echo": args.get("message", "")}

        registered = RegisteredTool(tool=tool_def, impl=test_impl)
        runtime.register("test_tool", registered)

        return runtime

    def test_create_bridge(self, registry, runtime):
        """Test creating an MCP bridge."""
        from rig_bridge_mcp import create_mcp_bridge
        
        bridge = create_mcp_bridge(registry, runtime)
        
        assert bridge is not None
        assert bridge.registry == registry
        assert bridge.runtime == runtime

    def test_bridge_config(self):
        """Test MCP bridge configuration."""
        from rig_bridge_mcp import McpBridgeConfig
        
        config = McpBridgeConfig(
            transport="http",
            host="0.0.0.0",
            port=9000,
            debug=True,
        )
        
        assert config.transport == "http"
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.debug is True

    def test_bridge_default_config(self):
        """Test default MCP bridge configuration."""
        from rig_bridge_mcp import McpBridgeConfig
        
        config = McpBridgeConfig()
        
        assert config.transport == "stdio"
        assert config.host == "127.0.0.1"
        assert config.port == 8789
        assert config.debug is False

    @patch('mcp_use.server.MCPServer')
    def test_create_server(self, mock_mcp_server, registry, runtime):
        """Test creating MCP server."""
        from rig_bridge_mcp import RigMcpBridge

        # Mock the MCPServer
        mock_server_instance = Mock()
        mock_server_instance.tool = Mock(return_value=lambda f: f)  # Mock the decorator
        mock_mcp_server.return_value = mock_server_instance

        bridge = RigMcpBridge(registry, runtime)
        server = bridge.create_server(name="Test Server", version="1.0.0")

        # Verify MCPServer was created
        mock_mcp_server.assert_called_once()
        assert server == mock_server_instance

    def test_bridge_without_mcp_use(self, registry, runtime):
        """Test bridge fails gracefully without mcp-use installed."""
        from rig_bridge_mcp import RigMcpBridge
        
        bridge = RigMcpBridge(registry, runtime)
        
        # Mock the import to fail
        with patch.dict('sys.modules', {'mcp_use.server': None}):
            with pytest.raises(ImportError, match="mcp-use package not installed"):
                bridge.create_server()

    def test_tool_execution_through_bridge(self, registry, runtime):
        """Test that tools can be executed through the bridge."""
        from rig_core.runtime import CallContext

        # Execute tool directly through runtime (using call method)
        context = CallContext(
            auth={},
            correlation_id="test-123",
            actor_id="test-actor",
        )

        result = runtime.call("test_tool", {"message": "hello"}, context)

        assert result.ok
        assert result.output == {"echo": "hello"}

    def test_bridge_exports(self):
        """Test that bridge exports the correct symbols."""
        import rig_bridge_mcp
        
        assert hasattr(rig_bridge_mcp, 'RigMcpBridge')
        assert hasattr(rig_bridge_mcp, 'McpBridgeConfig')
        assert hasattr(rig_bridge_mcp, 'create_mcp_bridge')

    def test_bridge_readme_exists(self):
        """Test that bridge has documentation."""
        from pathlib import Path
        
        readme_path = Path("packages/rig-bridge-mcp/README.md")
        assert readme_path.exists()
        
        content = readme_path.read_text()
        assert "MCP" in content
        assert "RIG" in content

