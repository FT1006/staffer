"""Test GenAI service layer for MCP tool integration."""
import pytest
import os
from adk_to_genai import GenAIToolService


class TestGenAIToolService:
    """Test the GenAI service layer that handles all MCP→GenAI concerns."""
    
    @pytest.mark.asyncio
    async def test_service_factory_method_loads_config(self):
        """Test that service can be created from config using factory method."""
        # Use factory method (new interface)
        service = GenAIToolService.from_config("test_config.yaml")
        
        # Should have composer initialized
        assert service.composer is not None
    
    @pytest.mark.asyncio
    async def test_get_tool_declarations_with_real_config(self):
        """Test that service returns tools using real configuration."""
        service = GenAIToolService.from_config("test_config.yaml")
        
        declarations = await service.get_tool_declarations()
        
        # Should return list of function declarations
        assert isinstance(declarations, list)
        # With test config, should get some tools (might be 0 if no servers available)
        print(f"Found {len(declarations)} tool declarations")
        for decl in declarations:
            assert hasattr(decl, 'name')
            assert hasattr(decl, 'description')
            print(f"  - {decl.name}: {decl.description}")
    
    @pytest.mark.asyncio 
    async def test_path_resolution_functionality(self):
        """Test that service handles path resolution correctly."""
        service = GenAIToolService()
        
        # Test path preparation directly (method renamed)
        working_dir = "/test/working/dir"
        arguments = {
            "file_path": "relative/file.txt",
            "output_path": "/absolute/path.txt",
            "other_param": "not_a_path"
        }
        
        prepared = service._prepare_genai_arguments(arguments, working_dir)
        
        # Should convert relative to absolute
        assert prepared["file_path"] == "/test/working/dir/relative/file.txt"
        # Should keep absolute paths unchanged
        assert prepared["output_path"] == "/absolute/path.txt"
        # Should not modify non-path parameters
        assert prepared["other_param"] == "not_a_path"
    
    def test_service_interface_completeness(self):
        """Test that service provides complete interface for Staffer."""
        service = GenAIToolService()
        
        # Service should have these methods to replace Staffer's MCP code
        assert hasattr(service, 'get_tool_declarations')
        assert hasattr(service, 'execute_tool')
        assert hasattr(service, 'from_config')  # Class method
        
        # Service should be callable
        assert callable(service.get_tool_declarations)
        assert callable(service.execute_tool)
        assert callable(GenAIToolService.from_config)  # Class method