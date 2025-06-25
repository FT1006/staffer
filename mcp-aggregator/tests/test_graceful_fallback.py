"""
Test graceful fallback when ADK MCP servers are unavailable.

Following RED-GREEN-REFACTOR TDD approach.
Uses factories for consistent test setup.
"""
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import os
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.factories import create_mock_adk_tool, create_mock_mcp_tool
from config import load_config
from server import MCPAggregatorServer
from composer import GenericMCPServerComposer


class TestGracefulServerFallback:
    """Test graceful fallback when MCP servers are unavailable."""
    
    @pytest.mark.asyncio
    async def test_server_continues_when_one_mcp_server_fails(self):
        """RED: Test that aggregator continues when one MCP server fails."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
            
        # Mock composer to simulate one server failing
        with patch.object(server.composer, '_discover_tools_from_server') as mock_discover:
            def mock_discover_with_failure(server_config):
                if server_config.get('name') == 'mock_excel':
                    # Excel server succeeds - return proper ADK tool
                    return [create_mock_adk_tool("excel_read", description="Excel tool")]
                else:
                    # Analytics server fails
                    raise ConnectionError("Analytics server unavailable")
            
            mock_discover.side_effect = mock_discover_with_failure
            
            # Should continue operating with available servers
            tools = await server.get_tools()
            
            # This will fail until we implement graceful fallback
            assert len(tools) >= 1, "Should return tools from working servers even when others fail"
            
            # Should have Excel tools but not Analytics tools
            tool_names = [tool.name for tool in tools]
            assert "excel_read" in tool_names, "Should include tools from working servers"
    
    @pytest.mark.asyncio
    async def test_server_returns_empty_list_when_all_servers_fail(self):
        """RED: Test graceful handling when all MCP servers fail."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
            
        # Mock all servers to fail
        with patch.object(server.composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.side_effect = ConnectionError("All servers unavailable")
            
            # Should not crash, should return empty list
            tools = await server.get_tools()
            assert isinstance(tools, list), "Should return list even when all servers fail"
            assert len(tools) == 0, "Should return empty list when no servers available"
    
    def test_server_logs_server_failures_appropriately(self):
        """Test that server logs failures but continues operating."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
            
        # Server delegates failure tracking to composer
        assert hasattr(server.composer, 'failed_servers'), "Composer should track failed servers"
        assert isinstance(server.composer.failed_servers, list), "Failed servers should be a list"
    
    @pytest.mark.asyncio
    async def test_composer_handles_individual_server_failures(self):
        """RED: Test that composer gracefully handles individual server failures."""
        config_dict = {
            "source_servers": [
                {"name": "working_server", "enabled": True, "priority": 1},
                {"name": "failing_server", "enabled": True, "priority": 2}
            ],
            "tool_selection": {"strategy": "curated"}
        }
        
        composer = GenericMCPServerComposer(config_dict)
        
        # Mock discovery to have one server fail
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            def mock_discover_mixed(server_config):
                if server_config.get('name') == 'working_server':
                    return [create_mock_adk_tool("working_tool", description="Working tool")]
                else:
                    raise ConnectionError("Server unavailable")
                    
            mock_discover.side_effect = mock_discover_mixed
            
            # This will fail until we implement graceful handling in composer
            tools = await composer.get_all_tools()
            
            assert len(tools) >= 1, "Should return tools from working servers"
            tool_names = [tool.name for tool in tools]
            assert "working_tool" in tool_names, "Should include tools from working servers"
    
    def test_config_validation_allows_missing_servers(self):
        """RED: Test that config validation is graceful about missing servers."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        # Test with some environment variables missing
        with patch.dict(os.environ, {"PWD": "/test/path"}, clear=True):
            # Some servers won't be available, but config should still load
            config = load_config(str(config_path))
            
            # Should load successfully even if not all servers are available
            assert config is not None, "Config should load even when some servers unavailable"
            
            # Available servers should be a subset of all servers
            available_count = len(config.available_servers)
            total_count = len(config.source_servers)
            assert available_count <= total_count, "Available servers should be subset of total"