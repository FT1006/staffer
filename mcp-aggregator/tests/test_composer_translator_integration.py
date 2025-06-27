"""RED tests for composer translator integration - should fail until implementation."""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from tests.factories import adk_tool

# These imports will test proper separation
try:
    from composer import GenericMCPServerComposer
except ImportError:
    GenericMCPServerComposer = None

try:
    from adk_to_genai import convert_adk_tool_to_genai
except ImportError:
    convert_adk_tool_to_genai = None


class TestComposerTranslatorIntegration:
    """RED tests for composer using translator to convert ADK tools - should fail first."""
    
    @pytest.mark.asyncio
    async def test_composer_converts_adk_tools_to_genai_format(self):
        """Test composer converts ADK tools to GenAI format using translator - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Composer with ADK tools from server
        config = {
            'source_servers': [
                {'name': 'test_server', 'priority': 1}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Use factory for real ADK tools instead of mocks
        test_adk_tool = adk_tool("test_function", "Test function", {
            'type': 'object',
            'properties': {
                'param': {'type': 'string'}
            }
        })
        
        # When: Getting all tools with translator conversion
        with patch.object(composer, '_discover_tools_from_server') as mock_discover, \
             patch.object(composer, '_convert_adk_tools_to_genai') as mock_convert:
            
            mock_discover.return_value = [test_adk_tool]
            mock_convert.return_value = [test_adk_tool]  # Converted tool
            
            result_tools = await composer.get_all_tools()
        
        # Then: Should call conversion with ADK tools
        mock_convert.assert_called_once_with([test_adk_tool])
        assert len(result_tools) == 1
    
    @pytest.mark.asyncio
    async def test_composer_handles_mixed_tool_types(self):
        """Test composer handles both ADK FunctionTools and simple tools - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Mix of different tool types using factories
        config = {
            'source_servers': [
                {'name': 'mixed_server', 'priority': 1}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Use factory for consistent test tools
        adk_function_tool = adk_tool("adk_function", "ADK function", {
            'type': 'object',
            'properties': {'input': {'type': 'string'}}
        })
        
        simple_tool = Mock()
        simple_tool.name = "simple_tool"
        simple_tool.description = "Simple tool"
        # No input_schema attribute to distinguish from ADK tools
        
        mixed_tools = [adk_function_tool, simple_tool]
        
        # When: Converting mixed tools
        with patch.object(composer, '_discover_tools_from_server') as mock_discover, \
             patch.object(composer, '_convert_adk_tools_to_genai') as mock_convert:
            
            mock_discover.return_value = mixed_tools
            mock_convert.return_value = mixed_tools  # Return converted versions
            
            result_tools = await composer.get_all_tools()
        
        # Then: Should process all tool types
        mock_convert.assert_called_once_with(mixed_tools)
        assert len(result_tools) == 2
    
    def test_composer_has_adk_conversion_method(self):
        """Test composer has _convert_adk_tools_to_genai method - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Composer instance
        composer = GenericMCPServerComposer({})
        
        # Then: Should have conversion method
        assert hasattr(composer, '_convert_adk_tools_to_genai'), "Missing _convert_adk_tools_to_genai method"
        assert callable(getattr(composer, '_convert_adk_tools_to_genai')), "Method not callable"
    
    def test_convert_adk_tools_distinguishes_by_input_schema(self):
        """Test _convert_adk_tools_to_genai distinguishes tools by input_schema presence - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Tools with and without input_schema
        composer = GenericMCPServerComposer({})
        
        # Tool with input_schema (ADK FunctionTool)
        adk_function_tool = adk_tool("function_with_schema", "Has schema", {
            'type': 'object',
            'properties': {'param': {'type': 'string'}}
        })
        
        # Tool without input_schema (simple tool) - properly configure Mock
        simple_tool = Mock(spec=['name', 'description'])  # Only these attributes
        simple_tool.name = "no_schema_tool"
        simple_tool.description = "No schema"
        # Explicitly ensure no input_schema attribute
        if hasattr(simple_tool, 'input_schema'):
            delattr(simple_tool, 'input_schema')
        
        tools = [adk_function_tool, simple_tool]
        
        # When: Converting tools
        with patch('composer.convert_adk_tool_to_genai') as mock_translator, \
             patch.object(composer, '_create_flexible_declaration') as mock_flexible:
            
            mock_translator.return_value = adk_function_tool
            mock_flexible.return_value = simple_tool
            
            result = composer._convert_adk_tools_to_genai(tools)
        
        # Then: Should route based on input_schema presence
        mock_translator.assert_called_once_with(adk_function_tool)
        mock_flexible.assert_called_once_with(simple_tool)
        assert len(result) == 2
    
    def test_convert_adk_tools_continues_on_conversion_failure(self):
        """Test _convert_adk_tools_to_genai continues when individual conversions fail - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Multiple tools with one failing conversion
        composer = GenericMCPServerComposer({})
        
        working_tool = adk_tool("working_tool", "Works fine", {
            'type': 'object',
            'properties': {'param': {'type': 'string'}}
        })
        
        failing_tool = adk_tool("failing_tool", "Will fail", {
            'type': 'object',
            'properties': {'bad_param': {'type': 'invalid'}}
        })
        
        tools = [working_tool, failing_tool]
        
        # When: Converting with one failure
        with patch('composer.convert_adk_tool_to_genai') as mock_translator:
            mock_translator.side_effect = [
                working_tool,                    # First succeeds
                Exception("Schema conversion failed")  # Second fails
            ]
            
            result = composer._convert_adk_tools_to_genai(tools)
        
        # Then: Should continue with successful conversions
        assert len(result) == 1
        assert result[0] == working_tool
        assert mock_translator.call_count == 2


class TestFlexibleDeclarationCreation:
    """RED tests for creating declarations for tools without schemas - should fail first."""
    
    def test_composer_has_flexible_declaration_method(self):
        """Test composer has _create_flexible_declaration method - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Composer instance
        composer = GenericMCPServerComposer({})
        
        # Then: Should have flexible declaration method
        assert hasattr(composer, '_create_flexible_declaration'), "Missing _create_flexible_declaration method"
        assert callable(getattr(composer, '_create_flexible_declaration')), "Method not callable"
    
    def test_flexible_declaration_uses_tool_attributes(self):
        """Test _create_flexible_declaration uses available tool attributes - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Tool with name and description
        composer = GenericMCPServerComposer({})
        tool = Mock()
        tool.name = "dynamic_tool"
        tool.description = "Dynamically created tool"
        
        # When: Creating flexible declaration
        with patch('composer.genai.protos.FunctionDeclaration') as mock_declaration:
            composer._create_flexible_declaration(tool)
        
        # Then: Should use tool's actual attributes
        mock_declaration.assert_called_once()
        call_kwargs = mock_declaration.call_args[1]
        assert call_kwargs['name'] == tool.name
        assert call_kwargs['description'] == tool.description
    
    def test_flexible_declaration_handles_missing_attributes_gracefully(self):
        """Test flexible declaration provides defaults for missing attributes - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Given: Tool with minimal attributes
        composer = GenericMCPServerComposer({})
        minimal_tool = Mock(spec=[])  # Mock with no attributes
        
        # When: Creating declaration
        with patch('composer.genai.protos.FunctionDeclaration') as mock_declaration:
            composer._create_flexible_declaration(minimal_tool)
        
        # Then: Should provide sensible defaults
        call_kwargs = mock_declaration.call_args[1]
        assert 'name' in call_kwargs
        assert 'description' in call_kwargs
        assert 'parameters' in call_kwargs


class TestProperImportStructure:
    """RED tests for correct import architecture - should fail first."""
    
    def test_adk_translator_available_as_separate_module(self):
        """Test adk_translator is available as independent module - should fail first."""
        # This tests that translator is properly moved to aggregator
        try:
            from adk_to_genai import convert_adk_tool_to_genai
            assert convert_adk_tool_to_genai is not None
            assert callable(convert_adk_tool_to_genai)
        except ImportError:
            pytest.fail("adk_translator should be available as separate module in aggregator")
    
    def test_composer_can_import_translator_function(self):
        """Test composer can import translator function - should fail first."""
        if not GenericMCPServerComposer:
            pytest.skip("GenericMCPServerComposer not implemented yet")
        
        # Test that composer module can access translator
        try:
            import composer
            # Should be able to access convert_adk_tool_to_genai through composer module
            assert hasattr(composer, 'convert_adk_tool_to_genai')
        except (ImportError, AttributeError):
            pytest.fail("Composer should import convert_adk_tool_to_genai from adk_translator")
    
    def test_translator_works_with_factory_tools(self):
        """Test translator works with tools created by factory - should fail first."""
        if not convert_adk_tool_to_genai:
            pytest.skip("convert_adk_tool_to_genai not available")
        
        # Given: Tool from factory
        test_tool = adk_tool("factory_test", "Test with factory", {
            'type': 'object',
            'properties': {
                'test_param': {'type': 'string'}
            }
        })
        
        # When: Converting with translator
        try:
            result = convert_adk_tool_to_genai(test_tool)
            # Should not raise exception with factory-created tools
            assert result is not None
        except Exception as e:
            pytest.fail(f"Translator should work with factory tools: {e}")