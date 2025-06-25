"""Simple MCP client for connecting Staffer to the MCP aggregator service."""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class MCPClientConfig:
    """Configuration for MCP client."""
    host: str
    port: int
    timeout: float = 5.0
    auto_reconnect: bool = True
    max_retries: int = 3
    max_connections: int = 5


class StafferMCPClient:
    """Simple MCP client that connects Staffer to the MCP aggregator service."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP client with configuration validation."""
        self._validate_config(config)
        
        self.host = config['host']
        self.port = config['port']
        self.timeout = config.get('timeout', 5.0)
        self.auto_reconnect = config.get('auto_reconnect', True)
        self.max_retries = config.get('max_retries', 3)
        self.max_connections = config.get('max_connections', 5)
        
        self.is_connected = False
        self.last_error = None
        self._connection = None
        self._tools_cache = {}
        
        self.logger = logging.getLogger(__name__)
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate client configuration."""
        if not config:
            raise ValueError("Configuration cannot be empty")
        
        if 'host' not in config or not config['host']:
            raise ValueError("Host is required and cannot be empty")
        
        if 'port' not in config:
            raise ValueError("Port is required")
        
        if not isinstance(config['port'], int):
            raise TypeError("Port must be an integer")
        
        if config['port'] <= 0 or config['port'] > 65535:
            raise ValueError("Port must be between 1 and 65535")
    
    async def connect(self) -> bool:
        """Connect to the MCP aggregator service."""
        try:
            success = await self._establish_connection()
            if success:
                self.is_connected = True
                self.last_error = None
                self.logger.info(f"Connected to MCP aggregator at {self.host}:{self.port}")
            return success
        except Exception as e:
            self.last_error = e
            self.is_connected = False
            self.logger.error(f"Failed to connect to MCP aggregator: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP aggregator service."""
        try:
            await self._close_connection()
            self.is_connected = False
            self.logger.info("Disconnected from MCP aggregator")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the aggregator."""
        if not self.is_connected:
            return []
        
        try:
            tools = await self._request_tools()
            self._tools_cache = {tool['name']: tool for tool in tools}
            self.logger.info(f"Discovered {len(tools)} tools from aggregator")
            return tools
        except Exception as e:
            self.last_error = e
            self.logger.error(f"Failed to discover tools: {e}")
            return []
    
    async def call_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call through the aggregator."""
        tool_name = tool_call.get('name')
        arguments = tool_call.get('arguments', {})
        
        try:
            # Check if we need to reconnect
            if not self.is_connected and self.auto_reconnect:
                await self.connect()
            
            result = await self._execute_tool(tool_name, arguments)
            return result
            
        except ConnectionError as e:
            # Handle connection loss with auto-reconnect
            if self.auto_reconnect:
                self.logger.warning(f"Connection lost, attempting to reconnect: {e}")
                reconnected = await self.connect()
                if reconnected:
                    # Retry the tool call
                    try:
                        result = await self._execute_tool(tool_name, arguments)
                        return result
                    except Exception as retry_error:
                        return {
                            'success': False,
                            'error': f"Tool execution failed after reconnect: {retry_error}"
                        }
            
            return {
                'success': False,
                'error': f"Connection error: {e}"
            }
            
        except Exception as e:
            self.last_error = e
            self.logger.error(f"Tool execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    # Internal methods that will be mocked in tests
    async def _establish_connection(self) -> bool:
        """Establish connection to MCP aggregator (mocked in tests)."""
        # In real implementation, this would create HTTP/WebSocket connection
        await asyncio.sleep(0.1)  # Simulate connection delay
        return True
    
    async def _close_connection(self) -> None:
        """Close connection to MCP aggregator (mocked in tests)."""
        # In real implementation, this would close the connection
        await asyncio.sleep(0.05)  # Simulate disconnect delay
        self._connection = None
    
    async def _request_tools(self) -> List[Dict[str, Any]]:
        """Request tools from aggregator (mocked in tests)."""
        # In real implementation, this would make HTTP request to /tools endpoint
        await asyncio.sleep(0.1)  # Simulate network delay
        return []
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via aggregator (mocked in tests)."""
        # In real implementation, this would make HTTP POST to /execute endpoint
        await asyncio.sleep(0.1)  # Simulate execution delay
        return {
            'success': True,
            'result': f"Mock result for {tool_name}"
        }


class MCPClientFactory:
    """Factory for creating MCP clients with standard configurations."""
    
    @staticmethod
    def create_local_client(port: int = 8080) -> StafferMCPClient:
        """Create client for local aggregator service."""
        config = {
            'host': 'localhost',
            'port': port,
            'timeout': 5.0,
            'auto_reconnect': True
        }
        return StafferMCPClient(config)
    
    @staticmethod
    def create_production_client(host: str, port: int = 8080) -> StafferMCPClient:
        """Create client for production aggregator service."""
        config = {
            'host': host,
            'port': port,
            'timeout': 10.0,
            'auto_reconnect': True,
            'max_retries': 5
        }
        return StafferMCPClient(config)