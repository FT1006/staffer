"""
Tests for MCP aggregator server.py entry point.

Following RED-GREEN-REFACTOR TDD approach.
Uses factories for consistent test setup.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.factories import create_test_server_config
from server import MCPAggregatorServer, main


class TestMCPAggregatorServer:
    """Test MCP aggregator server entry point."""
    
    def test_server_class_exists(self):
        """Test that MCPAggregatorServer class exists."""
        assert MCPAggregatorServer is not None, "MCPAggregatorServer class should exist"
    
    def test_server_has_required_methods(self):
        """Test that server has required interface methods."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        # Mock environment variables for test config
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
            
        assert hasattr(server, 'start'), "Server should have start method"
        assert hasattr(server, 'stop'), "Server should have stop method"
        assert hasattr(server, 'get_tools'), "Server should have get_tools method"
    
    def test_server_loads_config_on_init(self):
        """Test that server loads configuration on initialization."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        # Mock environment variables for test config
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
        
        assert hasattr(server, 'config'), "Server should have config attribute"
        assert server.config is not None, "Server config should be loaded"
    
    @pytest.mark.asyncio
    async def test_server_get_tools_returns_list(self):
        """Test that get_tools returns list of GenAI tools."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        # Mock environment variables and composer
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
            
        # Mock composer to avoid actual MCP server calls
        with patch.object(server.composer, 'get_all_tools', return_value=[]):
            tools = await server.get_tools()
            
        assert isinstance(tools, list), "get_tools should return a list"


class TestMainFunction:
    """Test main entry point function."""
    
    def test_main_function_exists(self):
        """Test that main function exists."""
        assert main is not None, "main function should exist"
    
    def test_main_accepts_config_argument(self):
        """Test that main function accepts config path argument."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        with patch('sys.argv', ['server.py', '--config', str(config_path)]):
            with patch('os.getenv', return_value="/test/path"):
                with patch.object(MCPAggregatorServer, 'start') as mock_start:
                    main()
                    mock_start.assert_called_once()