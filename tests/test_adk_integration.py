"""Tests for Google ADK integration."""
import pytest
import asyncio
from google.adk import Agent
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters


@pytest.mark.asyncio
async def test_adk_mcp_toolset_with_excel_server():
    """Test that ADK MCPToolset works with our excel-mcp-server."""
    # Use the server path discovered in feature/mcp-support branch  
    # Need to run from the excel-mcp-server directory for go.mod
    server_params = StdioServerParameters(
        command="go",
        args=["run", "cmd/excel-mcp-server/main.go"],
        cwd="/Users/spaceship/project/staffer/excel-mcp-server"
    )
    
    connection_params = StdioConnectionParams(
        server_params=server_params
    )
    
    # Test with tool_filter (the key feature we want to validate)
    excel_toolset = MCPToolset(
        connection_params=connection_params,
        tool_filter=["excel_read_sheet", "excel_write_to_sheet"]  # Expected excel tools
    )
    
    # This should work or fail with a specific error we can fix
    tools = await excel_toolset.get_tools()
    
    assert len(tools) > 0
    assert any("read" in tool.name.lower() for tool in tools)