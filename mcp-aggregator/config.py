"""Configuration management for MCP Aggregator."""
import yaml
import os
import re
from typing import Dict, List, Any, Optional, Union
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


def _substitute_env_vars(obj: Any) -> Any:
    """Recursively substitute environment variables in configuration object."""
    if isinstance(obj, str):
        # Pattern matches ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_env_var(match):
            var_expr = match.group(1)
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                value = os.getenv(var_name.strip(), default_value.strip())
            else:
                value = os.getenv(var_expr.strip(), '')
            
            # Try to convert to appropriate type
            if value.isdigit():
                return int(value)
            elif value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            else:
                return value
        
        # Handle the case where the entire string is a variable substitution
        if re.fullmatch(pattern, obj):
            return replace_env_var(re.match(pattern, obj))
        else:
            # Handle partial substitutions within strings
            return re.sub(pattern, lambda m: str(replace_env_var(m)), obj)
    
    elif isinstance(obj, dict):
        return {key: _substitute_env_vars(value) for key, value in obj.items()}
    
    elif isinstance(obj, list):
        return [_substitute_env_vars(item) for item in obj]
    
    else:
        return obj


def load_config(config_path: str = "aggregation.yaml") -> AggregatorConfig:
    """Load configuration from YAML file with environment variable substitution."""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Substitute environment variables
    config_data = _substitute_env_vars(config_data)
    
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
        domain=config_data.get('domain', ''),
        model=config_data.get('model', ''),
        instruction=config_data.get('instruction', ''),
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