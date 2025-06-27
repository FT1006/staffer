"""RED tests for executing tools via real MCP servers - following TDD approach."""
import pytest
import os
import asyncio
from pathlib import Path
from unittest.mock import patch

from config import normalize_config_dict
from composer import GenericMCPServerComposer


class TestRealMCPExecution:
    """Test tool execution via real installed MCP servers."""
    
    @pytest.mark.asyncio
    async def test_excel_mcp_server_tool_execution(self):
        """RED: Test executing Excel tool via real Excel MCP server."""
        # Given: Config pointing to real Excel MCP server
        excel_server_path = str(Path(__file__).parent.parent.parent / "excel-mcp-server")
        
        config = {
            'domain': 'test',
            'model': 'test',
            'source_servers': [
                {
                    'name': 'excel',
                    'command': './excel-mcp-server',
                    'args': [],
                    'cwd_env': 'EXCEL_MCP_PATH',
                    'enabled': True,
                    'priority': 1,
                    'tool_filter': ['excel_describe_sheets']  # Use a simple tool
                }
            ]
        }
        
        # Set up environment to point to Excel MCP server
        with patch.dict(os.environ, {'EXCEL_MCP_PATH': excel_server_path}):
            composer = GenericMCPServerComposer(config)
            
            # When: Execute excel_describe_sheets tool with a test file  
            test_xlsx_path = str(Path(__file__).parent.parent.parent / "data/department_satisfaction.xlsx")
            arguments = {
                'fileAbsolutePath': test_xlsx_path  # Excel server expects this parameter name
            }
            
            try:
                # This should execute successfully with real Excel MCP server
                result = await composer.call_tool('excel_describe_sheets', arguments)
                
                # Then: Should get a valid response from Excel server
                assert result is not None
                print(f"Excel MCP tool result: {result}")
                
                # Check if it's a CallToolResult object or plain result
                if hasattr(result, 'content'):
                    # CallToolResult object - check for successful execution
                    assert not result.isError, f"Tool execution failed: {result.content}"
                    assert len(result.content) > 0, "Should have content in result"
                else:
                    # Plain result
                    assert isinstance(result, (str, dict))
                
            except ValueError as e:
                # If tool not found, that's also valuable info about what tools are available
                if "not found" in str(e):
                    # Let's see what tools are actually available
                    tools = await composer.get_all_tools()
                    tool_names = [tool.name for tool in tools]
                    pytest.fail(f"excel_describe_sheets not found. Available tools: {tool_names}")
                else:
                    raise
    
    @pytest.mark.asyncio
    async def test_quick_data_mcp_server_tool_execution(self):
        """RED: Test executing Quick Data tool via real Quick Data MCP server."""
        # Given: Config pointing to real Quick Data MCP server
        quick_data_path = str(Path(__file__).parent.parent.parent / "quick-data-mcp-main/quick-data-mcp")
        
        config = {
            'domain': 'test',
            'model': 'test', 
            'source_servers': [
                {
                    'name': 'analytics',
                    'command': 'python3',
                    'args': ['main.py'],  # Run main.py directly instead of as module
                    'cwd_env': 'ANALYTICS_MCP_PATH',
                    'enabled': True,
                    'priority': 1,
                    'tool_filter': ['load_dataset']
                }
            ]
        }
        
        # Set up environment to point to Quick Data MCP server
        with patch.dict(os.environ, {'ANALYTICS_MCP_PATH': quick_data_path}):
            composer = GenericMCPServerComposer(config)
            
            # When: Execute load_dataset tool
            test_csv_path = "data/employee_survey.csv"  # Relative to quick-data-mcp directory
            arguments = {
                'dataset_name': 'employee_survey',  # Name for the dataset
                'file_path': test_csv_path  # Path to the CSV file
            }
            
            try:
                # This should execute successfully with real Quick Data MCP server
                result = await composer.call_tool('load_dataset', arguments)
                
                # Then: Should get a valid response from Quick Data server
                assert result is not None
                print(f"Quick Data MCP tool result: {result}")
                
                # Check if it's a CallToolResult object or plain result
                if hasattr(result, 'content'):
                    # CallToolResult object - check for successful execution
                    assert not result.isError, f"Tool execution failed: {result.content}"
                    assert len(result.content) > 0, "Should have content in result"
                else:
                    # Plain result
                    assert isinstance(result, (str, dict))
                
            except ValueError as e:
                # If tool not found, that's also valuable info about what tools are available
                if "not found" in str(e):
                    # Let's see what tools are actually available
                    tools = await composer.get_all_tools()
                    tool_names = [tool.name for tool in tools]
                    pytest.fail(f"load_dataset not found. Available tools: {tool_names}")
                else:
                    raise


class TestServerEnableDisable:
    """Test server enable/disable functionality."""
    
    @pytest.mark.asyncio
    async def test_disabled_server_not_discovered(self):
        """RED: Test that disabled servers are not included in tool discovery."""
        # Given: Two servers, one enabled and one disabled
        excel_path = str(Path(__file__).parent.parent.parent / "excel-mcp-server")
        quick_data_path = str(Path(__file__).parent.parent.parent / "quick-data-mcp-main/quick-data-mcp")
        
        config = {
            'domain': 'test',
            'model': 'test',
            'source_servers': [
                {
                    'name': 'excel_enabled',
                    'command': './excel-mcp-server',
                    'args': [],
                    'cwd_env': 'EXCEL_MCP_PATH',
                    'enabled': True,  # Enabled
                    'priority': 1
                },
                {
                    'name': 'analytics_disabled',
                    'command': 'python3',
                    'args': ['main.py'],
                    'cwd_env': 'ANALYTICS_MCP_PATH', 
                    'enabled': False,  # Disabled
                    'priority': 2
                }
            ]
        }
        
        # Set up environment for both servers
        with patch.dict(os.environ, {
            'EXCEL_MCP_PATH': excel_path,
            'ANALYTICS_MCP_PATH': quick_data_path
        }):
            composer = GenericMCPServerComposer(config)
            
            # When: Get all tools
            tools = await composer.get_all_tools()
            
            # Then: Only tools from enabled server should be present
            tool_names = [tool.name for tool in tools]
            
            # Should have Excel tools (from enabled server)
            has_excel_tools = any('excel' in name.lower() for name in tool_names)
            
            # Should NOT have analytics tools (from disabled server)
            has_analytics_tools = any(name in ['load_dataset', 'find_correlations'] for name in tool_names)
            
            assert has_excel_tools, f"Expected Excel tools from enabled server. Got: {tool_names}"
            assert not has_analytics_tools, f"Should not have analytics tools from disabled server. Got: {tool_names}"
    
    @pytest.mark.asyncio
    async def test_server_missing_environment_not_available(self):
        """RED: Test that servers with missing environment variables are not available."""
        # Given: Server config with missing environment variable
        config = {
            'domain': 'test',
            'model': 'test',
            'source_servers': [
                {
                    'name': 'missing_env_server',
                    'command': 'python3',
                    'args': ['-m', 'server'],
                    'cwd_env': 'NONEXISTENT_ENV_VAR',  # This env var doesn't exist
                    'enabled': True,
                    'priority': 1
                }
            ]
        }
        
        # Don't set the environment variable (simulating missing config)
        composer = GenericMCPServerComposer(config)
        
        # When: Get all tools
        tools = await composer.get_all_tools()
        
        # Then: Should get empty list since server is not available
        assert len(tools) == 0, f"Expected no tools from unavailable server. Got: {tools}"
        
        # Verify that the server config is recognized as not available
        normalized_config = composer.config
        server = normalized_config.source_servers[0]
        assert not server.is_available, "Server should not be available without environment variable"