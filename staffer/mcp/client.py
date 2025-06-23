"""MCP client for subprocess communication."""
import subprocess
import json


class McpClient:
    """MCP client that communicates via subprocess stdin/stdout."""
    
    def __init__(self, command_list):
        """Initialize client with command to spawn MCP server."""
        self.process = subprocess.Popen(
            command_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    def send_request(self, method, params=None):
        """Send JSON-RPC request and return response."""
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
    
    def close(self):
        """Close the MCP client connection."""
        if self.process:
            self.process.terminate()
            self.process.wait()