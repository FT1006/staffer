"""
Test environment variable substitution in config loader.

Following RED-GREEN-REFACTOR TDD approach.
"""
import pytest
from unittest.mock import patch
import tempfile
import os

from config import load_config


class TestConfigEnvironmentSubstitution:
    """Test config loader supports environment variable substitution."""
    
    def test_config_loader_resolves_environment_variables(self):
        """Test that config loader resolves ${VAR} syntax for legitimate use cases (secrets)."""
        # Create temporary config with environment variables for secrets
        config_content = """
domain: "test_domain"
model: "test_model"
instruction: "test instruction"

source_servers:
  - name: "secure_server"
    command: "python"
    args: ["-m", "secure_server"]
    cwd: "/path/to/secure-server"
    api_key: "${SECRET_API_KEY}"
    enabled: true
    priority: 1
  - name: "env_path_server"
    command: "go"
    args: ["run", "main.go"]
    cwd: "${SERVER_PATH}"
    enabled: "${SERVER_ENABLED:-true}"
    priority: 2

tool_selection:
  strategy: "curated"
  max_tools_per_server: ${MAX_TOOLS:-10}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test with environment variables set
            with patch.dict(os.environ, {
                'SECRET_API_KEY': 'super_secret_key_123',
                'SERVER_PATH': '/tmp/test_server',
                'SERVER_ENABLED': 'false',
                'MAX_TOOLS': '50'
            }):
                config = load_config(temp_config_path)
                
                # Should resolve environment variables
                secure_server = config.source_servers[0]
                env_path_server = config.source_servers[1]
                
                assert hasattr(secure_server, '__dict__') and 'api_key' in secure_server.__dict__
                assert secure_server.api_key == 'super_secret_key_123'
                assert env_path_server.cwd == '/tmp/test_server'
                assert env_path_server.enabled == False
                assert config.tool_selection['max_tools_per_server'] == 50
        finally:
            os.unlink(temp_config_path)
    
    def test_config_loader_uses_defaults_when_env_vars_missing(self):
        """Test that config loader uses default values when env vars not set."""
        config_content = """
domain: "test_domain"
model: "test_model"
instruction: "test instruction"

source_servers:
  - name: "default_server"
    command: "python"
    args: ["-m", "server"]
    cwd: "/default/path"
    enabled: "${SERVER_ENABLED:-true}"
    priority: 1

tool_selection:
  strategy: "curated"
  max_tools_per_server: ${MAX_TOOLS:-25}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test with no environment variables set
            with patch.dict(os.environ, {}, clear=True):
                config = load_config(temp_config_path)
                
                # Should use default values
                server = config.source_servers[0]
                assert server.enabled == True  # Default from ${SERVER_ENABLED:-true}
                assert config.tool_selection['max_tools_per_server'] == 25  # Default from ${MAX_TOOLS:-25}
        finally:
            os.unlink(temp_config_path)