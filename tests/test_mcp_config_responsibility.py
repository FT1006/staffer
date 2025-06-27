"""RED tests to verify configuration decision responsibility between Staffer and MCP aggregator."""
import pytest
import os
from unittest.mock import patch, Mock

# Import the functions we need to test
try:
    from staffer.available_functions import _get_mcp_tool_declarations, get_available_functions
except ImportError:
    _get_mcp_tool_declarations = None
    get_available_functions = None


class TestMCPConfigurationResponsibility:
    """RED tests for configuration decision responsibility - should fail first."""
    
    def test_staffer_works_without_mcp_config_path(self):
        """Test Staffer works with only built-in functions when no MCP_CONFIG_PATH set - should fail first."""
        if not get_available_functions:
            pytest.skip("get_available_functions not available")
        
        # Clear any MCP config environment variable
        with patch.dict(os.environ, {}, clear=True):
            # Should work with only built-in functions
            tools = get_available_functions('.')
            
            # Should contain built-in functions (4-5 tools)
            assert len(tools.function_declarations) >= 4
            assert len(tools.function_declarations) <= 5
            
            # Should not attempt MCP integration when no config path provided
            builtin_names = [decl.name for decl in tools.function_declarations]
            expected_builtins = ["get_files_info", "get_file_content", "write_file", "run_python_file"]
            
            for builtin in expected_builtins:
                assert builtin in builtin_names
    
    def test_mcp_integration_only_when_config_path_provided(self):
        """Test MCP integration only activates when MCP_CONFIG_PATH is explicitly set - should fail first."""
        if not _get_mcp_tool_declarations:
            pytest.skip("_get_mcp_tool_declarations not available")
        
        # Test 1: No MCP_CONFIG_PATH - should return empty list (no MCP integration)
        with patch.dict(os.environ, {}, clear=True):
            tools = _get_mcp_tool_declarations()
            assert tools == []  # No MCP tools when no config provided
        
        # Test 2: MCP_CONFIG_PATH set - should attempt MCP integration
        with patch.dict(os.environ, {'MCP_CONFIG_PATH': '/custom/config.yaml'}):
            # Mock the MCP components to avoid actual file loading
            with patch('staffer.available_functions.GenericMCPServerComposer') as mock_composer_class:
                mock_composer = Mock()
                mock_composer_class.from_config.return_value = mock_composer
                
                # Should attempt to use the provided config path
                _get_mcp_tool_declarations()
                
                # Should call composer with the explicit config path
                mock_composer_class.from_config.assert_called_once_with('/custom/config.yaml')
    
    def test_staffer_does_not_assume_mcp_exists(self):
        """Test Staffer doesn't assume MCP aggregator exists or has default config - should fail first."""
        if not get_available_functions:
            pytest.skip("get_available_functions not available")
        
        # Should work even if MCP components are not available
        with patch('staffer.available_functions.GenericMCPServerComposer', None):
            with patch.dict(os.environ, {}, clear=True):
                tools = get_available_functions('.')
                
                # Should still work with built-in functions only
                assert len(tools.function_declarations) >= 4
                
                # Should contain built-in function names
                builtin_names = [decl.name for decl in tools.function_declarations]
                assert "get_files_info" in builtin_names
    
    def test_no_hardcoded_mcp_config_paths(self):
        """Test Staffer doesn't hardcode MCP configuration paths - should fail first."""
        import staffer.available_functions as af
        import inspect
        
        # Get the source code
        source = inspect.getsource(af._get_mcp_tool_declarations)
        
        # Should not contain hardcoded paths to MCP configuration
        assert 'production.yaml' not in source, "Hardcoded production.yaml path found"
        assert 'aggregation.yaml' not in source, "Hardcoded aggregation.yaml path found"
        assert 'mcp-aggregator' not in source, "Hardcoded mcp-aggregator path found"
        
        # Should only check environment variable, no fallback to hardcoded paths
        lines = source.split('\n')
        config_lines = [line for line in lines if 'config_path' in line and 'os.getenv' in line]
        
        for line in config_lines:
            # Should not have default fallback path
            assert 'os.path.join' not in line, f"Hardcoded path fallback found in: {line}"
    
    def test_mcp_aggregator_owns_its_default_config(self):
        """Test MCP aggregator owns its own default configuration decisions - should fail first."""
        # This test ensures the responsibility boundary is clear
        
        # Staffer should only know about MCP via environment variable
        # MCP aggregator should handle its own defaults internally
        
        # Import MCP aggregator components
        try:
            import sys
            import os
            
            # Add mcp-aggregator to path temporarily
            staffer_root = os.path.dirname(os.path.dirname(__file__))
            mcp_aggregator_path = os.path.join(staffer_root, 'mcp-aggregator')
            if mcp_aggregator_path not in sys.path:
                sys.path.insert(0, mcp_aggregator_path)
            
            from composer import GenericMCPServerComposer
            from config import load_config
            
            # MCP aggregator should have its own default in load_config
            # Check that load_config has a default parameter
            import inspect
            signature = inspect.signature(load_config)
            
            # Should have default config parameter
            assert 'config_path' in signature.parameters
            default_value = signature.parameters['config_path'].default
            
            # MCP aggregator can have its own default
            assert default_value is not None
            assert default_value != inspect.Parameter.empty
            
        except ImportError:
            # If MCP components not available, that's fine for this test
            pass


class TestConfigurationBoundaryClarity:
    """RED tests for clear configuration responsibility boundaries - should fail first."""
    
    def test_staffer_config_boundary(self):
        """Test Staffer's configuration boundary is clear - should fail first."""
        if not get_available_functions:
            pytest.skip("get_available_functions not available")
        
        # Staffer's responsibility: built-in functions + optional external integration
        # Should work in isolation without any external dependencies
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('staffer.available_functions.GenericMCPServerComposer', None):
                tools = get_available_functions('.')
                
                # Should be self-contained
                assert len(tools.function_declarations) >= 4
                
                # All tools should be built-in functions
                for decl in tools.function_declarations:
                    # Built-in functions have predictable names
                    assert any(builtin in decl.name for builtin in 
                             ['get_files_info', 'get_file_content', 'write_file', 'run_python_file', 'get_working_directory'])
    
    def test_mcp_config_boundary(self):
        """Test MCP aggregator's configuration boundary is clear - should fail first."""
        # MCP aggregator should handle its own configuration completely
        # Staffer should only provide a config path if explicitly requested via environment
        
        with patch.dict(os.environ, {'MCP_CONFIG_PATH': '/test/config.yaml'}):
            with patch('staffer.available_functions.GenericMCPServerComposer') as mock_composer_class:
                mock_composer = Mock()
                mock_composer_class.from_config.return_value = mock_composer
                mock_composer.get_all_tools.return_value = []
                
                # When MCP_CONFIG_PATH is set, should use exactly that path
                _get_mcp_tool_declarations()
                
                # Should not modify or interpret the path - just pass it through
                mock_composer_class.from_config.assert_called_once_with('/test/config.yaml')
                
    def test_no_shared_configuration_concerns(self):
        """Test no shared configuration concerns between Staffer and MCP - should fail first."""
        import staffer.available_functions as af
        import inspect
        
        # Get all functions in available_functions
        functions = [getattr(af, name) for name in dir(af) if callable(getattr(af, name))]
        
        for func in functions:
            if hasattr(func, '__name__') and func.__name__.startswith('_'):
                source = inspect.getsource(func)
                
                # Should not contain shared config logic
                assert 'default' not in source.lower() or 'config' not in source.lower() or \
                       not ('production.yaml' in source or 'aggregation.yaml' in source), \
                       f"Function {func.__name__} contains shared config concerns"