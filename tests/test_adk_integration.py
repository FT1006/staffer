"""Tests for Google ADK integration."""
import pytest
import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams


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


@pytest.mark.asyncio
async def test_adk_tool_filter_works():
    """Test that tool_filter actually filters tools."""
    server_params = StdioServerParameters(
        command="go",
        args=["run", "cmd/excel-mcp-server/main.go"],
        cwd="/Users/spaceship/project/staffer/excel-mcp-server"
    )
    
    connection_params = StdioConnectionParams(
        server_params=server_params
    )
    
    # Test 1: Get ALL tools (no filter)
    all_tools_toolset = MCPToolset(connection_params=connection_params)
    all_tools = await all_tools_toolset.get_tools()
    
    # Test 2: Get FILTERED tools  
    filtered_toolset = MCPToolset(
        connection_params=connection_params,
        tool_filter=["excel_read_sheet"]  # Only one specific tool
    )
    filtered_tools = await filtered_toolset.get_tools()
    
    # Debug output
    all_tool_names = [tool.name for tool in all_tools]
    filtered_tool_names = [tool.name for tool in filtered_tools]
    print(f"All tools ({len(all_tools)}): {all_tool_names}")
    print(f"Filtered tools ({len(filtered_tools)}): {filtered_tool_names}")
    
    # tool_filter should reduce the number of tools
    assert len(all_tools) > len(filtered_tools)
    assert len(filtered_tools) == 1
    assert filtered_tools[0].name == "excel_read_sheet"