"""Tests for MCP client subprocess communication."""
import os
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