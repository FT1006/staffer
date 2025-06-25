"""Configuration management for MCP Aggregator."""
import yaml
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Configuration for an individual MCP server."""
    name: str
    command: str
    args: List[str]
    cwd_env: str
    tool_filter: Optional[List[str]] = None
    priority: int = 1
    enabled: bool = True
    
    @property
    def cwd(self) -> Optional[str]:
        """Get working directory from environment variable."""
        return os.getenv(self.cwd_env)
    
    @property
    def is_available(self) -> bool:
        """Check if server is available (has required environment)."""
        return self.enabled and self.cwd is not None


@dataclass
class AggregatorConfig:
    """Main aggregator configuration."""
    domain: str
    model: str
    instruction: str
    source_servers: List[ServerConfig]
    tool_selection: Dict[str, Any]
    server: Dict[str, Any]
    
    @property
    def available_servers(self) -> List[ServerConfig]:
        """Get only servers that are available."""
        return [server for server in self.source_servers if server.is_available]


def load_config(config_path: str = "aggregation.yaml") -> AggregatorConfig:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Parse server configurations
    source_servers = []
    for server_data in config_data.get('source_servers', []):
        server_config = ServerConfig(
            name=server_data['name'],
            command=server_data['command'],
            args=server_data.get('args', []),
            cwd_env=server_data['cwd_env'],
            tool_filter=server_data.get('tool_filter'),
            priority=server_data.get('priority', 1),
            enabled=server_data.get('enabled', True)
        )
        source_servers.append(server_config)
    
    return AggregatorConfig(
        domain=config_data['domain'],
        model=config_data['model'],
        instruction=config_data['instruction'],
        source_servers=source_servers,
        tool_selection=config_data.get('tool_selection', {}),
        server=config_data.get('server', {})
    )


def validate_config(config: AggregatorConfig) -> List[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    # Check if any servers are available
    if not config.available_servers:
        issues.append("No MCP servers are available (check environment variables)")
    
    # Check for required fields
    if not config.domain:
        issues.append("Domain is required")
    
    if not config.model:
        issues.append("Model is required")
    
    # Check server configuration
    for server in config.source_servers:
        if server.enabled and not server.cwd:
            issues.append(f"Server '{server.name}' is enabled but {server.cwd_env} environment variable not set")
    
    return issues