"""
StafferMCPClient - Simple MCP protocol client for connecting to MCP aggregator.

Handles MCP protocol communication to discover and execute tools from the aggregator service.
"""
import asyncio
import json
import aiohttp
from typing import List, Dict, Any, Optional


class StafferMCPClient:
    """Client for communicating with MCP aggregator service."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP client with connection configuration.
        
        Args:
            config: Dictionary with 'host', 'port', and optional 'timeout'
        """
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.timeout = config.get('timeout', 5.0)
        self.base_url = f"http://{self.host}:{self.port}"
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from MCP aggregator.
        
        Returns:
            List of tool dictionaries with name, description, and optional schema
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/tools") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Return empty list on error for graceful fallback
                        return []
        except (aiohttp.ClientError, asyncio.TimeoutError):
            # Graceful fallback when aggregator is unavailable
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool through MCP protocol.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool
            
        Returns:
            Tool execution result in MCP format
        """
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.base_url}/execute", json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Return error response
                        return {
                            "content": [
                                {"type": "text", "text": f"Error executing tool {tool_name}: HTTP {response.status}"}
                            ]
                        }
        except asyncio.TimeoutError:
            return {
                "content": [
                    {"type": "text", "text": f"Timeout executing tool {tool_name}"}
                ]
            }
        except aiohttp.ClientError as e:
            return {
                "content": [
                    {"type": "text", "text": f"Connection error executing tool {tool_name}: {e}"}
                ]
            }
    
    async def call_tool_with_timeout(self, tool_name: str, arguments: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Execute tool with explicit timeout handling.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool
            timeout: Timeout in seconds
            
        Returns:
            Tool execution result or timeout error
        """
        try:
            return await asyncio.wait_for(
                self.call_tool(tool_name, arguments),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return self._timeout_response(tool_name)
    
    def _timeout_response(self, tool_name: str) -> Dict[str, Any]:
        """Generate timeout response for tool execution."""
        return {
            "content": [
                {"type": "text", "text": f"Tool {tool_name} execution timed out"}
            ]
        }