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
        """RED: Test that config loader resolves ${VAR} syntax."""
        # Create temporary config with environment variables
        config_content = """
domain: "test_domain"
model: "test_model"
instruction: "test instruction"

source_servers:
  - name: "test_server"
    command: "python"
    args: ["-m", "test"]
    cwd_env: "TEST_PATH"
    enabled: true
    priority: 1

tool_selection:
  strategy: "curated"
  max_tools_per_server: ${MAX_TOOLS:-10}

server:
  host: "${HOST:-localhost}"
  port: ${PORT:-8080}
  name: "test-server"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test with environment variables set
            with patch.dict(os.environ, {
                'HOST': 'production.server.com',
                'PORT': '9000',
                'MAX_TOOLS': '50'
            }):
                # This will fail until we implement environment variable substitution
                config = load_config(temp_config_path)
                
                # Should resolve environment variables
                assert config.server['host'] == 'production.server.com'
                assert config.server['port'] == 9000
                assert config.tool_selection['max_tools_per_server'] == 50
        finally:
            os.unlink(temp_config_path)
    
    def test_config_loader_uses_defaults_when_env_vars_missing(self):
        """RED: Test that config loader uses default values when env vars not set."""
        config_content = """
domain: "test_domain"
model: "test_model"
instruction: "test instruction"

source_servers: []

tool_selection:
  strategy: "curated"

server:
  host: "${HOST:-localhost}"
  port: ${PORT:-8080}
  name: "test-server"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test with no environment variables set
            with patch.dict(os.environ, {}, clear=True):
                config = load_config(temp_config_path)
                
                # Should use default values
                assert config.server['host'] == 'localhost'
                assert config.server['port'] == 8080
        finally:
            os.unlink(temp_config_path)