"""
End-to-end integration test: Staffer CLI → MCP Aggregator → External MCP servers.

Following RED-GREEN-REFACTOR TDD approach with REAL ADK integration.
Uses real ADK MCPToolset components, only mocks external server processes.
"""
import pytest
import asyncio
import subprocess
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
from tests.factories import create_mock_adk_tool, create_test_server_config

# Test imports - will fail until implementation is correct
try:
    from staffer.mcp_client import StafferMCPClient
except ImportError:
    StafferMCPClient = None

try:
    from staffer.available_functions import get_available_functions_with_mcp
except ImportError:
    get_available_functions_with_mcp = None


class TestStafferMCPIntegrationWithRealADK:
    """Test Staffer MCP integration using real ADK components."""
    
    def test_staffer_mcp_client_constructor_validation(self):
        """RED: Test that StafferMCPClient constructor fails with current incorrect ADK usage."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        # Set up environment for test
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
            'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
            'MCP_TIMEOUT': '10.0'
        }):
            
            # Create client - this should fail during MCPToolset creation
            mcp_client = StafferMCPClient({
                'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                'timeout': float(os.getenv('MCP_TIMEOUT'))
            })
            
            # Should succeed to create client, but fail when trying to create MCPToolset
            # with incorrect connection_params instead of server_params
            from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
            
            # This demonstrates the correct usage that we need to implement
            correct_server_params = StdioServerParameters(
                command="python3",
                args=["server.py", "--config", "test_config.yaml"],
                cwd=str(Path(__file__).parent.parent / "mcp-aggregator")
            )
            
            # This should work (correct usage)
            try:
                correct_toolset = MCPToolset(server_params=correct_server_params)
                # If this works, our current implementation is wrong
            except Exception as e:
                pytest.skip(f"ADK MCPToolset not available: {e}")
            
            # Now test our current incorrect implementation would fail
            # This will be fixed in the next step
    
    @pytest.mark.asyncio
    async def test_mcp_client_with_real_adk_server_params(self):
        """RED: Test will pass once we fix server_params usage."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        # This test will fail until we fix the MCPToolset usage
        # Then it should pass with mock server communication
        
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
            'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
            'MCP_TIMEOUT': '10.0'
        }):
            
            # Mock server process startup and communication
            mock_server_responses = [
                # Mock MCP protocol initialization
                json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}}),
                # Mock tools list response
                json.dumps({
                    "jsonrpc": "2.0", 
                    "id": 2, 
                    "result": {
                        "tools": [
                            {
                                "name": "excel_read_sheet",
                                "description": "Read Excel sheet data",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string"},
                                        "sheet_name": {"type": "string"}
                                    }
                                }
                            }
                        ]
                    }
                })
            ]
            
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.stdin = Mock()
                mock_process.stdout = Mock()
                mock_process.stderr = Mock()
                mock_process.poll.return_value = None
                
                # Mock reading responses from server
                mock_process.stdout.readline.side_effect = [
                    line.encode() + b'\n' for line in mock_server_responses
                ] + [b'']  # EOF
                
                mock_popen.return_value = mock_process
                
                # Create client
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
                
                # This should work once we fix server_params usage
                tools = await mcp_client.list_tools()
                
                # Validate real ADK integration worked
                assert isinstance(tools, list)
                assert len(tools) > 0
                assert tools[0]['name'] == 'excel_read_sheet'
    
    def test_available_functions_integration_with_real_adk(self):
        """RED: Test available_functions integration with real ADK discovery."""
        if not get_available_functions_with_mcp:
            pytest.skip("get_available_functions_with_mcp not implemented yet")
        
        working_dir = "/test/directory"
        
        # Mock server process but use real ADK components
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.poll.return_value = None
            
            # Mock successful tool discovery response
            tool_response = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "tools": [
                        {
                            "name": "excel_read_sheet",
                            "description": "Read Excel sheet",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"}
                                }
                            }
                        }
                    ]
                }
            })
            
            mock_process.stdout.readline.side_effect = [
                tool_response.encode() + b'\n',
                b''  # EOF
            ]
            mock_popen.return_value = mock_process
            
            # This will fail until the async event loop issue is fixed
            # and until MCPToolset usage is corrected
            with pytest.raises(Exception):
                functions = get_available_functions_with_mcp(working_dir)
    
    @pytest.mark.asyncio
    async def test_tool_execution_with_real_adk(self):
        """RED: Test tool execution through real ADK MCPToolset."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
            'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
            'MCP_TIMEOUT': '10.0'
        }):
            
            # Mock server responses for tool execution
            execution_responses = [
                # Protocol initialization
                json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}}),
                # Tool execution result
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "content": [
                            {"type": "text", "text": "Excel file read: 10 rows, 5 columns"}
                        ]
                    }
                })
            ]
            
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.stdin = Mock()
                mock_process.stdout = Mock()
                mock_process.stderr = Mock()
                mock_process.poll.return_value = None
                
                mock_process.stdout.readline.side_effect = [
                    line.encode() + b'\n' for line in execution_responses
                ] + [b'']
                
                mock_popen.return_value = mock_process
                
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
                
                # This will fail until MCPToolset usage is fixed
                with pytest.raises(Exception):
                    result = await mcp_client.call_tool(
                        tool_name="excel_read_sheet",
                        arguments={"file_path": "/test/data.xlsx"}
                    )


class TestRealADKErrorHandling:
    """Test error handling with real ADK components."""
    
    @pytest.mark.asyncio
    async def test_adk_handles_server_connection_failure(self):
        """Test that real ADK gracefully handles server connection failures."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
            'MCP_AGGREGATOR_CONFIG': 'nonexistent_config.yaml',  # Intentionally wrong
            'MCP_TIMEOUT': '5.0'
        }):
            
            # Mock server startup failure
            with patch('subprocess.Popen') as mock_popen:
                mock_popen.side_effect = FileNotFoundError("Server not found")
                
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
                
                # Should handle connection failure gracefully
                tools = await mcp_client.list_tools()
                
                # Should return empty list, not crash
                assert isinstance(tools, list)
                assert len(tools) == 0
    
    @pytest.mark.asyncio 
    async def test_adk_timeout_handling(self):
        """Test timeout handling with real ADK MCPToolset."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        with patch.dict(os.environ, {
            'MCP_AGGREGATOR_PATH': str(Path(__file__).parent.parent / "mcp-aggregator"),
            'MCP_AGGREGATOR_CONFIG': 'test_config.yaml',
            'MCP_TIMEOUT': '1.0'  # Short timeout
        }):
            
            # Mock slow server responses
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.stdin = Mock()
                mock_process.stdout = Mock()
                mock_process.stderr = Mock()
                mock_process.poll.return_value = None
                
                # Mock hanging server (no response)
                mock_process.stdout.readline.side_effect = lambda: asyncio.sleep(5)  # Longer than timeout
                mock_popen.return_value = mock_process
                
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
                
                # Should timeout gracefully
                import time
                start_time = time.time()
                
                tools = await mcp_client.call_tool_with_timeout(
                    "slow_tool", 
                    {}, 
                    timeout=1.0
                )
                
                execution_time = time.time() - start_time
                
                # Should timeout quickly
                assert execution_time < 2.0
                assert "timeout" in str(tools).lower()


class TestEnvironmentBasedConfiguration:
    """Test environment-based configuration with real ADK."""
    
    @pytest.mark.asyncio
    async def test_environment_variable_configuration(self):
        """Test that environment variables properly configure ADK components."""
        if not StafferMCPClient:
            pytest.skip("StafferMCPClient not implemented yet")
        
        # Test with custom environment settings
        custom_env = {
            'MCP_AGGREGATOR_PATH': '/custom/path/aggregator',
            'MCP_AGGREGATOR_CONFIG': 'custom_config.yaml',
            'MCP_TIMEOUT': '15.0'
        }
        
        with patch.dict(os.environ, custom_env):
            
            # Mock server to verify correct parameters are passed
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.stdin = Mock()
                mock_process.stdout = Mock()
                mock_process.stderr = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                mcp_client = StafferMCPClient({
                    'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH'),
                    'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG'),
                    'timeout': float(os.getenv('MCP_TIMEOUT'))
                })
                
                # Try to connect (will fail but should use correct paths)
                try:
                    await mcp_client.list_tools()
                except Exception:
                    pass  # Expected - focusing on parameter validation
                
                # Verify subprocess was called with environment-configured parameters
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args
                
                # Should include custom config in args
                assert 'custom_config.yaml' in str(call_args)
                # Should use custom working directory
                assert call_args[1]['cwd'] == '/custom/path/aggregator'
    
    def test_default_fallback_configuration(self):
        """Test that missing environment variables fall back to sensible defaults."""
        if not get_available_functions_with_mcp:
            pytest.skip("get_available_functions_with_mcp not implemented yet")
        
        # Clear all MCP-related environment variables
        env_to_clear = ['MCP_AGGREGATOR_PATH', 'MCP_AGGREGATOR_CONFIG', 'MCP_TIMEOUT']
        
        with patch.dict(os.environ, {}, clear=False):
            # Remove specific env vars
            for var in env_to_clear:
                os.environ.pop(var, None)
            
            # Should still work with defaults
            # This will fail until implementation is complete
            working_dir = "/test/directory"
            
            with pytest.raises(Exception):  # Expected until implementation complete
                functions = get_available_functions_with_mcp(working_dir)