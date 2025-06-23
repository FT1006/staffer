"""Tests for MCP client subprocess communication."""
import os
import json
import pytest
from staffer.mcp.client import McpClient


def test_mcp_client_can_communicate():
    """Test that MCP client can send and receive JSON-RPC messages."""
    echo_server_path = os.path.join(
        os.path.dirname(__file__), 
        "test_servers", 
        "test_echo_server.py"
    )
    
    client = McpClient(["python3", echo_server_path])
    
    response = client.send_request("echo", {"message": "hello"})
    
    assert response["result"] == "hello"
    assert response["jsonrpc"] == "2.0"
    
    client.close()


def test_mcp_client_handles_invalid_response():
    """Test that MCP client handles malformed JSON responses gracefully."""
    # This server will send invalid JSON
    invalid_server_cmd = [
        "python3", "-c", 
        "import sys; print('invalid json'); sys.stdout.flush()"
    ]
    
    client = McpClient(invalid_server_cmd)
    
    # This should raise JSONDecodeError since the response is invalid
    with pytest.raises(json.JSONDecodeError):
        client.send_request("echo", {"message": "hello"})
    
    client.close()


def test_tool_discovery_returns_all_tools():
    """Test that MCP client can discover tools from server."""
    mcp_server_path = os.path.join(
        os.path.dirname(__file__), 
        "test_servers", 
        "test_mcp_server.py"
    )
    
    client = McpClient(["python3", mcp_server_path])
    
    # This should fail because McpClient doesn't have initialize() or list_tools()
    client.initialize()
    tools = client.list_tools()
    
    assert len(tools) == 2
    assert tools[0]["name"] == "test_tool" 
    assert tools[1]["name"] == "another_tool"
    
    client.close()