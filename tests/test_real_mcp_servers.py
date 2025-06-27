"""Test with real Excel and Quick Data MCP servers."""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from staffer.available_functions import call_function, get_available_functions
from tests.factories import function_call


class TestRealMCPServers:
    """Test with real Excel and Quick Data MCP servers."""
    
    def test_mcp_integration_with_real_config(self):
        """Test MCP integration works with real server config."""
        # Set environment for real MCP servers
        original_config = os.environ.get('MCP_CONFIG_PATH')
        
        # Use real servers config
        test_config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'mcp-aggregator', 'real_servers_config.yaml'
        )
        os.environ['MCP_CONFIG_PATH'] = test_config_path
        
        try:
            # Get available functions - should include built-ins even if MCP fails
            functions = get_available_functions("/test/dir")
            
            # Extract function names
            function_names = [decl.name for decl in functions.function_declarations]
            
            # Should always have built-in functions
            assert "get_files_info" in function_names
            assert "get_file_content" in function_names
            assert "write_file" in function_names
            assert "run_python_file" in function_names
            assert "get_working_directory" in function_names
            
            print(f"Total functions available: {len(function_names)}")
            print(f"Functions: {function_names}")
            
            # Test calling a built-in function still works
            func_call = function_call("get_working_directory", {})
            result = call_function(func_call.parts[0].function_call, "/test/dir")
            
            # Verify built-in function executed successfully
            assert result.role == "tool"
            assert result.parts[0].function_response.name == "get_working_directory"
            assert "result" in result.parts[0].function_response.response
            
            # Check if any MCP tools were discovered
            builtin_names = {"get_files_info", "get_file_content", "write_file", 
                           "run_python_file", "get_working_directory"}
            mcp_tools = [name for name in function_names if name not in builtin_names]
            
            if mcp_tools:
                print(f"MCP tools discovered: {mcp_tools}")
                # Test calling an MCP tool if available
                test_tool = mcp_tools[0]
                func_call = function_call(test_tool, {})
                result = call_function(func_call.parts[0].function_call, "/test/dir")
                
                # Should get a response (success or error both valid)
                assert result.role == "tool"
                assert result.parts[0].function_response.name.lower() == test_tool.lower()
                response = result.parts[0].function_response.response
                assert "result" in response or "error" in response
                print(f"MCP tool '{test_tool}' response: {response}")
            else:
                print("No MCP tools discovered (servers may not be available)")
                
        finally:
            # Restore environment
            if original_config is not None:
                os.environ['MCP_CONFIG_PATH'] = original_config
            elif 'MCP_CONFIG_PATH' in os.environ:
                del os.environ['MCP_CONFIG_PATH']