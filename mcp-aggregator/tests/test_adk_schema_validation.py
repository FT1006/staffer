"""RED tests for comprehensive ADK schema validation - should fail until enhancements."""
import pytest
import google.generativeai as genai
from adk_to_genai import convert_adk_tool_to_genai
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from tests.factories import adk_tool


class TestComplexSchemaValidation:
    """RED tests for complex ADK schema conversion - should fail first."""
    
    def test_adk_to_genai_array_parameter(self):
        """Test converting ADK tool with array parameter - should fail first."""
        # Given: Simple ADK tool with array parameter - create directly
        from tests.factories import BaseTool
        
        class ArrayTool(BaseTool):
            def input_schema(self):
                return {
                    'type': 'object',
                    'properties': {
                        'items': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of items to process'
                        }
                    },
                    'required': ['items']
                }
        
        array_tool = ArrayTool(name="process_list", description="Process list of items")
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(array_tool)
        
        # Then: Should handle array type correctly
        assert genai_declaration.name == "process_list"
        params = genai_declaration.parameters
        assert params.type == genai.protos.Type.OBJECT
        
        items_param = params.properties['items']
        assert items_param.type == genai.protos.Type.ARRAY
        assert items_param.items.type == genai.protos.Type.STRING
        assert 'items' in params.required
    
    def test_adk_to_genai_nested_object_parameter(self):
        """Test converting ADK tool with nested object parameter - should fail first."""
        # Given: ADK tool with nested object
        nested_tool = adk_tool("create_user", "Create user with profile", {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'age': {'type': 'number'},
                        'profile': {
                            'type': 'object',
                            'properties': {
                                'bio': {'type': 'string'},
                                'active': {'type': 'boolean'}
                            },
                            'required': ['bio']
                        }
                    },
                    'required': ['name', 'profile']
                }
            },
            'required': ['user']
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(nested_tool)
        
        # Then: Should handle nested objects correctly
        assert genai_declaration.name == "create_user"
        params = genai_declaration.parameters
        
        user_param = params.properties['user']
        assert user_param.type == genai.protos.Type.OBJECT
        assert 'name' in user_param.required
        assert 'profile' in user_param.required
        
        profile_param = user_param.properties['profile']
        assert profile_param.type == genai.protos.Type.OBJECT
        assert 'bio' in profile_param.required
        assert profile_param.properties['active'].type == genai.protos.Type.BOOLEAN
    
    def test_adk_to_genai_boolean_parameter(self):
        """Test converting ADK tool with boolean parameter - should fail first."""
        # Given: ADK tool with boolean parameter
        boolean_tool = adk_tool("toggle_feature", "Toggle feature on/off", {
            'type': 'object',
            'properties': {
                'enabled': {
                    'type': 'boolean',
                    'description': 'Whether to enable the feature'
                },
                'force': {
                    'type': 'boolean',
                    'default': False
                }
            },
            'required': ['enabled']
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(boolean_tool)
        
        # Then: Should handle boolean type correctly
        params = genai_declaration.parameters
        enabled_param = params.properties['enabled']
        force_param = params.properties['force']
        
        assert enabled_param.type == genai.protos.Type.BOOLEAN
        assert force_param.type == genai.protos.Type.BOOLEAN
        assert 'enabled' in params.required
        assert 'force' not in params.required
    
    def test_adk_to_genai_mixed_array_types(self):
        """Test converting ADK tool with mixed array types - should fail first."""
        # Given: ADK tool with array of objects
        mixed_array_tool = adk_tool("process_records", "Process array of records", {
            'type': 'object',
            'properties': {
                'records': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'value': {'type': 'number'},
                            'active': {'type': 'boolean'}
                        },
                        'required': ['id']
                    }
                },
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            },
            'required': ['records']
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(mixed_array_tool)
        
        # Then: Should handle mixed array types correctly
        params = genai_declaration.parameters
        
        records_param = params.properties['records']
        assert records_param.type == genai.protos.Type.ARRAY
        assert records_param.items.type == genai.protos.Type.OBJECT
        assert 'id' in records_param.items.required
        
        tags_param = params.properties['tags']
        assert tags_param.type == genai.protos.Type.ARRAY
        assert tags_param.items.type == genai.protos.Type.STRING


class TestSchemaEdgeCases:
    """RED tests for schema edge cases and error handling - should fail first."""
    
    def test_adk_to_genai_missing_properties(self):
        """Test converting ADK tool with missing properties field - should fail first."""
        # Given: ADK tool with minimal schema
        minimal_tool = adk_tool("simple_action", "Simple action", {
            'type': 'object'
            # No properties field
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(minimal_tool)
        
        # Then: Should handle gracefully
        assert genai_declaration.name == "simple_action"
        params = genai_declaration.parameters
        assert params.type == genai.protos.Type.OBJECT
        # Should have empty or default properties
    
    def test_adk_to_genai_empty_required_list(self):
        """Test converting ADK tool with empty required list - should fail first."""
        # Given: ADK tool with no required fields
        optional_tool = adk_tool("optional_params", "Tool with optional params", {
            'type': 'object',
            'properties': {
                'param1': {'type': 'string'},
                'param2': {'type': 'number'}
            },
            'required': []  # Empty required list
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(optional_tool)
        
        # Then: Should handle empty required list
        params = genai_declaration.parameters
        assert len(params.required) == 0
        assert len(params.properties) == 2
    
    def test_adk_to_genai_unsupported_type(self):
        """Test converting ADK tool with unsupported type - should fail first."""
        # Given: ADK tool with unsupported type
        unsupported_tool = adk_tool("custom_type", "Tool with custom type", {
            'type': 'object',
            'properties': {
                'custom_field': {
                    'type': 'custom_type',  # Unsupported type
                    'description': 'Custom field'
                }
            }
        })
        
        # When: Converting to GenAI format
        # Then: Should either handle gracefully or raise appropriate error
        try:
            genai_declaration = convert_adk_tool_to_genai(unsupported_tool)
            # If it succeeds, should fallback to STRING type
            params = genai_declaration.parameters
            custom_param = params.properties['custom_field']
            assert custom_param.type == genai.protos.Type.STRING
        except (ValueError, KeyError, AttributeError):
            # Or it should raise a clear error
            pass  # This is acceptable behavior
    
    def test_adk_to_genai_circular_reference_protection(self):
        """Test handling of potential circular references - should fail first."""
        # Given: ADK tool with self-referencing structure (potential infinite loop)
        # Note: This is a theoretical edge case
        recursive_tool = adk_tool("recursive_structure", "Tool with recursive structure", {
            'type': 'object',
            'properties': {
                'node': {
                    'type': 'object',
                    'properties': {
                        'value': {'type': 'string'},
                        'children': {
                            'type': 'array',
                            'items': {
                                # This could potentially reference back to node
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string'},
                                    'parent_ref': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(recursive_tool)
        
        # Then: Should complete without infinite loop
        assert genai_declaration.name == "recursive_structure"
        params = genai_declaration.parameters
        node_param = params.properties['node']
        children_param = node_param.properties['children']
        assert children_param.type == genai.protos.Type.ARRAY


class TestSchemaDescriptions:
    """RED tests for description handling in schema conversion - should fail first."""
    
    def test_adk_to_genai_preserves_descriptions(self):
        """Test that parameter descriptions are preserved - should fail first."""
        # Given: ADK tool with detailed descriptions
        described_tool = adk_tool("documented_function", "Well documented function", {
            'type': 'object',
            'properties': {
                'input_file': {
                    'type': 'string',
                    'description': 'Path to the input file to process'
                },
                'output_format': {
                    'type': 'string',
                    'description': 'Desired output format (json, xml, csv)'
                },
                'options': {
                    'type': 'object',
                    'description': 'Processing options',
                    'properties': {
                        'validate': {
                            'type': 'boolean',
                            'description': 'Whether to validate input'
                        }
                    }
                }
            }
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(described_tool)
        
        # Then: Should preserve descriptions
        params = genai_declaration.parameters
        
        input_param = params.properties['input_file']
        assert input_param.description == 'Path to the input file to process'
        
        format_param = params.properties['output_format']
        assert format_param.description == 'Desired output format (json, xml, csv)'
        
        options_param = params.properties['options']
        assert options_param.description == 'Processing options'
        
        validate_param = options_param.properties['validate']
        assert validate_param.description == 'Whether to validate input'
    
    def test_adk_to_genai_handles_missing_descriptions(self):
        """Test handling of missing descriptions gracefully - should fail first."""
        # Given: ADK tool with some missing descriptions
        partial_desc_tool = adk_tool("partial_descriptions", "Tool with partial descriptions", {
            'type': 'object',
            'properties': {
                'with_desc': {
                    'type': 'string',
                    'description': 'This has a description'
                },
                'without_desc': {
                    'type': 'string'
                    # No description field
                }
            }
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(partial_desc_tool)
        
        # Then: Should handle both cases gracefully
        params = genai_declaration.parameters
        
        with_desc = params.properties['with_desc']
        assert with_desc.description == 'This has a description'
        
        without_desc = params.properties['without_desc']
        # Should either have empty description or default description
        assert hasattr(without_desc, 'description')


class TestSchemaValidationAgainstKnownExamples:
    """RED tests comparing against known good schema translations - should fail first."""
    
    def test_excel_read_sheet_schema_accuracy(self):
        """Test excel_read_sheet schema matches expected GenAI format - should fail first."""
        # Given: Known Excel tool schema
        excel_tool = adk_tool("excel_read_sheet", "Read data from Excel sheet", {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'Path to Excel file'
                },
                'sheet_name': {
                    'type': 'string',
                    'description': 'Name of sheet to read'
                },
                'range': {
                    'type': 'string',
                    'description': 'Cell range (e.g., A1:D10)',
                    'default': 'A1:Z1000'
                }
            },
            'required': ['file_path', 'sheet_name']
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(excel_tool)
        
        # Then: Should match expected structure exactly
        assert genai_declaration.name == "excel_read_sheet"
        assert genai_declaration.description == "Read data from Excel sheet"
        
        params = genai_declaration.parameters
        assert params.type == genai.protos.Type.OBJECT
        assert len(params.properties) == 3
        assert set(params.required) == {'file_path', 'sheet_name'}
        
        # Validate each parameter
        file_param = params.properties['file_path']
        assert file_param.type == genai.protos.Type.STRING
        assert file_param.description == 'Path to Excel file'
        
        sheet_param = params.properties['sheet_name']
        assert sheet_param.type == genai.protos.Type.STRING
        assert sheet_param.description == 'Name of sheet to read'
        
        range_param = params.properties['range']
        assert range_param.type == genai.protos.Type.STRING
        assert range_param.description == 'Cell range (e.g., A1:D10)'
    
    def test_analytics_load_dataset_schema_accuracy(self):
        """Test analytics tool schema matches expected format - should fail first."""
        # Given: Known Analytics tool schema
        analytics_tool = adk_tool("load_dataset", "Load dataset for analysis", {
            'type': 'object',
            'properties': {
                'source_path': {
                    'type': 'string',
                    'description': 'Path to dataset file'
                },
                'format': {
                    'type': 'string',
                    'description': 'Data format (csv, json, parquet)'
                },
                'options': {
                    'type': 'object',
                    'properties': {
                        'header': {'type': 'boolean', 'default': True},
                        'delimiter': {'type': 'string', 'default': ','},
                        'encoding': {'type': 'string', 'default': 'utf-8'}
                    }
                }
            },
            'required': ['source_path', 'format']
        })
        
        # When: Converting to GenAI format
        genai_declaration = convert_adk_tool_to_genai(analytics_tool)
        
        # Then: Should match expected analytics tool structure
        assert genai_declaration.name == "load_dataset"
        assert genai_declaration.description == "Load dataset for analysis"
        
        params = genai_declaration.parameters
        assert set(params.required) == {'source_path', 'format'}
        
        options_param = params.properties['options']
        assert options_param.type == genai.protos.Type.OBJECT
        assert len(options_param.properties) == 3
        
        header_param = options_param.properties['header']
        assert header_param.type == genai.protos.Type.BOOLEAN