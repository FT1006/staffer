"""MCP client for subprocess communication."""
import subprocess
import json
from typing import Dict, List, Any, Optional


class McpClient:
    """
    MCP client that communicates with MCP servers via subprocess stdin/stdout.
    
    This client handles JSON-RPC communication with MCP (Model Context Protocol)
    servers running as separate processes.
    """
    
    def __init__(self, command_list: List[str]) -> None:
        """
        Initialize client with command to spawn MCP server.
        
        Args:
            command_list: Command and arguments to spawn the MCP server process
            
        Raises:
            subprocess.SubprocessError: If the process cannot be started
        """
        self.process = subprocess.Popen(
            command_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.initialized = False
    
    def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC request and return response.
        
        Args:
            method: The JSON-RPC method to call
            params: Optional parameters for the method
            
        Returns:
            JSON-RPC response as dictionary
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        return json.loads(response_line)
    
    def close(self) -> None:
        """Clean up and close the MCP client connection."""
        if self.process:
            self.process.terminate()
            self.process.wait()
    
    def initialize(self) -> None:
        """Initialize MCP session with handshake."""
        self.send_request("initialize", {
            "capabilities": {},
            "clientInfo": {"name": "staffer", "version": "1.0"},
            "protocolVersion": "2024-11-05"
        })
        self.initialized = True
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.
        
        Returns:
            List of tool dictionaries with name, description, and inputSchema
        """
        if not self.initialized:
            self.initialize()
        
        response = self.send_request("tools/list")
        return response.get("result", {}).get("tools", [])
    
    def __del__(self) -> None:
        """Ensure process cleanup on object destruction."""
        self.close()