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
    
    def __init__(self, command_list: List[str], selected_tools: Optional[List[str]] = None) -> None:
        """
        Initialize client with command to spawn MCP server.
        
        Args:
            command_list: Command and arguments to spawn the MCP server process
            selected_tools: Optional list of tool names to filter for
            
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
        self.selected_tools = selected_tools or []
    
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
            RuntimeError: If server communication fails
        """
        if not self.process:
            raise ValueError("Client not initialized")
            
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        try:
            self.process.stdin.write(json.dumps(request) + '\n')
            self.process.stdin.flush()
        except Exception as e:
            raise RuntimeError(f"Failed to send request to server: {e}")
        
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("Server closed connection or failed to respond")
            
        try:
            return json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response from server: {response_line[:100]}... Error: {e}")
    
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
        List available tools from the MCP server, filtered by selection if specified.
        
        Returns:
            List of tool dictionaries with name, description, and inputSchema
        """
        if not self.initialized:
            self.initialize()
        
        response = self.send_request("tools/list")
        all_tools = response.get("result", {}).get("tools", [])
        
        if self.selected_tools:
            return [tool for tool in all_tools if tool["name"] in self.selected_tools]
        return all_tools
    
    def __del__(self) -> None:
        """Ensure process cleanup on object destruction."""
        self.close()