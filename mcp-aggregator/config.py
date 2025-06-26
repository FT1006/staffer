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
    cwd: str  # Direct path, not environment variable
    tool_filter: Optional[List[str]] = None
    priority: int = 1
    enabled: bool = True
    # Keep backward compatibility with cwd_env for migration
    cwd_env: Optional[str] = None
    
    def __post_init__(self):
        """Handle backward compatibility and direct path resolution."""
        # If cwd_env is provided but cwd is not, resolve from environment
        if self.cwd_env and not hasattr(self, '_cwd_resolved'):
            env_path = os.getenv(self.cwd_env)
            if env_path:
                self.cwd = env_path
            self._cwd_resolved = True
    
    @property
    def is_available(self) -> bool:
        """Check if server is available (path exists and enabled)."""
        return self.enabled and self.cwd and os.path.exists(self.cwd)


@dataclass
class AggregatorConfig:
    """Main aggregator configuration."""
    domain: str
    model: str
    instruction: str
    source_servers: List[ServerConfig]
    tool_selection: Dict[str, Any]
    
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
    """Load configuration from YAML file.
    
    By default, uses direct YAML values (single source of truth).
    Environment variable substitution only occurs for explicit ${VAR} patterns.
    """
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Apply environment variable substitution only for explicit ${VAR} patterns
    config_data = _substitute_env_vars(config_data)
    
    # Parse server configurations
    source_servers = []
    for server_data in config_data.get('source_servers', []):
        # Support both direct 'cwd' and backward-compatible 'cwd_env'
        if 'cwd' in server_data:
            # Direct path configuration (preferred)
            server_config = ServerConfig(
                name=server_data['name'],
                command=server_data['command'],
                args=server_data.get('args', []),
                cwd=server_data['cwd'],
                tool_filter=server_data.get('tool_filter'),
                priority=server_data.get('priority', 1),
                enabled=server_data.get('enabled', True)
            )
        elif 'cwd_env' in server_data:
            # Backward compatibility with environment variables
            server_config = ServerConfig(
                name=server_data['name'],
                command=server_data['command'],
                args=server_data.get('args', []),
                cwd='',  # Will be resolved in __post_init__
                cwd_env=server_data['cwd_env'],
                tool_filter=server_data.get('tool_filter'),
                priority=server_data.get('priority', 1),
                enabled=server_data.get('enabled', True)
            )
        else:
            raise ValueError(f"Server '{server_data['name']}' must have either 'cwd' or 'cwd_env' specified")
        
        source_servers.append(server_config)
    
    return AggregatorConfig(
        domain=config_data.get('domain', ''),
        model=config_data.get('model', ''),
        instruction=config_data.get('instruction', ''),
        source_servers=source_servers,
        tool_selection=config_data.get('tool_selection', {})
    )


def validate_config(config: AggregatorConfig) -> List[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    # Check if any servers are available
    if not config.available_servers:
        issues.append("No MCP servers are available (check paths and enabled status)")
    
    # Check for required fields
    if not config.domain:
        issues.append("Domain is required")
    
    if not config.model:
        issues.append("Model is required")
    
    # Check server configuration
    for server in config.source_servers:
        if server.enabled:
            if not server.cwd:
                if server.cwd_env:
                    issues.append(f"Server '{server.name}' is enabled but {server.cwd_env} environment variable not set")
                else:
                    issues.append(f"Server '{server.name}' is enabled but no path specified")
            elif not os.path.exists(server.cwd):
                issues.append(f"Server '{server.name}' path does not exist: {server.cwd}")
    
    return issues


def normalize_config_dict(config_dict: Dict[str, Any]) -> AggregatorConfig:
    """Normalize a configuration dictionary to AggregatorConfig.
    
    This function ensures all parts of mcp-aggregator work with the same
    standardized configuration format (AggregatorConfig with ServerConfig objects).
    
    Args:
        config_dict: Raw configuration dictionary
        
    Returns:
        AggregatorConfig with properly typed ServerConfig objects
    """
    # Handle source_servers conversion
    source_servers = []
    for server_data in config_dict.get('source_servers', []):
        if isinstance(server_data, ServerConfig):
            # Already a ServerConfig, use as-is
            source_servers.append(server_data)
        elif isinstance(server_data, dict):
            # Convert dict to ServerConfig
            # Support both direct 'cwd' and backward-compatible 'cwd_env'
            if 'cwd' in server_data:
                server_config = ServerConfig(
                    name=server_data.get('name', 'unknown'),
                    command=server_data.get('command', ''),
                    args=server_data.get('args', []),
                    cwd=server_data['cwd'],
                    tool_filter=server_data.get('tool_filter'),
                    priority=server_data.get('priority', 1),
                    enabled=server_data.get('enabled', True)
                )
            else:
                # Backward compatibility
                server_config = ServerConfig(
                    name=server_data.get('name', 'unknown'),
                    command=server_data.get('command', ''),
                    args=server_data.get('args', []),
                    cwd='',
                    cwd_env=server_data.get('cwd_env', ''),
                    tool_filter=server_data.get('tool_filter'),
                    priority=server_data.get('priority', 1),
                    enabled=server_data.get('enabled', True)
                )
            source_servers.append(server_config)
        else:
            # Skip invalid server configs (None, strings, numbers, etc.)
            continue
    
    # Create AggregatorConfig with defaults for missing fields
    return AggregatorConfig(
        domain=config_dict.get('domain', ''),
        model=config_dict.get('model', ''),
        instruction=config_dict.get('instruction', ''),
        source_servers=source_servers,
        tool_selection=config_dict.get('tool_selection', {})
    )