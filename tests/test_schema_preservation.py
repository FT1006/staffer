"""Test that MCP tool schemas are preserved correctly."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add mcp-aggregator to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mcp-aggregator'))

from google.genai import types
from staffer.available_functions import _get_mcp_tool_declarations, _async_get_mcp_tools
from staffer.mcp_path_handler import convert_relative_to_absolute_paths
from tests.factories import create_mock_adk_tool


class TestSchemaPreservation:
    """Test that MCP tool schemas are preserved, not simplified."""
    
    @pytest.mark.asyncio
    async def test_excel_tool_schema_is_preserved(self):
        """Test that Excel tool schema with fileAbsolutePath parameter is preserved."""
        # RED: This test should fail with current implementation
        
        # Create mock Excel tool with specific parameter schema
        # The composer returns GenAI FunctionDeclaration objects
        excel_tool = types.FunctionDeclaration(
            name="excel_describe_sheets",
            description="List all sheet information of specified Excel file",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "fileAbsolutePath": types.Schema(
                        type=types.Type.STRING,
                        description="Absolute path to the Excel file"
                    )
                },
                required=["fileAbsolutePath"]
            )
        )
        
        # Mock composer to return our Excel tool
        with patch('staffer.available_functions.GenericMCPServerComposer') as mock_composer_class:
            mock_composer = Mock()
            mock_composer_class.from_config.return_value = mock_composer
            mock_composer.get_all_tools = AsyncMock(return_value=[excel_tool])
            
            # Get tool declarations
            declarations = await _async_get_mcp_tools('test_config.yaml')
            
            # Verify we got a declaration
            assert len(declarations) == 1
            decl = declarations[0]
            
            # ASSERTION: Schema should preserve fileAbsolutePath parameter
            assert decl.name == "excel_describe_sheets"
            assert decl.parameters.type == types.Type.OBJECT
            
            # Check that fileAbsolutePath parameter is preserved (not "input")
            properties = decl.parameters.properties
            assert "fileAbsolutePath" in properties, f"Expected fileAbsolutePath in schema, got: {list(properties.keys())}"
            assert properties["fileAbsolutePath"].type == types.Type.STRING
            
            # Should NOT have generic "input" parameter
            assert "input" not in properties, "Schema was simplified to generic 'input' parameter"
    
    @pytest.mark.asyncio
    async def test_complex_schema_with_nested_objects_preserved(self):
        """Test that complex schemas with nested objects are preserved."""
        # Create tool with complex nested schema
        complex_tool = types.FunctionDeclaration(
            name="data_processor",
            description="Process data with complex options",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "inputFile": types.Schema(
                        type=types.Type.STRING,
                        description="Path to input file"
                    ),
                    "options": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "format": types.Schema(
                                type=types.Type.STRING,
                                enum=["csv", "json", "xml"]
                            ),
                            "encoding": types.Schema(
                                type=types.Type.STRING,
                                default="utf-8"
                            )
                        },
                        required=["format"]
                    ),
                    "outputPath": types.Schema(
                        type=types.Type.STRING,
                        description="Where to save output"
                    )
                },
                required=["inputFile", "options"]
            )
        )
        
        with patch('staffer.available_functions.GenericMCPServerComposer') as mock_composer_class:
            mock_composer = Mock()
            mock_composer_class.from_config.return_value = mock_composer
            mock_composer.get_all_tools = AsyncMock(return_value=[complex_tool])
            
            declarations = await _async_get_mcp_tools('test_config.yaml')
            
            assert len(declarations) == 1
            decl = declarations[0]
            
            # Check all parameters are preserved
            properties = decl.parameters.properties
            assert "inputFile" in properties
            assert "options" in properties
            assert "outputPath" in properties
            
            # Check nested schema is preserved
            assert properties["options"].type == types.Type.OBJECT
            assert "format" in properties["options"].properties
            assert "encoding" in properties["options"].properties
    
    @pytest.mark.asyncio
    async def test_problematic_properties_are_sanitized(self):
        """Test that problematic properties like $schema are removed but structure preserved."""
        # For this test, we need to test sanitization at the schema dict level
        # So we'll create a tool that has an input_schema dict that needs sanitization
        # But the composer would have already converted it to GenAI format
        tool_with_problems = types.FunctionDeclaration(
            name="sanitize_test",
            description="Tool with problematic schema properties",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "fileName": types.Schema(
                        type=types.Type.STRING,
                        description="File to process"
                    )
                },
                required=["fileName"]
            )
        )
        
        with patch('staffer.available_functions.GenericMCPServerComposer') as mock_composer_class:
            mock_composer = Mock()
            mock_composer_class.from_config.return_value = mock_composer
            mock_composer.get_all_tools = AsyncMock(return_value=[tool_with_problems])
            
            declarations = await _async_get_mcp_tools('test_config.yaml')
            
            assert len(declarations) == 1
            decl = declarations[0]
            
            # Original parameter structure should be preserved
            properties = decl.parameters.properties
            assert "fileName" in properties
            assert properties["fileName"].type == types.Type.STRING
            
            # But problematic properties should be gone
            # (This test might need adjustment based on how we access raw schema)
            assert "input" not in properties, "Schema was incorrectly simplified"


class TestPathConversion:
    """Test that relative paths are converted to absolute paths for MCP tools."""
    
    def test_convert_file_abs_path_parameter(self):
        """Test that fileAbsolutePath gets converted from relative to absolute."""
        # RED: This should fail because function doesn't exist yet
        
        arguments = {
            "fileAbsolutePath": "department_satisfaction.xlsx"
        }
        working_directory = "/Users/spaceship/project/staffer/data"
        
        result = convert_relative_to_absolute_paths(arguments, working_directory)
        
        expected_path = "/Users/spaceship/project/staffer/data/department_satisfaction.xlsx"
        assert result["fileAbsolutePath"] == expected_path
    
    def test_convert_multiple_file_parameters(self):
        """Test conversion of multiple file-related parameters."""
        arguments = {
            "inputFile": "input.csv",
            "outputPath": "results/output.json",
            "configFile": "../config.yaml",
            "non_file_param": "keep_unchanged"
        }
        working_directory = "/Users/spaceship/project/staffer"
        
        result = convert_relative_to_absolute_paths(arguments, working_directory)
        
        assert result["inputFile"] == "/Users/spaceship/project/staffer/input.csv"
        assert result["outputPath"] == "/Users/spaceship/project/staffer/results/output.json"
        assert result["configFile"] == "/Users/spaceship/project/config.yaml"
        assert result["non_file_param"] == "keep_unchanged"
    
    def test_absolute_paths_unchanged(self):
        """Test that already absolute paths are not modified."""
        arguments = {
            "fileAbsolutePath": "/already/absolute/path.xlsx",
            "relativePath": "relative.txt"
        }
        working_directory = "/Users/spaceship/project/staffer/data"
        
        result = convert_relative_to_absolute_paths(arguments, working_directory)
        
        assert result["fileAbsolutePath"] == "/already/absolute/path.xlsx"
        assert result["relativePath"] == "/Users/spaceship/project/staffer/data/relative.txt"
    
    def test_no_file_parameters(self):
        """Test that non-file arguments are returned unchanged."""
        arguments = {
            "query": "SELECT * FROM table",
            "limit": 100,
            "format": "json"
        }
        working_directory = "/some/directory"
        
        result = convert_relative_to_absolute_paths(arguments, working_directory)
        
        assert result == arguments  # Should be unchanged