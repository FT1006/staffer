"""RED tests for discovery engine config alignment - ensuring standardized config usage."""
import pytest
import os
from unittest.mock import patch, Mock, AsyncMock
from pathlib import Path

# Import components
from config import ServerConfig, normalize_config_dict
from discovery import ToolDiscoveryEngine
from composer import GenericMCPServerComposer


class TestDiscoveryConfigAlignment:
    """Test that discovery engine works with standardized config format."""
    
    @pytest.mark.asyncio
    async def test_discovery_engine_accepts_server_config_list(self):
        """RED: Test discovery engine works with List[ServerConfig] - should pass."""
        # Given: Standardized ServerConfig objects
        server_configs = [
            ServerConfig(
                name='test_server',
                command='python',
                args=['-m', 'server'],
                cwd_env='TEST_PATH',
                enabled=True,
                priority=1
            )
        ]
        
        # Set environment for availability
        with patch.dict(os.environ, {'TEST_PATH': '/tmp/test'}):
            discovery_engine = ToolDiscoveryEngine()
            
            # Mock the actual tool discovery to avoid real server connections
            with patch.object(discovery_engine, '_discover_server_tools') as mock_discover:
                mock_discover.return_value = {'test_tool': Mock()}
                
                # When: Discover tools using standardized config
                result = await discovery_engine.discover_all_tools(server_configs)
                
                # Then: Should work without any dict/ServerConfig conversion issues
                assert isinstance(result, dict)
                mock_discover.assert_called_once_with(server_configs[0])
    
    @pytest.mark.asyncio
    async def test_composer_uses_discovery_engine_properly(self):
        """RED: Test composer integrates with discovery engine using standard config."""
        # Given: Raw dict config that gets normalized
        raw_config = {
            'source_servers': [
                {
                    'name': 'test_server',
                    'command': 'python',
                    'args': ['-m', 'server'],
                    'cwd_env': 'TEST_PATH',
                    'enabled': True,
                    'priority': 1
                }
            ]
        }
        
        with patch.dict(os.environ, {'TEST_PATH': '/tmp/test'}):
            composer = GenericMCPServerComposer(raw_config)
            
            # Mock the discovery to avoid real connections
            with patch.object(composer, '_discover_tools_from_server') as mock_discover:
                mock_discover.return_value = [Mock(name='test_tool')]
                
                # When: Get tools (should use normalized config internally)
                tools = await composer.get_all_tools()
                
                # Then: Should work with standardized ServerConfig objects
                assert isinstance(tools, list)
                # Verify the config was normalized
                assert hasattr(composer.config, 'source_servers')
                assert isinstance(composer.config.source_servers[0], ServerConfig)
    
    def test_normalize_config_dict_is_used_by_composer(self):
        """RED: Test composer constructor uses config normalization."""
        # Given: Raw dict config
        raw_config = {
            'domain': 'test',
            'model': 'test',
            'source_servers': [
                {
                    'name': 'test_server',
                    'command': 'test',
                    'cwd_env': 'TEST_PATH'
                }
            ]
        }
        
        # When: Create composer
        composer = GenericMCPServerComposer(raw_config)
        
        # Then: Config should be normalized to AggregatorConfig
        from config import AggregatorConfig
        assert isinstance(composer.config, AggregatorConfig)
        assert len(composer.config.source_servers) == 1
        assert isinstance(composer.config.source_servers[0], ServerConfig)
        assert composer.config.source_servers[0].name == 'test_server'
    
    @pytest.mark.asyncio
    async def test_composer_call_tool_with_normalized_config(self):
        """RED: Test call_tool works with normalized config objects."""
        # Given: Raw config that will be normalized
        raw_config = {
            'source_servers': [
                {
                    'name': 'test_server',
                    'command': 'python',
                    'args': ['-m', 'server'],
                    'cwd_env': 'TEST_PATH',
                    'enabled': True
                }
            ]
        }
        
        with patch.dict(os.environ, {'TEST_PATH': '/tmp/test'}):
            composer = GenericMCPServerComposer(raw_config)
            
            # Mock tool discovery and execution
            mock_tool = Mock()
            mock_tool.run_async = AsyncMock(return_value="tool_result")
            
            with patch.object(composer.discovery_engine, '_discover_server_tools') as mock_discover:
                mock_discover.return_value = {'test_tool': mock_tool}
                
                # When: Call tool using normalized config
                result = await composer.call_tool('test_tool', {'param': 'value'})
                
                # Then: Should execute successfully with ServerConfig objects
                assert result == "tool_result"
                mock_tool.run_async.assert_called_once_with(
                    args={'param': 'value'},
                    tool_context=None
                )
                
                # Verify the ServerConfig was passed to discovery
                called_server_config = mock_discover.call_args[0][0]
                assert isinstance(called_server_config, ServerConfig)
                assert called_server_config.name == 'test_server'