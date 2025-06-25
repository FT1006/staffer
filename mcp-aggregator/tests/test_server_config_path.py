"""
Test config path resolution for server.py.

Following RED-GREEN-REFACTOR TDD approach.
"""
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile
import os

from server import MCPAggregatorServer


class TestServerConfigPathResolution:
    """Test that server properly resolves config file paths."""
    
    def test_server_finds_relative_config_from_server_directory(self):
        """RED: Test that server finds config relative to server.py location."""
        # This should work when running from server directory
        config_path = "test_config.yaml"
        
        with patch('os.getenv', return_value="/test/path"):
            # This will fail until we fix path resolution
            server = MCPAggregatorServer(config_path=config_path)
            assert server.config is not None
    
    def test_server_handles_absolute_config_paths(self):
        """Test that server handles absolute config paths correctly."""
        config_path = Path(__file__).parent.parent / "test_config.yaml"
        
        with patch('os.getenv', return_value="/test/path"):
            server = MCPAggregatorServer(config_path=str(config_path))
            assert server.config is not None
    
    def test_server_provides_helpful_error_for_missing_config(self):
        """Test that server provides helpful error message for missing config."""
        with pytest.raises(FileNotFoundError) as exc_info:
            MCPAggregatorServer(config_path="nonexistent.yaml")
        
        # Should provide helpful error message
        assert "nonexistent.yaml" in str(exc_info.value)