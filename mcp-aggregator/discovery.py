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
    
    async def discover_all_tools(self, server_configs: List[ServerConfig]) -> Dict[str, Any]:
        """Discover tools from all configured sources."""
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
        
        # Combine tools from all servers
        for i, result in enumerate(server_results):
            server_config = server_configs[i] if i < len(server_configs) else None
            
            if isinstance(result, Exception):
                print(f"Server {server_config.name if server_config else 'unknown'} failed: {result}")
                continue
                
            if not result:
                continue
                
            # Check for naming conflicts
            conflicts = set(result.keys()) & set(all_tools.keys())
            if conflicts:
                self.conflicts.extend([
                    {
                        'tool': tool, 
                        'servers': [all_tools[tool]['source'], server_config.name]
                    }
                    for tool in conflicts
                ])
            
            # Add tools with metadata
            for tool_name, tool in result.items():
                all_tools[tool_name] = {
                    'tool': tool,
                    'source': server_config.name,
                    'priority': server_config.priority
                }
        
        return self._resolve_conflicts(all_tools)
    
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
        """Create MCPToolset from server configuration."""
        server_params = StdioServerParameters(
            command=server_config.command,
            args=server_config.args,
            cwd=server_config.cwd
        )
        
        connection_params = StdioConnectionParams(
            server_params=server_params
        )
        
        return MCPToolset(
            connection_params=connection_params,
            tool_filter=server_config.tool_filter
        )
    
    def _resolve_conflicts(self, tools: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve tool name conflicts based on priority."""
        resolved_tools = {}
        
        for tool_name, tool_info in tools.items():
            if tool_name in resolved_tools:
                # Keep higher priority tool
                current_priority = resolved_tools[tool_name]['priority']
                new_priority = tool_info['priority']
                
                if new_priority > current_priority:
                    print(f"Conflict resolution: Using {tool_name} from {tool_info['source']} (priority {new_priority})")
                    resolved_tools[tool_name] = tool_info
                else:
                    print(f"Conflict resolution: Keeping {tool_name} from {resolved_tools[tool_name]['source']} (priority {current_priority})")
            else:
                resolved_tools[tool_name] = tool_info
        
        return resolved_tools
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get statistics about tool discovery."""
        return {
            'total_conflicts': len(self.conflicts),
            'conflicts': self.conflicts,
            'cache_size': len(self.cache),
            'cached_servers': list(self.cache.keys())
        }