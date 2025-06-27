"""Tool discovery engine for multiple MCP servers."""
import asyncio
import time
from typing import Dict, List, Any, Optional
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams
from config import ServerConfig


class ToolDiscoveryEngine:
    """Generic tool discovery and aggregation engine from documentation patterns."""
    
    def __init__(self, cache_duration: int = 300):
        self.cache_duration = cache_duration  # 5 minutes
        self.discovered_tools = {}
        self.conflicts = []
        self.cache = {}
    
    async def discover_all_tools(self, server_configs: List[ServerConfig]) -> Dict[str, Dict[str, Any]]:
        """Discover raw tools from all configured sources.
        
        Returns tools grouped by server name for composer to handle filtering and conflicts.
        """
        all_tools = {}
        
        # Process servers in parallel for performance
        tasks = []
        for server_config in server_configs:
            if server_config.is_available:
                tasks.append(self._discover_server_tools(server_config))
        
        if not tasks:
            print("No available servers to discover tools from")
            return {}
        
        # Gather results from all servers
        server_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Return raw tools grouped by server for composer to handle
        for i, result in enumerate(server_results):
            server_config = server_configs[i] if i < len(server_configs) else None
            
            if isinstance(result, Exception):
                print(f"Server {server_config.name if server_config else 'unknown'} failed: {result}")
                continue
                
            if not result:
                continue
                
            # Store raw tools with server metadata (no conflict resolution here)
            all_tools[server_config.name] = {
                'tools': result,
                'config': server_config
            }
        
        return all_tools
    
    async def _discover_server_tools(self, server_config: ServerConfig) -> Dict[str, Any]:
        """Discover tools from a single MCP server with caching."""
        cache_key = f"{server_config.name}_{server_config.priority}"
        now = time.time()
        
        # Check cache first
        if cache_key in self.cache:
            cached_time, tools = self.cache[cache_key]
            if now - cached_time < self.cache_duration:
                print(f"Using cached tools for {server_config.name}")
                return tools
        
        try:
            print(f"Discovering tools from {server_config.name}...")
            
            # Create MCPToolset for this server
            toolset = self._create_mcp_toolset(server_config)
            tools_list = await toolset.get_tools()
            
            # Convert to dictionary
            tools_dict = {tool.name: tool for tool in tools_list}
            
            print(f"Discovered {len(tools_dict)} tools from {server_config.name}")
            
            # Cache the results
            self.cache[cache_key] = (now, tools_dict)
            
            return tools_dict
            
        except Exception as e:
            print(f"Failed to discover tools from {server_config.name}: {e}")
            return {}
    
    def _create_mcp_toolset(self, server_config: ServerConfig) -> MCPToolset:
        """Create MCPToolset from server configuration.
        
        Note: Tool filtering is now handled by Composer, not Discovery Engine.
        """
        server_params = StdioServerParameters(
            command=server_config.command,
            args=server_config.args,
            cwd=server_config.cwd
        )
        
        connection_params = StdioConnectionParams(
            server_params=server_params
        )
        
        return MCPToolset(
            connection_params=connection_params
            # No tool_filter - raw tools returned for Composer to filter
        )
    
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get statistics about tool discovery."""
        return {
            'total_conflicts': len(self.conflicts),
            'conflicts': self.conflicts,
            'cache_size': len(self.cache),
            'cached_servers': list(self.cache.keys())
        }