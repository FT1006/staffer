"""Test MCP tool integration in available_functions."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from staffer.available_functions import get_available_functions
from tests.factories import create_mock_adk_tool, create_mock_mcp_tool


class TestMCPIntegration:
    """Test integration of MCP tools in available_functions."""
    
    def test_get_available_functions_includes_mcp_tools(self):
        """Test that get_available_functions includes both built-in and MCP tools."""
        # Create mock MCP tools using factories
        mock_excel_tool = create_mock_adk_tool("analyze_excel", "Analyze Excel files")
        mock_web_tool = create_mock_mcp_tool("fetch_webpage", "Fetch webpage content")
        
        # Mock the composer from mcp-aggregator
        with patch('staffer.available_functions.GenericMCPServerComposer') as MockComposer:
            mock_composer = Mock()
            MockComposer.from_config.return_value = mock_composer
            mock_composer.get_all_tools = AsyncMock(
                return_value=[mock_excel_tool, mock_web_tool]
            )
            
            # Mock the ADK to GenAI converter
            with patch('staffer.available_functions.HybridToolToGenAIConverter') as MockConverter:
                mock_converter = Mock()
                MockConverter.return_value = mock_converter
                mock_converter.convert_to_genai_tools.return_value = [
                    {
                        "name": "analyze_excel",
                        "description": "Analyze Excel files", 
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"}
                            },
                            "required": ["input"]
                        }
                    },
                    {
                        "name": "fetch_webpage",
                        "description": "Fetch webpage content",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
                
                # Get available functions - should include both built-in and MCP
                functions = get_available_functions("/test/dir")
                
                # Should return types.Tool with function declarations
                assert hasattr(functions, 'function_declarations')
                
                # Extract function names from declarations
                function_names = [decl.name for decl in functions.function_declarations]
                
                # Verify built-in functions are still present
                assert "get_files_info" in function_names
                assert "get_file_content" in function_names
                assert "write_file" in function_names
                
                # Verify MCP tools are now included
                assert "analyze_excel" in function_names
                assert "fetch_webpage" in function_names
                
                # Verify composer was used
                MockComposer.from_config.assert_called_once()
                mock_composer.get_all_tools.assert_called_once()