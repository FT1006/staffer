"""
MCP Aggregator Server Entry Point.

Production-ready MCP server for aggregating tools from multiple sources.
"""
import argparse
import asyncio
import logging
from typing import List, Any, Optional
from pathlib import Path

from config import load_config, validate_config
from composer import GenericMCPServerComposer


class MCPAggregatorServer:
    """MCP aggregator server for exposing aggregated tools via MCP protocol."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize server with configuration."""
        if config_path is None:
            config_path = "aggregation.yaml"
        
        # Resolve config path relative to server.py if not absolute
        resolved_config_path = self._resolve_config_path(config_path)
        
        # Load and validate configuration
        self.config = load_config(resolved_config_path)
        validation_issues = validate_config(self.config)
        
        if validation_issues:
            raise ValueError(f"Configuration validation failed: {validation_issues}")
        
        # Convert to dict format for composer
        self.config_dict = self._convert_config_to_dict()
        self.composer = GenericMCPServerComposer(self.config_dict)
        self.running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _resolve_config_path(self, config_path: str) -> str:
        """Resolve config path relative to server.py location if not absolute."""
        config_path_obj = Path(config_path)
        
        # If already absolute, use as-is
        if config_path_obj.is_absolute():
            return config_path
        
        # If relative, resolve relative to server.py directory
        server_dir = Path(__file__).parent
        resolved_path = server_dir / config_path
        
        # If the resolved path exists, use it
        if resolved_path.exists():
            return str(resolved_path)
        
        # Otherwise, try the original path (current working directory)
        if config_path_obj.exists():
            return config_path
        
        # If neither exists, provide helpful error message
        raise FileNotFoundError(
            f"Configuration file not found: '{config_path}'\n"
            f"Searched in:\n"
            f"  - {resolved_path} (relative to server.py)\n"
            f"  - {config_path_obj.absolute()} (current directory)"
        )
    
    def _convert_config_to_dict(self) -> dict:
        """Convert AggregatorConfig to dict format for composer."""
        return {
            "domain": self.config.domain,
            "source_servers": [
                {
                    "name": server.name,
                    "command": server.command,
                    "args": server.args,
                    "cwd_env": server.cwd_env,
                    "enabled": server.enabled,
                    "priority": server.priority,
                    "tool_filter": server.tool_filter
                }
                for server in self.config.source_servers
            ],
            "tool_selection": self.config.tool_selection
        }
    
    async def get_tools(self) -> List[Any]:
        """Get aggregated tools from all configured servers."""
        try:
            tools = await self.composer.get_all_tools()
            self.logger.info(f"Successfully aggregated {len(tools)} tools from available servers")
            return tools
        except Exception as e:
            self.logger.error(f"Failed to aggregate tools: {e}")
            return []
    
    def start(self):
        """Start the MCP server."""
        self.running = True
        host = self.config.server.get('host', 'localhost')
        port = self.config.server.get('port', 8080)
        
        self.logger.info(f"MCP Aggregator Server starting on {host}:{port}")
        self.logger.info(f"Available servers: {len(self.config.available_servers)}")
        
        # Log server status
        for server in self.config.source_servers:
            status = "enabled" if server.enabled else "disabled"
            env_status = "available" if server.is_available else "missing env"
            self.logger.info(f"  - {server.name}: {status} ({env_status})")
    
    def stop(self):
        """Stop the MCP server."""
        self.running = False
        self.logger.info("MCP Aggregator Server stopped")


def main():
    """Main entry point for MCP aggregator server."""
    parser = argparse.ArgumentParser(description="MCP Aggregator Server")
    parser.add_argument(
        "--config",
        default="aggregation.yaml",
        help="Path to configuration file (default: aggregation.yaml)"
    )
    
    args = parser.parse_args()
    
    # Create and start server
    server = MCPAggregatorServer(config_path=args.config)
    server.start()


if __name__ == "__main__":
    main()