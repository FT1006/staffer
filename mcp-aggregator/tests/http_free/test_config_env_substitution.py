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
    
    def test_config_loader_resolves_stdio_environment_variables(self):
        """RED: Test that config loader resolves ${VAR} syntax for STDIO configs only."""
        # Create temporary config with environment variables (NO server section)
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
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test with environment variables set
            with patch.dict(os.environ, {
                'MAX_TOOLS': '50'
            }):
                # Should implement environment variable substitution
                config = load_config(temp_config_path)
                
                # Should resolve environment variables in STDIO config only
                assert config.tool_selection['max_tools_per_server'] == 50
                # No server section for STDIO protocol
                assert config.server is None
        finally:
            os.unlink(temp_config_path)
    
    def test_config_loader_uses_defaults_for_stdio_when_env_vars_missing(self):
        """RED: Test that config loader uses default values for STDIO configs when env vars not set."""
        config_content = """
domain: "test_domain"
model: "test_model"
instruction: "test instruction"

source_servers: []

tool_selection:
  strategy: "curated"
  max_tools_per_server: ${MAX_TOOLS:-15}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test with no environment variables set
            with patch.dict(os.environ, {}, clear=True):
                config = load_config(temp_config_path)
                
                # Should use default values for STDIO configs
                assert config.tool_selection['max_tools_per_server'] == 15
                # No server section for STDIO protocol
                assert config.server is None
        finally:
            os.unlink(temp_config_path)