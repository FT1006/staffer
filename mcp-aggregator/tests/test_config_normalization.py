"""RED tests for config normalization - ensuring standardized config format."""
import pytest
from typing import Dict, Any

# Import will succeed since config.py exists
from config import ServerConfig, AggregatorConfig

# Import the function we need to implement
try:
    from config import normalize_config_dict
except ImportError:
    normalize_config_dict = None


class TestConfigNormalization:
    """Test config normalization to standard AggregatorConfig format."""
    
    def test_normalize_dict_config_to_aggregator_config(self):
        """RED: Test normalizing dict config to AggregatorConfig - should fail first."""
        if not normalize_config_dict:
            pytest.skip("normalize_config_dict not implemented yet")
        
        # Given: Raw dict configuration (like from tests)
        raw_config = {
            'domain': 'test_domain',
            'model': 'gemini-2.0-flash',
            'instruction': 'Test aggregator',
            'source_servers': [
                {
                    'name': 'excel',
                    'command': 'go',
                    'args': ['run', 'main.go'],
                    'cwd_env': 'EXCEL_PATH',
                    'enabled': True,
                    'priority': 1
                },
                {
                    'name': 'analytics',
                    'command': 'python',
                    'args': ['-m', 'server'],
                    'cwd_env': 'ANALYTICS_PATH',
                    'enabled': False,
                    'priority': 2
                }
            ],
            'tool_selection': {'strategy': 'curated'}
        }
        
        # When: Normalize to standard format
        normalized = normalize_config_dict(raw_config)
        
        # Then: Should return AggregatorConfig with ServerConfig objects
        assert isinstance(normalized, AggregatorConfig)
        assert normalized.domain == 'test_domain'
        assert normalized.model == 'gemini-2.0-flash'
        assert normalized.instruction == 'Test aggregator'
        
        # Check servers are ServerConfig objects
        assert len(normalized.source_servers) == 2
        for server in normalized.source_servers:
            assert isinstance(server, ServerConfig)
        
        excel_server = normalized.source_servers[0]
        assert excel_server.name == 'excel'
        assert excel_server.command == 'go'
        assert excel_server.enabled is True
        
        analytics_server = normalized.source_servers[1]
        assert analytics_server.name == 'analytics'
        assert analytics_server.enabled is False
    
    def test_normalize_already_normalized_config(self):
        """RED: Test normalizing already normalized config - should be idempotent."""
        if not normalize_config_dict:
            pytest.skip("normalize_config_dict not implemented yet")
        
        # Given: Already normalized config with ServerConfig objects
        server_configs = [
            ServerConfig(
                name='excel',
                command='go',
                args=['run', 'main.go'],
                cwd='/path/to/excel',  # Direct path
                enabled=True,
                priority=1
            )
        ]
        
        raw_config = {
            'domain': 'test_domain',
            'model': 'gemini-2.0-flash',
            'instruction': 'Test',
            'source_servers': server_configs,
            'tool_selection': {}
        }
        
        # When: Normalize already normalized config
        normalized = normalize_config_dict(raw_config)
        
        # Then: Should preserve ServerConfig objects
        assert isinstance(normalized, AggregatorConfig)
        assert len(normalized.source_servers) == 1
        assert normalized.source_servers[0] is server_configs[0]  # Same object
    
    def test_normalize_mixed_server_configs(self):
        """RED: Test normalizing mix of dict and ServerConfig servers."""
        if not normalize_config_dict:
            pytest.skip("normalize_config_dict not implemented yet")
        
        # Given: Mix of dict and ServerConfig in source_servers
        existing_server = ServerConfig(
            name='existing',
            command='test',
            args=[],
            cwd='/path/to/existing',  # Direct path
            enabled=True
        )
        
        raw_config = {
            'domain': 'test',
            'model': 'gemini-2.0-flash',
            'instruction': 'Test',
            'source_servers': [
                existing_server,  # Already a ServerConfig
                {  # Dict that needs conversion
                    'name': 'new_server',
                    'command': 'python',
                    'args': ['-m', 'server'],
                    'cwd': '/path/to/new_server',  # Direct path
                    'enabled': True
                }
            ],
            'tool_selection': {}
        }
        
        # When: Normalize mixed config
        normalized = normalize_config_dict(raw_config)
        
        # Then: Should handle both types correctly
        assert len(normalized.source_servers) == 2
        assert normalized.source_servers[0] is existing_server
        assert isinstance(normalized.source_servers[1], ServerConfig)
        assert normalized.source_servers[1].name == 'new_server'
    
    def test_normalize_handles_missing_fields(self):
        """RED: Test normalization provides defaults for missing fields."""
        if not normalize_config_dict:
            pytest.skip("normalize_config_dict not implemented yet")
        
        # Given: Minimal config missing optional fields
        raw_config = {
            'source_servers': [
                {
                    'name': 'minimal',
                    'command': 'test',
                    'cwd_env': 'TEST_PATH'
                    # Missing: args, enabled, priority, tool_filter
                }
            ]
            # Missing: domain, model, instruction, tool_selection
        }
        
        # When: Normalize minimal config
        normalized = normalize_config_dict(raw_config)
        
        # Then: Should provide sensible defaults
        assert isinstance(normalized, AggregatorConfig)
        assert normalized.domain == ''  # Default empty string
        assert normalized.model == ''   # Default empty string
        assert normalized.instruction == ''  # Default empty string
        assert normalized.tool_selection == {}  # Default empty dict
        
        server = normalized.source_servers[0]
        assert server.args == []  # Default empty list
        assert server.enabled is True  # Default enabled
        assert server.priority == 1  # Default priority
        assert server.tool_filter is None  # Default no filter
    
    def test_normalize_skips_invalid_server_entries(self):
        """RED: Test normalization skips invalid server entries."""
        if not normalize_config_dict:
            pytest.skip("normalize_config_dict not implemented yet")
        
        # Given: Config with invalid server entries
        raw_config = {
            'domain': 'test',
            'model': 'test',
            'source_servers': [
                {'name': 'valid', 'command': 'test', 'cwd_env': 'PATH'},
                None,  # Invalid: None
                'string_server',  # Invalid: string
                123,  # Invalid: number
                {'name': 'valid2', 'command': 'test2', 'cwd_env': 'PATH2'}
            ]
        }
        
        # When: Normalize with invalid entries
        normalized = normalize_config_dict(raw_config)
        
        # Then: Should only include valid servers
        assert len(normalized.source_servers) == 2
        assert normalized.source_servers[0].name == 'valid'
        assert normalized.source_servers[1].name == 'valid2'