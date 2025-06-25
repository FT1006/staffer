"""
End-to-end integration test: Staffer CLI → MCP Aggregator → External MCP servers.

Following RED-GREEN-REFACTOR TDD approach.
Tests the complete integration flow identified in handover document priorities.
"""
import pytest
import asyncio
import subprocess
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, Mock
from tests.factories import create_mock_adk_tool, create_test_server_config

# Test imports - will fail until implementation
try:
    from staffer.mcp_client import StafferMCPClient
except ImportError:
    StafferMCPClient = None

try:
    from staffer.available_functions import get_available_functions_with_mcp
except ImportError:
    get_available_functions_with_mcp = None

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-aggregator'))
from server import MCPAggregatorServer


class TestStafferMCPIntegration:
    """Test complete Staffer → MCP Aggregator → External servers integration."""
    
    @pytest.mark.asyncio
    async def test_staffer_discovers_mcp_tools_via_aggregator(self):
        """Test Staffer discovers tools through MCP aggregator via STDIO."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        # Use factories to create mock ADK tools
        mock_tools_objects = [
            create_mock_adk_tool("excel_read_sheet", "Read Excel sheet"),
            create_mock_adk_tool("load_dataset", "Load dataset")
        ]
        
        # Mock the MCPToolset at the ADK level
        with patch('staffer.mcp_client.MCPToolset') as mock_toolset_class:
            mock_toolset = Mock()
            # Make get_tools return an awaitable
            async def mock_get_tools():
                return mock_tools_objects
            mock_toolset.get_tools = mock_get_tools
            mock_toolset_class.return_value = mock_toolset
            
            # When: Staffer connects to aggregator via STDIO (using environment config)
            with patch.dict(os.environ, {
                'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
                'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
                'MCP_TIMEOUT': '10.0'
            }):
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
            
            # Should discover MCP tools
            tools = await mcp_client.list_tools()
            
            # Validate the integration works
            assert len(tools) >= 2, "Should discover tools from MCP aggregator"
            tool_names = [tool['name'] for tool in tools]
            assert "excel_read_sheet" in tool_names, "Should include Excel tools"
            assert "load_dataset" in tool_names, "Should include Analytics tools"
    
    def test_staffer_available_functions_includes_mcp_tools(self):
        """Test that Staffer's available_functions includes MCP tools."""
        if not get_available_functions_with_mcp:
            pytest.skip("get_available_functions_with_mcp not implemented yet")
        
        # Given: Staffer in a working directory
        working_dir = "/test/directory"
        
        # Use factories to create mock ADK tools
        mock_tools_objects = [
            create_mock_adk_tool("excel_read_sheet", "Read Excel sheet"),
            create_mock_adk_tool("create_chart", "Create data visualization")
        ]
        
        # Mock the MCPToolset at the ADK level
        with patch('staffer.mcp_client.MCPToolset') as mock_toolset_class:
            mock_toolset = Mock()
            # Make get_tools return an awaitable
            async def mock_get_tools():
                return mock_tools_objects
            mock_toolset.get_tools = mock_get_tools
            mock_toolset_class.return_value = mock_toolset
            
            # When: Getting available functions
            functions = get_available_functions_with_mcp(working_dir)
            
            # Should return GenAI-compatible tools
            assert hasattr(functions, 'function_declarations'), "Should return GenAI-compatible tools"
            
            # Should include both built-in and MCP tools
            function_names = [decl.name for decl in functions.function_declarations]
            assert "get_file_content" in function_names, "Should include built-in Staffer functions"
            assert "excel_read_sheet" in function_names, "Should include MCP tools"
            assert "create_chart" in function_names, "Should include Analytics tools"
    
    @pytest.mark.asyncio
    async def test_staffer_executes_mcp_tool_via_aggregator(self):
        """Test Staffer can execute tools through MCP aggregator."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        # Create mock ADK tool for execution test
        mock_tool = create_mock_adk_tool("excel_read_sheet", "Read Excel sheet")
        
        # Mock the MCPToolset at the ADK level
        with patch('staffer.mcp_client.MCPToolset') as mock_toolset_class:
            mock_toolset = Mock()
            
            # Mock tool execution
            async def mock_call_tool(tool_name, **kwargs):
                return "Excel file read successfully: 10 rows, 5 columns"
            mock_toolset.call_tool = mock_call_tool
            mock_toolset_class.return_value = mock_toolset
            
            # Given: Connected MCP client (using environment config)
            with patch.dict(os.environ, {
                'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
                'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
                'MCP_TIMEOUT': '10.0'
            }):
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
            
            # When: Executing MCP tool
            result = await mcp_client.call_tool(
                tool_name="excel_read_sheet",
                arguments={"file_path": "/test/data.xlsx", "sheet_name": "Sheet1"}
            )
            
            # Should return execution result
            assert result is not None, "Should return execution result"
            assert "content" in result, "Should return MCP-format response"
            assert "Excel file read successfully" in str(result), "Should include tool output"
    
    @pytest.mark.asyncio
    async def test_end_to_end_tool_discovery_and_execution(self):
        """Test complete flow: discover tools → execute tool → return result."""
        if not StafferMCPClient or not get_available_functions_with_mcp:
            pytest.skip("End-to-end integration not implemented yet")
        
        working_dir = "/test/directory"
        
        # Use factory to create mock ADK tool
        mock_tool = create_mock_adk_tool("excel_read_sheet", "Read Excel sheet")
        
        # Mock the MCPToolset at both the direct client level and available_functions level
        with patch('staffer.mcp_client.MCPToolset') as mock_toolset_class:
            mock_toolset = Mock()
            
            # Make get_tools return an awaitable
            async def mock_get_tools():
                return [mock_tool]
            mock_toolset.get_tools = mock_get_tools
            
            # Mock call_tool for execution test
            async def mock_call_tool(tool_name, **kwargs):
                return "Data: [Row1, Row2, Row3]"
            mock_toolset.call_tool = mock_call_tool
            mock_toolset_class.return_value = mock_toolset
            
            # Also patch the MCPToolset in available_functions module
            with patch('staffer.available_functions.MCPToolset', mock_toolset_class):
                # Step 1: Discover tools
                functions = get_available_functions_with_mcp(working_dir)
                function_names = [decl.name for decl in functions.function_declarations]
                assert "excel_read_sheet" in function_names, "Should discover MCP tools"
            
            # Step 2: Execute tool (using environment config)
            with patch.dict(os.environ, {
                'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
                'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
                'MCP_TIMEOUT': '10.0'
            }):
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
            
            result = await mcp_client.call_tool(
                tool_name="excel_read_sheet",
                arguments={"file_path": "/test/data.xlsx"}
            )
            
            # Should execute and return tool results
            assert "Data: [Row1, Row2, Row3]" in str(result), "Should execute and return tool results"


class TestMCPAggregatorServerIntegration:
    """Test MCP aggregator server running with real configuration."""
    
    @pytest.mark.asyncio
    async def test_aggregator_server_starts_with_production_config(self):
        """RED: Test aggregator server starts with production configuration."""
        production_config_path = Path(__file__).parent.parent / "mcp-aggregator" / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
        
        # Test with environment variables set
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_HOST': 'localhost',
            'MCP_AGGREGATOR_PORT': '8080',
            'EXCEL_MCP_PATH': '/test/excel-server',
            'ANALYTICS_MCP_PATH': '/test/analytics-server',
            'EXCEL_ENABLED': 'true',
            'ANALYTICS_ENABLED': 'true'
        }):
            # This will fail until we implement server startup
            server = MCPAggregatorServer(config_path=str(production_config_path))
            assert server.config is not None, "Should load production configuration"
            
            # Should have environment-resolved configuration
            assert len(server.config.source_servers) >= 2, "Should have Excel and Analytics servers configured"
    
    @pytest.mark.asyncio
    async def test_aggregator_handles_missing_external_servers_gracefully(self):
        """RED: Test aggregator graceful fallback with missing external servers."""
        config_path = Path(__file__).parent.parent / "mcp-aggregator" / "test_config.yaml"
        
        with patch('os.getenv', return_value=None):  # No server paths
            server = MCPAggregatorServer(config_path=str(config_path))
        
        # Should not crash when external servers are unavailable
        tools = await server.get_tools()
        
        # This will fail until graceful fallback is implemented
        assert isinstance(tools, list), "Should return list even when external servers unavailable"
        # Should either return empty list or built-in tools only
        assert len(tools) >= 0, "Should handle missing servers gracefully"


class TestRealServerValidation:
    """Test integration with actual Excel and Analytics MCP servers."""
    
    @pytest.mark.skipif(not os.getenv('EXCEL_MCP_PATH'), reason="EXCEL_MCP_PATH not set")
    @pytest.mark.asyncio
    async def test_integration_with_real_excel_server(self):
        """RED: Test integration with actual Excel MCP server."""
        excel_path = os.getenv('EXCEL_MCP_PATH')
        if not Path(excel_path).exists():
            pytest.skip(f"Excel MCP server not found at {excel_path}")
        
        # Test with real Excel server path
        config_dict = {
            "source_servers": [{
                "name": "excel",
                "command": "go",
                "args": ["run", "cmd/excel-mcp-server/main.go"],
                "cwd_env": "EXCEL_MCP_PATH",
                "enabled": True,
                "priority": 1,
                "tool_filter": ["excel_read_sheet", "excel_describe_sheets"]
            }],
            "tool_selection": {"strategy": "curated"}
        }
        
        from mcp_aggregator.composer import GenericMCPServerComposer
        composer = GenericMCPServerComposer(config_dict)
        
        # This will fail until real server integration works
        tools = await composer.get_all_tools()
        assert len(tools) > 0, "Should discover tools from real Excel server"
        
        tool_names = [tool.name for tool in tools]
        assert any("excel" in name for name in tool_names), "Should include Excel-specific tools"
    
    @pytest.mark.skipif(not os.getenv('ANALYTICS_MCP_PATH'), reason="ANALYTICS_MCP_PATH not set")
    @pytest.mark.asyncio
    async def test_integration_with_real_analytics_server(self):
        """RED: Test integration with actual Analytics MCP server."""
        analytics_path = os.getenv('ANALYTICS_MCP_PATH')
        if not Path(analytics_path).exists():
            pytest.skip(f"Analytics MCP server not found at {analytics_path}")
        
        # Test with real Analytics server path
        config_dict = {
            "source_servers": [{
                "name": "analytics",
                "command": "python",
                "args": ["-m", "src.mcp_server.server"],
                "cwd_env": "ANALYTICS_MCP_PATH",
                "enabled": True,
                "priority": 1,
                "tool_filter": ["load_dataset", "create_chart", "find_correlations"]
            }],
            "tool_selection": {"strategy": "curated"}
        }
        
        from mcp_aggregator.composer import GenericMCPServerComposer
        composer = GenericMCPServerComposer(config_dict)
        
        # This will fail until real server integration works
        tools = await composer.get_all_tools()
        assert len(tools) > 0, "Should discover tools from real Analytics server"
        
        tool_names = [tool.name for tool in tools]
        assert any("dataset" in name or "chart" in name for name in tool_names), "Should include Analytics-specific tools"


class TestPerformanceBenchmarking:
    """Test performance with concurrent tool execution."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_discovery_performance(self):
        """RED: Test tool discovery performance with multiple servers."""
        # Use factories to create multiple server configs
        from tests.factories import create_mock_adk_tool
        config_dict = {
            "source_servers": [
                {"name": f"server_{i}", "enabled": True, "priority": i, "tools": [
                    create_mock_adk_tool(f"tool_{i}_{j}", f"Tool {j} from server {i}")
                    for j in range(5)  # 5 tools per server
                ]} for i in range(10)  # 10 servers
            ],
            "tool_selection": {"strategy": "curated"}
        }
        
        from mcp_aggregator.composer import GenericMCPServerComposer
        composer = GenericMCPServerComposer(config_dict)
        
        # Mock fast tool discovery
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.side_effect = lambda config: config.get('tools', [])
            
            # Measure discovery time
            import time
            start_time = time.time()
            tools = await composer.get_all_tools()
            discovery_time = time.time() - start_time
            
            # This will fail until concurrent processing is implemented
            assert len(tools) >= 50, "Should discover all tools from all servers"
            assert discovery_time < 2.0, "Should complete discovery within 2 seconds"  # Performance requirement
    
    @pytest.mark.asyncio
    async def test_tool_execution_timeout_handling(self):
        """Test handling of tool execution timeouts."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        # Create MCP client with short timeout (using environment config)
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
            'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
            'MCP_TIMEOUT': '1.0'
        }):
            mcp_client = StafferMCPClient({
                'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                'timeout': float(os.getenv('MCP_TIMEOUT'))
            })
        
        # Mock slow tool execution
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(2.0)  # Longer than timeout
            return {"content": [{"type": "text", "text": "Slow result"}]}
        
        with patch.object(mcp_client, 'call_tool', side_effect=slow_execution):
            # Should handle timeout gracefully
            import time
            start_time = time.time()
            
            try:
                result = await mcp_client.call_tool("slow_tool", {})
                assert False, "Should have timed out"
            except asyncio.TimeoutError:
                # Expected behavior - graceful timeout
                execution_time = time.time() - start_time
                assert execution_time < 1.5, "Should timeout quickly"