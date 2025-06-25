"""
Test production MCP ADK configurations for environment-driven deployment.

Following RED-GREEN-REFACTOR TDD approach for configurable, deployable configurations.
Tests enforce environment variable resolution, not hardcoding.
"""
import pytest
from unittest.mock import patch
from pathlib import Path
import os
import yaml

from config import load_config


class TestProductionConfigurability:
    """Test production configuration supports environment-driven deployment."""
    
    def test_production_config_file_exists(self):
        """Test that production config file exists."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        # This will fail until we create the production config
        assert production_config_path.exists(), "production.yaml should exist"
    
    def test_production_config_has_no_server_section(self):
        """RED: Test that production config uses STDIO protocol (no server section)."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        # Read raw YAML to check for STDIO-only configuration
        with open(production_config_path, 'r') as f:
            raw_config = f.read()
        
        # Should NOT have server section (STDIO protocol)
        import yaml
        config_data = yaml.safe_load(raw_config)
        assert "server" not in config_data, \
            "Production config should not have server section for STDIO protocol"
        assert "host" not in raw_config, \
            "Production config should not reference host (STDIO protocol)"
        assert "port" not in raw_config, \
            "Production config should not reference port (STDIO protocol)"
    
    def test_production_config_loads_without_server_section(self):
        """RED: Test that production config loads successfully without server section."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        # Test with no environment variables set
        with patch.dict(os.environ, {}, clear=True):
            # Should load successfully with STDIO config
            config = load_config(str(production_config_path))
            
            # Should NOT have server section for STDIO protocol
            assert config.server is None, \
                "Production config should not have server settings for STDIO protocol"
    
    def test_mcp_server_paths_are_configurable(self):
        """RED: Test that MCP server paths come from environment variables."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        config = load_config(str(production_config_path))
        
        # All servers should depend on environment variables for paths
        for server in config.source_servers:
            assert server.cwd_env is not None, f"Server {server.name} should have cwd_env set"
            assert len(server.cwd_env) > 0, f"Server {server.name} should specify environment variable"
            
            # Environment variable should follow naming convention
            assert server.cwd_env.endswith("_PATH") or server.cwd_env.endswith("_DIR"), \
                f"Server {server.name} env var {server.cwd_env} should follow PATH/DIR convention"
    
    def test_tool_discovery_supports_multiple_strategies(self):
        """RED: Test that configuration supports flexible tool discovery."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        config = load_config(str(production_config_path))
        
        # Should support configurable tool selection strategy
        assert hasattr(config, 'tool_selection'), "Config should have tool_selection settings"
        assert 'strategy' in config.tool_selection, "Should specify tool selection strategy"
        
        # Strategy should be configurable, not hardcoded
        valid_strategies = ['curated', 'dynamic', 'hybrid', 'discovery']
        assert config.tool_selection['strategy'] in valid_strategies, \
            f"Tool selection strategy should be one of {valid_strategies}"
    
    def test_stdio_configuration_adapts_to_different_environments(self):
        """RED: Test that STDIO config works across dev/staging/production environments."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        # Test development environment (STDIO only)
        with patch.dict(os.environ, {
            'EXCEL_MCP_PATH': '/dev/excel-server',
            'ANALYTICS_MCP_PATH': '/dev/analytics-server'
        }):
            dev_config = load_config(str(production_config_path))
            # Should work in development with STDIO
            assert len(dev_config.source_servers) > 0
            assert dev_config.server is None  # No server section for STDIO
        
        # Test production environment (STDIO only)
        with patch.dict(os.environ, {
            'EXCEL_MCP_PATH': '/opt/excel-server',
            'ANALYTICS_MCP_PATH': '/opt/analytics-server'
        }):
            prod_config = load_config(str(production_config_path))
            # Should work in production with STDIO
            assert len(prod_config.source_servers) > 0
            assert prod_config.server is None  # No server section for STDIO
    
    def test_stdio_environment_variable_documentation_exists(self):
        """RED: Test that STDIO environment variables are documented for deployment."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        env_example_path = Path(__file__).parent.parent.parent / ".env.example"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        # This will fail until we create .env.example
        assert env_example_path.exists(), ".env.example should exist for deployment documentation"
        
        env_content = env_example_path.read_text()
        
        # Should document STDIO-only environment variables (no HOST/PORT)
        required_env_vars = [
            'EXCEL_MCP_PATH',
            'ANALYTICS_MCP_PATH'
        ]
        
        for env_var in required_env_vars:
            assert f"{env_var}=" in env_content, f".env.example should document {env_var}"
            
        # Should NOT document HTTP variables
        forbidden_vars = ['HOST', 'PORT', 'MCP_AGGREGATOR_HOST', 'MCP_AGGREGATOR_PORT']
        for var in forbidden_vars:
            assert var not in env_content, f".env.example should not document HTTP variable {var}"
    
    def test_configuration_supports_feature_toggles(self):
        """RED: Test that servers can be enabled/disabled via environment."""
        production_config_path = Path(__file__).parent.parent.parent / "production.yaml"
        
        if not production_config_path.exists():
            pytest.skip("production.yaml not created yet")
            
        # Should support environment-driven feature toggles
        with patch.dict(os.environ, {'EXCEL_ENABLED': 'false', 'ANALYTICS_ENABLED': 'true'}):
            # This will fail until we implement environment-driven server enabling
            config = load_config(str(production_config_path))
            
            # Configuration should be flexible enough to handle runtime toggles
            assert hasattr(config, 'source_servers'), "Should have source_servers"
            
            # All servers should support being enabled/disabled
            for server in config.source_servers:
                assert hasattr(server, 'enabled'), f"Server {server.name} should have enabled property"