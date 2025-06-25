"""RED tests for YAML configuration system - should fail until implementation."""
import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import patch

# These imports will fail until we implement the configuration loading properly
try:
    from config import load_config, validate_config, AggregatorConfig, ServerConfig
except ImportError:
    load_config = None
    validate_config = None
    AggregatorConfig = None
    ServerConfig = None


class TestYAMLConfigLoading:
    """RED tests for YAML configuration loading - should fail first."""
    
    def test_yaml_config_loads_server_parameters(self):
        """Test YAML config loads server parameters correctly - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: Valid YAML configuration
        yaml_content = """
domain: "test_domain"
model: "gemini-2.0-flash"
instruction: "Test instruction"

source_servers:
  - name: "excel"
    command: "go"
    args: ["run", "main.go"]
    cwd_env: "EXCEL_PATH"
    tool_filter: ["read_excel", "write_excel"]
    priority: 1
    enabled: true
  - name: "analytics"
    command: "python"
    args: ["-m", "analytics"]
    cwd_env: "ANALYTICS_PATH"
    priority: 2
    enabled: false

tool_selection:
  strategy: "curated"
  max_tools_per_server: 10

server:
  host: "localhost"
  port: 8080
"""
        
        # When: Loading configuration from YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                config = load_config(f.name)
            finally:
                os.unlink(f.name)
        
        # Then: Configuration should be loaded correctly
        assert config.domain == "test_domain"
        assert config.model == "gemini-2.0-flash"
        assert config.instruction == "Test instruction"
        
        # Server configurations
        assert len(config.source_servers) == 2
        
        excel_server = config.source_servers[0]
        assert excel_server.name == "excel"
        assert excel_server.command == "go"
        assert excel_server.args == ["run", "main.go"]
        assert excel_server.cwd_env == "EXCEL_PATH"
        assert excel_server.tool_filter == ["read_excel", "write_excel"]
        assert excel_server.priority == 1
        assert excel_server.enabled == True
        
        analytics_server = config.source_servers[1]
        assert analytics_server.name == "analytics"
        assert analytics_server.enabled == False
        
        # Tool selection settings
        assert config.tool_selection["strategy"] == "curated"
        assert config.tool_selection["max_tools_per_server"] == 10
        
        # Server settings
        assert config.server["host"] == "localhost"
        assert config.server["port"] == 8080

    def test_yaml_config_validates_required_fields(self):
        """Test YAML config validation catches missing required fields - should fail first."""
        if not validate_config or not load_config:
            pytest.skip("Configuration validation not implemented yet")
        
        # Given: Invalid configuration missing required fields
        invalid_yaml = """
# Missing domain and model
instruction: "Test instruction"
source_servers: []
"""
        
        # When: Loading and validating invalid configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                config = load_config(f.name)
                issues = validate_config(config)
            finally:
                os.unlink(f.name)
        
        # Then: Should have validation issues
        assert len(issues) > 0
        issue_text = " ".join(issues)
        assert "domain" in issue_text.lower()
        assert "model" in issue_text.lower()

    def test_yaml_config_handles_environment_variables(self):
        """Test YAML config resolves environment variables for server paths - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: Configuration with environment variables and set env vars
        yaml_content = """
domain: "test_domain"
model: "gemini-2.0-flash"
instruction: "Test instruction"

source_servers:
  - name: "excel"
    command: "go"
    args: ["run", "main.go"]
    cwd_env: "TEST_EXCEL_PATH"
    priority: 1
    enabled: true
  - name: "missing_env"
    command: "python"
    args: ["-m", "server"]
    cwd_env: "MISSING_ENV_VAR"
    priority: 2
    enabled: true

tool_selection: {}
server: {}
"""
        
        # Set test environment variable
        with patch.dict(os.environ, {'TEST_EXCEL_PATH': '/tmp/test_excel'}):
            # When: Loading configuration
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(yaml_content)
                f.flush()
                
                try:
                    config = load_config(f.name)
                finally:
                    os.unlink(f.name)
            
            # Then: Should resolve environment variables correctly
            excel_server = next(s for s in config.source_servers if s.name == "excel")
            missing_server = next(s for s in config.source_servers if s.name == "missing_env")
            
            # Available server with env var set
            assert excel_server.cwd == '/tmp/test_excel'
            assert excel_server.is_available == True
            
            # Unavailable server with missing env var
            assert missing_server.cwd is None
            assert missing_server.is_available == False
            
            # Available servers filter
            available = config.available_servers
            assert len(available) == 1
            assert available[0].name == "excel"


class TestServerConfigProperties:
    """RED tests for ServerConfig property behaviors - should fail first."""
    
    def test_server_config_cwd_property_reads_environment(self):
        """Test ServerConfig.cwd reads from environment variable - should fail first."""
        if not ServerConfig:
            pytest.skip("ServerConfig not implemented yet")
        
        # Given: ServerConfig with environment variable
        with patch.dict(os.environ, {'TEST_CWD_VAR': '/test/path'}):
            server = ServerConfig(
                name="test_server",
                command="test_cmd",
                args=[],
                cwd_env="TEST_CWD_VAR"
            )
            
            # Then: Should read path from environment
            assert server.cwd == '/test/path'
    
    def test_server_config_is_available_checks_environment(self):
        """Test ServerConfig.is_available checks environment variable - should fail first."""
        if not ServerConfig:
            pytest.skip("ServerConfig not implemented yet")
        
        # Given: ServerConfig with missing environment variable
        server = ServerConfig(
            name="test_server",
            command="test_cmd", 
            args=[],
            cwd_env="NONEXISTENT_VAR",
            enabled=True
        )
        
        # Then: Should not be available when env var missing
        assert server.is_available == False
        
        # Given: ServerConfig with existing environment variable
        with patch.dict(os.environ, {'EXISTING_VAR': '/some/path'}):
            available_server = ServerConfig(
                name="available_server",
                command="test_cmd",
                args=[],
                cwd_env="EXISTING_VAR",
                enabled=True
            )
            
            # Then: Should be available when env var exists
            assert available_server.is_available == True


class TestEdgeCases:
    """RED tests for edge cases and error handling - should fail first."""
    
    def test_yaml_config_handles_malformed_yaml(self):
        """Test YAML config handles malformed YAML gracefully - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: Malformed YAML content
        malformed_yaml = """
domain: "test"
  invalid: [ yaml syntax
model: "unclosed
"""
        
        # When: Loading malformed YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_yaml)
            f.flush()
            
            try:
                # Then: Should raise appropriate error or handle gracefully
                with pytest.raises((yaml.YAMLError, ValueError, Exception)):
                    load_config(f.name)
            finally:
                os.unlink(f.name)

    @pytest.mark.parametrize("server_count", [1, 3, 5])
    def test_config_loads_any_number_of_servers(self, server_count):
        """Test config scales with any number of servers - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: Configuration with N servers
        yaml_content = self._generate_config_with_n_servers(server_count)
        
        # When: Loading configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                config = load_config(f.name)
            finally:
                os.unlink(f.name)
        
        # Then: Should load exactly N servers
        assert len(config.source_servers) == server_count
        
        # All servers should have unique names
        server_names = [s.name for s in config.source_servers]
        assert len(set(server_names)) == server_count
    
    def _generate_config_with_n_servers(self, n):
        """Generate YAML config with N servers."""
        servers = []
        for i in range(n):
            servers.append(f"""  - name: "server_{i}"
    command: "python"
    args: ["-m", "server_{i}"]
    cwd_env: "SERVER_{i}_PATH"
    priority: {i + 1}
    enabled: true""")
        
        return f"""
domain: "test_domain"
model: "gemini-2.0-flash"
instruction: "Test instruction"

source_servers:
{chr(10).join(servers)}

tool_selection: {{}}
server: {{}}
"""

    def test_yaml_config_handles_missing_file(self):
        """Test YAML config handles missing file gracefully - should fail first."""
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: Non-existent file path
        nonexistent_path = "/tmp/nonexistent_config_file.yaml"
        
        # When/Then: Loading missing file should raise appropriate error
        with pytest.raises((FileNotFoundError, IOError)):
            load_config(nonexistent_path)

    def test_yaml_config_handles_empty_file(self):
        """Test YAML config handles empty file gracefully - should fail first.""" 
        if not load_config:
            pytest.skip("Configuration loading not implemented yet")
        
        # Given: Empty YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            try:
                # When/Then: Loading empty file should handle gracefully
                with pytest.raises((ValueError, KeyError, AttributeError)):
                    load_config(f.name)
            finally:
                os.unlink(f.name)


class TestConfigValidation:
    """RED tests for configuration validation - should fail first."""
    
    def test_validation_catches_no_available_servers(self):
        """Test validation catches when no servers are available - should fail first."""
        if not validate_config or not AggregatorConfig or not ServerConfig:
            pytest.skip("Configuration validation not implemented yet")
        
        # Given: Configuration with no available servers (missing env vars)
        unavailable_server = ServerConfig(
            name="unavailable",
            command="test",
            args=[],
            cwd_env="MISSING_VAR",
            enabled=True
        )
        
        config = AggregatorConfig(
            domain="test",
            model="gemini-2.0-flash", 
            instruction="test",
            source_servers=[unavailable_server],
            tool_selection={},
            server={}
        )
        
        # When: Validating configuration
        issues = validate_config(config)
        
        # Then: Should report no available servers
        assert len(issues) > 0
        issue_text = " ".join(issues)
        assert "no mcp servers are available" in issue_text.lower()
    
    def test_validation_catches_enabled_server_missing_env(self):
        """Test validation catches enabled servers with missing env vars - should fail first."""
        if not validate_config or not AggregatorConfig or not ServerConfig:
            pytest.skip("Configuration validation not implemented yet")
        
        # Given: Enabled server with missing environment variable
        server = ServerConfig(
            name="test_server",
            command="test",
            args=[],
            cwd_env="MISSING_ENV_VAR",
            enabled=True
        )
        
        config = AggregatorConfig(
            domain="test",
            model="gemini-2.0-flash",
            instruction="test", 
            source_servers=[server],
            tool_selection={},
            server={}
        )
        
        # When: Validating configuration
        issues = validate_config(config)
        
        # Then: Should report missing environment variable
        assert len(issues) > 0
        issue_text = " ".join(issues)
        assert "test_server" in issue_text
        assert "MISSING_ENV_VAR" in issue_text