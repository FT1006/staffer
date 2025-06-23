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