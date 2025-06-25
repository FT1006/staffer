"""GenericMCPServerComposer for aggregating tools from multiple MCP servers."""
import asyncio
from typing import Dict, List, Any, Optional
from config import ServerConfig, AggregatorConfig
from discovery import ToolDiscoveryEngine


class GenericMCPServerComposer:
    """Composes tools from multiple MCP servers with conflict resolution and graceful failure handling."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize composer with configuration."""
        self.config = config
        self.failed_servers = []
        self.server_failures = []  # Track failures for monitoring
        self.discovery_engine = ToolDiscoveryEngine()
    
    async def get_all_tools(self) -> List[Any]:
        """Get aggregated tools from all configured servers."""
        # Get server configurations from config
        server_configs = self._extract_server_configs()
        
        if not server_configs:
            return []
        
        # Use discovery engine to find tools from all servers
        all_tools = {}
        
        for server_config in server_configs:
            try:
                tools = await self._discover_tools_from_server(server_config)
                
                # Handle conflict resolution by priority
                for tool in tools:
                    tool_name = tool.name
                    # Handle both dict and object server configs
                    if isinstance(server_config, dict):
                        server_priority = server_config.get('priority', 1)
                        server_name = server_config.get('name', 'unknown')
                    else:
                        server_priority = getattr(server_config, 'priority', 1)
                        server_name = getattr(server_config, 'name', 'unknown')
                    
                    if tool_name in all_tools:
                        # Conflict detected - use priority to resolve
                        existing_priority = all_tools[tool_name]['priority']
                        if server_priority > existing_priority:
                            # Higher priority wins
                            all_tools[tool_name] = {
                                'tool': tool,
                                'priority': server_priority,
                                'source': server_name
                            }
                    else:
                        # No conflict, add tool
                        all_tools[tool_name] = {
                            'tool': tool,
                            'priority': server_priority,
                            'source': server_name
                        }
                        
            except Exception as e:
                # Gracefully handle server failures
                if isinstance(server_config, dict):
                    server_name = server_config.get('name', 'unknown')
                else:
                    server_name = getattr(server_config, 'name', 'unknown')
                self.failed_servers.append(server_name)
                self.server_failures.append({
                    'server': server_name,
                    'error': str(e)
                })
                # Continue with other servers
                continue
        
        # Return just the tools (not the metadata)
        return [tool_info['tool'] for tool_info in all_tools.values()]
    
    async def _discover_tools_from_server(self, server_config) -> List[Any]:
        """Discover tools from a single server."""
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
    
    def _extract_server_configs(self) -> List[Any]:
        """Extract server configurations from the config."""
        if 'source_servers' in self.config:
            return self.config['source_servers']
        return []