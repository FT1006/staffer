"""RED tests for composer pipeline validation - should fail until pipeline fixes."""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import google.generativeai as genai
from composer import GenericMCPServerComposer
from adk_translator import convert_adk_tool_to_genai
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from tests.factories import adk_tool


class TestComposerPipelineValidation:
    """RED tests for full composer pipeline: ADK → translator → GenAI → aggregation."""
    
    @pytest.mark.asyncio
    async def test_composer_pipeline_converts_real_adk_tools_to_genai(self):
        """Test full pipeline converts real ADK tools correctly - should fail first."""
        # Given: Composer with real ADK tools from multiple servers
        config = {
            'source_servers': [
                {'name': 'excel', 'priority': 1},
                {'name': 'analytics', 'priority': 2}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Create realistic ADK tools with complex schemas
        excel_tool = adk_tool("excel_read_sheet", "Read Excel sheet", {
            'type': 'object',
            'properties': {
                'file_path': {'type': 'string', 'description': 'Path to Excel file'},
                'sheet_name': {'type': 'string', 'description': 'Sheet name'},
                'range': {'type': 'string', 'description': 'Cell range'}
            },
            'required': ['file_path', 'sheet_name']
        })
        
        analytics_tool = adk_tool("load_dataset", "Load dataset", {
            'type': 'object',
            'properties': {
                'source_path': {'type': 'string', 'description': 'Dataset path'},
                'format': {'type': 'string', 'description': 'Data format'},
                'options': {
                    'type': 'object',
                    'properties': {
                        'header': {'type': 'boolean', 'default': True},
                        'encoding': {'type': 'string', 'default': 'utf-8'}
                    }
                }
            },
            'required': ['source_path', 'format']
        })
        
        # When: Processing through full composer pipeline
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.side_effect = [[excel_tool], [analytics_tool]]
            
            result_tools = await composer.get_all_tools()
        
        # Then: Should return properly converted GenAI tools
        assert len(result_tools) == 2
        
        # Validate that tools are GenAI FunctionDeclarations
        for tool in result_tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description') 
            assert hasattr(tool, 'parameters')
            assert tool.parameters.type == genai.protos.Type.OBJECT
        
        # Find specific tools and validate their conversion
        excel_genai = next(t for t in result_tools if t.name == "excel_read_sheet")
        assert excel_genai.description == "Read Excel sheet"
        assert 'file_path' in excel_genai.parameters.properties
        assert 'sheet_name' in excel_genai.parameters.properties
        assert set(excel_genai.parameters.required) == {'file_path', 'sheet_name'}
        
        analytics_genai = next(t for t in result_tools if t.name == "load_dataset")
        assert analytics_genai.description == "Load dataset"
        assert 'options' in analytics_genai.parameters.properties
        options_param = analytics_genai.parameters.properties['options']
        assert options_param.type == genai.protos.Type.OBJECT
        assert 'header' in options_param.properties
    
    @pytest.mark.asyncio
    async def test_composer_pipeline_handles_translation_failures_gracefully(self):
        """Test pipeline handles translation failures without breaking - should fail first."""
        # Given: Composer with tools that may fail translation
        config = {
            'source_servers': [
                {'name': 'working_server', 'priority': 1},
                {'name': 'problematic_server', 'priority': 2}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Working tool with valid schema
        working_tool = adk_tool("working_tool", "Works fine", {
            'type': 'object',
            'properties': {
                'param': {'type': 'string'}
            }
        })
        
        # Problematic tool that will fail translation
        class ProblematicTool:
            def __init__(self):
                self.name = "problematic_tool"
                self.description = "Will fail translation"
            
            def input_schema(self):
                # Return invalid schema that breaks translator
                return {
                    'type': 'invalid_type',
                    'properties': None  # Invalid structure
                }
        
        problematic_tool = ProblematicTool()
        
        # When: Processing through pipeline with translation failure
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.side_effect = [[working_tool], [problematic_tool]]
            
            result_tools = await composer.get_all_tools()
        
        # Then: Should continue with working tools despite failures
        assert len(result_tools) >= 1  # At least the working tool
        
        # Should have the working tool successfully converted
        working_genai = next((t for t in result_tools if t.name == "working_tool"), None)
        assert working_genai is not None
        assert working_genai.description == "Works fine"
    
    @pytest.mark.asyncio
    async def test_composer_pipeline_preserves_priority_during_conversion(self):
        """Test pipeline maintains priority-based conflict resolution - should fail first."""
        # Given: Two tools with same name but different priorities
        config = {
            'source_servers': [
                {'name': 'low_priority', 'priority': 1},
                {'name': 'high_priority', 'priority': 2}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Same tool name, different implementations
        low_priority_tool = adk_tool("shared_tool", "Low priority version", {
            'type': 'object',
            'properties': {
                'basic_param': {'type': 'string'}
            }
        })
        
        high_priority_tool = adk_tool("shared_tool", "High priority version", {
            'type': 'object',
            'properties': {
                'advanced_param': {'type': 'string'},
                'config': {
                    'type': 'object',
                    'properties': {
                        'enabled': {'type': 'boolean'}
                    }
                }
            }
        })
        
        # When: Processing conflicting tools through pipeline
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.side_effect = [[low_priority_tool], [high_priority_tool]]
            
            result_tools = await composer.get_all_tools()
        
        # Then: Should resolve conflict using priority
        assert len(result_tools) == 1
        resolved_tool = result_tools[0]
        
        # Should be the high priority version
        assert resolved_tool.name == "shared_tool"
        assert resolved_tool.description == "High priority version"
        assert 'advanced_param' in resolved_tool.parameters.properties
        assert 'config' in resolved_tool.parameters.properties
    
    @pytest.mark.asyncio
    async def test_composer_pipeline_handles_array_tools_correctly(self):
        """Test pipeline correctly processes tools with array parameters - should fail first."""
        # Given: Tool with complex array schema
        config = {
            'source_servers': [
                {'name': 'array_server', 'priority': 1}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        array_tool = adk_tool("process_batch", "Process batch of items", {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'data': {'type': 'string'},
                            'metadata': {
                                'type': 'object',
                                'properties': {
                                    'tags': {
                                        'type': 'array',
                                        'items': {'type': 'string'}
                                    }
                                }
                            }
                        },
                        'required': ['id', 'data']
                    }
                },
                'options': {
                    'type': 'object',
                    'properties': {
                        'parallel': {'type': 'boolean', 'default': False}
                    }
                }
            },
            'required': ['items']
        })
        
        # When: Processing array tool through pipeline
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.return_value = [array_tool]
            
            result_tools = await composer.get_all_tools()
        
        # Then: Should correctly convert complex array schema
        assert len(result_tools) == 1
        converted_tool = result_tools[0]
        
        assert converted_tool.name == "process_batch"
        params = converted_tool.parameters
        
        # Validate array structure is preserved
        items_param = params.properties['items']
        assert items_param.type == genai.protos.Type.ARRAY
        assert items_param.items.type == genai.protos.Type.OBJECT
        
        # Validate nested array within object
        item_metadata = items_param.items.properties['metadata']
        tags_param = item_metadata.properties['tags']
        assert tags_param.type == genai.protos.Type.ARRAY
        assert tags_param.items.type == genai.protos.Type.STRING


class TestComposerPipelinePerformance:
    """RED tests for composer pipeline performance characteristics - should fail first."""
    
    @pytest.mark.asyncio
    async def test_composer_pipeline_handles_many_tools_efficiently(self):
        """Test pipeline performs well with many tools - should fail first."""
        # Given: Large number of tools from multiple servers
        config = {
            'source_servers': [
                {'name': f'server_{i}', 'priority': i} 
                for i in range(5)  # 5 servers
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Create 10 tools per server (50 total)
        def create_tools_for_server(server_id):
            return [
                adk_tool(f"tool_{server_id}_{i}", f"Tool {i} from server {server_id}", {
                    'type': 'object',
                    'properties': {
                        'param1': {'type': 'string'},
                        'param2': {'type': 'number'},
                        'config': {
                            'type': 'object',
                            'properties': {
                                'enabled': {'type': 'boolean'}
                            }
                        }
                    }
                })
                for i in range(10)
            ]
        
        # When: Processing many tools through pipeline
        with patch.object(composer, '_discover_tools_from_server') as mock_discover:
            mock_discover.side_effect = [
                create_tools_for_server(i) for i in range(5)
            ]
            
            import time
            start_time = time.time()
            result_tools = await composer.get_all_tools()
            end_time = time.time()
        
        # Then: Should complete in reasonable time
        processing_time = end_time - start_time
        assert processing_time < 5.0, f"Pipeline took {processing_time:.2f}s, should be < 5s"
        
        # Should have all tools converted
        assert len(result_tools) == 50
        
        # All tools should be properly converted GenAI format
        for tool in result_tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'parameters')
            assert tool.parameters.type == genai.protos.Type.OBJECT
    
    @pytest.mark.asyncio
    async def test_composer_pipeline_concurrent_server_processing(self):
        """Test pipeline processes servers concurrently for performance - should fail first."""
        # Given: Multiple servers with simulated network delays
        config = {
            'source_servers': [
                {'name': 'slow_server_1', 'priority': 1},
                {'name': 'slow_server_2', 'priority': 2},
                {'name': 'slow_server_3', 'priority': 3}
            ]
        }
        composer = GenericMCPServerComposer(config)
        
        # Simulate slow tool discovery
        async def slow_discovery(server_config):
            await asyncio.sleep(0.5)  # 500ms delay per server
            return [adk_tool(f"tool_from_{server_config['name']}", "Slow tool", {
                'type': 'object',
                'properties': {'param': {'type': 'string'}}
            })]
        
        # When: Processing with concurrent discovery
        with patch.object(composer, '_discover_tools_from_server', side_effect=slow_discovery):
            start_time = time.time()
            result_tools = await composer.get_all_tools()
            end_time = time.time()
        
        # Then: Should complete faster than sequential processing
        processing_time = end_time - start_time
        # If sequential: 3 * 0.5s = 1.5s+
        # If concurrent: ~0.5s (plus overhead)
        assert processing_time < 1.0, f"Concurrent processing took {processing_time:.2f}s, should be < 1s"
        
        assert len(result_tools) == 3