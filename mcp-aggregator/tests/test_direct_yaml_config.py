"""RED tests for direct YAML configuration - YAML as single source of truth."""
import pytest
import tempfile
import os
import yaml
from pathlib import Path

# These imports will fail until we implement the direct configuration loading
try:
    from config import load_config, validate_config, AggregatorConfig, ServerConfig
except ImportError:
    load_config = None
    validate_config = None
    AggregatorConfig = None
    ServerConfig = None


class TestDirectYAMLConfig:
    """RED tests for direct YAML configuration (no environment substitution by default)."""
    
    def test_direct_yaml_config_with_absolute_paths(self):
        """Test YAML config uses direct paths, not environment variables - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: YAML with direct paths (no env substitution)
        yaml_content = """
domain: "direct_config_test"
model: "gemini-2.0-flash"
instruction: "Direct configuration test"

source_servers:
  - name: "excel"
    command: "go"
    args: ["run", "main.go"]
    cwd: "/absolute/path/to/excel-server"
    tool_filter: ["read_excel", "write_excel"]
    priority: 1
    enabled: true
  - name: "analytics"
    command: "python3"
    args: ["-m", "analytics_server"]
    cwd: "/absolute/path/to/analytics-server"
    priority: 2
    enabled: false

tool_selection:
  strategy: "curated"
  max_tools_per_server: 15
"""
        
        # When: Loading configuration from YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                config = load_config(f.name)
            finally:
                os.unlink(f.name)
        
        # Then: Configuration should use direct values (no env substitution)
        assert config.domain == "direct_config_test"
        assert len(config.source_servers) == 2
        
        excel_server = config.source_servers[0]
        assert excel_server.name == "excel"
        assert excel_server.cwd == "/absolute/path/to/excel-server"  # Direct path
        assert excel_server.enabled == True  # Direct boolean
        
        analytics_server = config.source_servers[1]
        assert analytics_server.name == "analytics"
        assert analytics_server.cwd == "/absolute/path/to/analytics-server"  # Direct path
        assert analytics_server.enabled == False  # Direct boolean

    def test_server_availability_based_on_path_existence(self):
        """Test server availability based on actual path existence, not env vars - should fail first."""
        if not ServerConfig:
            pytest.skip("ServerConfig not implemented yet")
        
        # Given: ServerConfig with direct path
        with tempfile.TemporaryDirectory() as temp_dir:
            server = ServerConfig(
                name="test_server",
                command="test_cmd",
                args=[],
                cwd=temp_dir,  # Direct path (exists)
                enabled=True
            )
            
            # Then: Should be available when path exists
            assert server.is_available == True
        
        # Given: ServerConfig with non-existent path
        server_missing = ServerConfig(
            name="missing_server",
            command="test_cmd",
            args=[],
            cwd="/nonexistent/path",  # Direct path (doesn't exist)
            enabled=True
        )
        
        # Then: Should not be available when path doesn't exist
        assert server_missing.is_available == False

    def test_disabled_server_is_not_available(self):
        """Test disabled servers are not available regardless of path - should fail first."""
        if not ServerConfig:
            pytest.skip("ServerConfig not implemented yet")
        
        # Given: Disabled server with valid path
        with tempfile.TemporaryDirectory() as temp_dir:
            server = ServerConfig(
                name="disabled_server",
                command="test_cmd",
                args=[],
                cwd=temp_dir,  # Valid path
                enabled=False  # Disabled
            )
            
            # Then: Should not be available when disabled
            assert server.is_available == False

    def test_optional_env_substitution_when_explicitly_used(self):
        """Test env substitution still works when explicitly used in YAML - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: YAML that explicitly uses environment variables for secrets
        yaml_content = """
domain: "mixed_config_test"
model: "gemini-2.0-flash"
instruction: "Mixed configuration test"

source_servers:
  - name: "secure_server"
    command: "python3"
    args: ["-m", "secure_server"]
    cwd: "/absolute/path/to/secure-server"  # Direct path
    api_key: "${SECRET_API_KEY}"  # Explicit env for secret
    enabled: true
  - name: "regular_server"
    command: "go"
    args: ["run", "main.go"]
    cwd: "/absolute/path/to/regular-server"  # Direct path
    enabled: true

tool_selection: {}
"""
        
        # Set environment variable for secret
        test_env = {'SECRET_API_KEY': 'test_secret_123'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                # When: Loading config with env vars set
                with pytest.MonkeyPatch().context() as m:
                    m.setenv('SECRET_API_KEY', 'test_secret_123')
                    config = load_config(f.name)
            finally:
                os.unlink(f.name)
        
        # Then: Direct paths should be used, env substitution only for explicit vars
        secure_server = config.source_servers[0]
        regular_server = config.source_servers[1]
        
        assert secure_server.cwd == "/absolute/path/to/secure-server"  # Direct path
        assert regular_server.cwd == "/absolute/path/to/regular-server"  # Direct path
        
        # Only explicit env substitution should work
        if hasattr(secure_server, 'api_key'):
            assert secure_server.api_key == "test_secret_123"


class TestYAMLAsSingleSourceOfTruth:
    """RED tests ensuring YAML is the single source of truth."""
    
    def test_yaml_config_ignores_unrelated_env_vars(self):
        """Test YAML config ignores environment variables not explicitly referenced - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: YAML with direct configuration and unrelated env vars
        yaml_content = """
domain: "env_ignore_test"
model: "gemini-2.0-flash"
instruction: "Environment ignore test"

source_servers:
  - name: "direct_server"
    command: "python3"
    args: ["-m", "server"]
    cwd: "/direct/path/to/server"
    enabled: true

tool_selection: {}
"""
        
        # Set environment variables that should be ignored
        unrelated_env = {
            'EXCEL_PATH': '/env/excel/path',
            'ANALYTICS_PATH': '/env/analytics/path',
            'SERVER_ENABLED': 'false',
            'RANDOM_VAR': 'should_be_ignored'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                # When: Loading config with unrelated env vars
                with pytest.MonkeyPatch().context() as m:
                    for key, value in unrelated_env.items():
                        m.setenv(key, value)
                    config = load_config(f.name)
            finally:
                os.unlink(f.name)
        
        # Then: Should use YAML values, not environment
        server = config.source_servers[0]
        assert server.cwd == "/direct/path/to/server"  # From YAML, not env
        assert server.enabled == True  # From YAML, not env

    def test_config_validation_checks_direct_paths(self):
        """Test validation works with direct paths, not env vars - should fail first."""
        if not validate_config or not AggregatorConfig or not ServerConfig:
            pytest.skip("Configuration validation not implemented yet")
        
        # Given: Configuration with direct paths
        with tempfile.TemporaryDirectory() as valid_dir:
            valid_server = ServerConfig(
                name="valid_server",
                command="test",
                args=[],
                cwd=valid_dir,  # Valid direct path
                enabled=True
            )
            
            invalid_server = ServerConfig(
                name="invalid_server", 
                command="test",
                args=[],
                cwd="/nonexistent/direct/path",  # Invalid direct path
                enabled=True
            )
            
            config = AggregatorConfig(
                domain="test",
                model="gemini-2.0-flash",
                instruction="test",
                source_servers=[valid_server, invalid_server],
                tool_selection={}
            )
            
            # When: Validating configuration
            issues = validate_config(config)
            
            # Then: Should report issues with invalid direct paths
            assert len(issues) > 0
            issue_text = " ".join(issues)
            assert "invalid_server" in issue_text
            assert "nonexistent" in issue_text.lower() or "not found" in issue_text.lower()