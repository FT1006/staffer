"""
StafferMCPClient - MCP protocol client for connecting to MCP aggregator.

Uses ADK MCPToolset to properly communicate with MCP servers via stdio protocol.
"""
import asyncio
import os
from typing import List, Dict, Any, Optional
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams


class StafferMCPClient:
    """Client for communicating with MCP aggregator via MCP protocol."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP client with connection configuration.
        
        Args:
            config: Dictionary with aggregator server configuration
        """
        self.config = config
        self.aggregator_path = config.get('aggregator_path', '/Users/spaceship/project/staffer/mcp-aggregator')
        self.aggregator_config = config.get('aggregator_config', 'test_config.yaml')
        self.timeout = config.get('timeout', 10.0)
        self.toolset = None
        
    async def _ensure_connection(self):
        """Ensure MCP toolset connection is established."""
        if self.toolset is None:
            try:
                # Create server parameters for MCP aggregator
                server_params = StdioServerParameters(
                    command="python3",
                    args=["server.py", "--config", self.aggregator_config],
                    cwd=self.aggregator_path
                )
                
                connection_params = StdioConnectionParams(
                    server_params=server_params
                )
                
                # Create MCPToolset to connect to aggregator
                self.toolset = MCPToolset(connection_params=connection_params)
                
            except Exception as e:
                print(f"Failed to connect to MCP aggregator: {e}")
                return False
        return True
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from MCP aggregator.
        
        Returns:
            List of tool dictionaries with name, description, and optional schema
        """
        try:
            if not await self._ensure_connection():
                return []
            
            # Get tools from MCP aggregator via ADK MCPToolset
            tools = await self.toolset.get_tools()
            
            # Convert ADK tools to dictionary format
            tool_dicts = []
            for tool in tools:
                tool_dict = {
                    'name': tool.name,
                    'description': tool.description or f"Tool: {tool.name}"
                }
                
                # Add input schema if available
                if hasattr(tool, 'input_schema') and tool.input_schema:
                    tool_dict['inputSchema'] = tool.input_schema()
                
                tool_dicts.append(tool_dict)
            
            return tool_dicts
            
        except Exception as e:
            print(f"Error listing tools from MCP aggregator: {e}")
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
        try:
            if not await self._ensure_connection():
                return {
                    "content": [
                        {"type": "text", "text": f"Failed to connect to MCP aggregator for tool {tool_name}"}
                    ]
                }
            
            # Execute tool via MCP toolset
            result = await self.toolset.call_tool(tool_name, **arguments)
            
            # Convert result to expected format
            if isinstance(result, str):
                return {
                    "content": [
                        {"type": "text", "text": result}
                    ]
                }
            elif isinstance(result, dict):
                return {
                    "content": [
                        {"type": "text", "text": str(result)}
                    ]
                }
            else:
                return {
                    "content": [
                        {"type": "text", "text": str(result)}
                    ]
                }
                
        except Exception as e:
            return {
                "content": [
                    {"type": "text", "text": f"Error executing tool {tool_name}: {e}"}
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
    
    async def close(self):
        """Close the MCP connection."""
        if self.toolset:
            try:
                # MCPToolset should handle cleanup automatically
                self.toolset = None
            except Exception as e:
                print(f"Error closing MCP connection: {e}")