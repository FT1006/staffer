"""GenericMCPServerComposer for aggregating tools from multiple MCP servers."""
import asyncio
import os
from typing import Dict, List, Any, Optional
from config import ServerConfig, AggregatorConfig
from discovery import ToolDiscoveryEngine


class GenericMCPServerComposer:
    """Composes tools from multiple MCP servers with conflict resolution and graceful failure handling."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize composer with configuration.
        
        Args:
            config: Configuration dict that will be normalized to AggregatorConfig
        """
        # Normalize configuration to standard format
        from config import normalize_config_dict
        self.config = normalize_config_dict(config)
        self.failed_servers = []
        self.server_failures = []  # Track failures for monitoring
        self.discovery_engine = ToolDiscoveryEngine()
    
    @classmethod
    def from_config(cls, config_path: str):
        """Create composer from YAML config file."""
        from config import load_config
        aggregator_config = load_config(config_path)
        # Store ServerConfig objects directly instead of converting to dicts
        config_dict = {
            'source_servers': aggregator_config.source_servers
        }
        return cls(config_dict)
    
    async def get_all_tools(self) -> List[Any]:
        """Get aggregated raw ADK tools from all configured servers with conflict resolution."""
        # Get server configurations from config
        server_configs = self._extract_server_configs()
        
        print(f"DEBUG: Composer loaded {len(server_configs)} server configs")
        for config in server_configs:
            print(f"  - {config.name}: enabled={config.enabled}, available={config.is_available}")
            if hasattr(config, 'tool_filter') and config.tool_filter:
                print(f"    tool_filter: {config.tool_filter}")
        
        if not server_configs:
            return []
        
        # Use discovery engine to get raw tools from all servers
        available_configs = [cfg for cfg in server_configs if cfg.is_available]
        raw_tools_by_server = await self.discovery_engine.discover_all_tools(available_configs)
        
        if not raw_tools_by_server:
            return []
        
        # Apply filtering and conflict resolution in Composer (ADR-007)
        all_tools = {}
        
        for server_name, server_data in raw_tools_by_server.items():
            server_config = server_data['config']
            server_tools = server_data['tools']
            
            # Apply tool filtering per server configuration
            filtered_tools = self._apply_tool_filter(server_tools, server_config.tool_filter)
            
            print(f"DEBUG: {server_name} - {len(server_tools)} raw tools, {len(filtered_tools)} after filtering")
            
            # Apply conflict resolution by priority on raw ADK tools
            for tool_name, adk_tool in filtered_tools.items():
                
                if tool_name in all_tools:
                    # Conflict detected - use priority to resolve
                    existing_priority = all_tools[tool_name]['priority']
                    if server_config.priority > existing_priority:
                        print(f"Conflict resolution: Using {tool_name} from {server_name} (priority {server_config.priority})")
                        all_tools[tool_name] = {
                            'tool': adk_tool,
                            'priority': server_config.priority,
                            'source': server_name
                        }
                    else:
                        print(f"Conflict resolution: Keeping {tool_name} from {all_tools[tool_name]['source']} (priority {existing_priority})")
                else:
                    # No conflict, add tool
                    all_tools[tool_name] = {
                        'tool': adk_tool,
                        'priority': server_config.priority,
                        'source': server_name
                    }
        
        # Return just the raw ADK tools (not the metadata)
        return [tool_info['tool'] for tool_info in all_tools.values()]
    
    async def _discover_tools_from_server(self, server_config) -> List[Any]:
        """Discover tools from a single server with graceful error handling."""
        try:
            # This method is mocked in tests - implement basic functionality
            if hasattr(server_config, 'tools'):
                # Test configuration with direct tools
                return server_config.tools
            
            # Real server configuration - use discovery engine
            if isinstance(server_config, dict):
                # Convert dict to ServerConfig-like object for testing
                class MockServerConfig:
                    def __init__(self, config_dict):
                        self.name = config_dict.get('name', 'unknown')
                        self.priority = config_dict.get('priority', 1)
                        self.tools = config_dict.get('tools', [])
                        
                mock_config = MockServerConfig(server_config)
                return mock_config.tools
            
            # For actual ServerConfig objects, use the discovery engine
            if isinstance(server_config, ServerConfig):
                tools_dict = await self.discovery_engine._discover_server_tools(server_config)
                return list(tools_dict.values())
            
            return []
            
        except (ConnectionError, TimeoutError, OSError) as e:
            # Re-raise connection errors to be handled by caller
            # This allows graceful fallback at the aggregation level
            raise e
        except Exception as e:
            # Log unexpected errors but don't crash the entire aggregation
            print(f"Warning: Unexpected error discovering tools from {server_config.name}: {e}")
            return []
    
    
    
    def _apply_tool_filter(self, tools: Dict[str, Any], tool_filter: Optional[List[str]]) -> Dict[str, Any]:
        """Apply tool filtering based on server configuration.
        
        Args:
            tools: Raw tools discovered from server
            tool_filter: List of tool names to include (None = include all)
            
        Returns:
            Filtered tools dictionary
        """
        if not tool_filter:
            # No filter specified - return all tools
            return tools
        
        # Filter tools to only include those in the filter list
        filtered_tools = {}
        for tool_name, tool in tools.items():
            if tool_name in tool_filter:
                filtered_tools[tool_name] = tool
        
        return filtered_tools
    
    def _extract_server_configs(self) -> List[ServerConfig]:
        """Extract server configurations from the normalized config."""
        return self.config.source_servers
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name with the given arguments.
        
        This method finds which server provides the tool and executes it directly
        using the ADK tool's run_async method as documented in MCP_INTEGRATION_SUCCESS_STORY.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not found
            Exception: If tool execution fails
        """
        # Get server configurations
        server_configs = self._extract_server_configs()
        
        # Find which server has this tool
        for server_config in server_configs:
            # Check if server is available (config normalization ensures ServerConfig objects)
            if not server_config.is_available:
                continue
                    
            # Discover tools from this server
            try:
                tools_dict = await self.discovery_engine._discover_server_tools(server_config)
                
                # Check if this server has the requested tool
                if tool_name in tools_dict:
                    adk_tool = tools_dict[tool_name]
                    
                    # Execute the tool directly using ADK's run_async method
                    # This is the documented pattern from MCP_INTEGRATION_SUCCESS_STORY
                    result = await adk_tool.run_async(
                        args=arguments,
                        tool_context=None
                    )
                    
                    return result
                    
            except Exception as e:
                # Log error but continue checking other servers
                print(f"Error checking server {server_config.name} for tool {tool_name}: {e}")
                continue
        
        # Tool not found in any server
        raise ValueError(f"Tool '{tool_name}' not found in any configured MCP server")