"""Tests for ADK to GenAI tool translation."""
import pytest
import google.generativeai as genai
from adk_to_genai import convert_adk_tool_to_genai
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from tests.factories import adk_string_tool, adk_number_tool, adk_object_tool


def test_adk_to_genai_string_parameter():
    """Test converting ADK tool with string parameter to GenAI format."""
    adk_tool = adk_string_tool()
    
    # Convert to GenAI format
    genai_declaration = convert_adk_tool_to_genai(adk_tool)
    
    # Verify conversion
    assert genai_declaration.name == "test_string_tool"
    assert genai_declaration.description == "A tool that takes a string parameter"
    assert "message" in genai_declaration.parameters.properties
    assert genai_declaration.parameters.properties["message"].type == genai.protos.Type.STRING
    assert genai_declaration.parameters.required == ["message"]


def test_adk_to_genai_number_parameter():
    """Test converting ADK tool with number parameter to GenAI format - should fail first."""
    adk_tool = adk_number_tool()
    
    # Convert to GenAI format
    genai_declaration = convert_adk_tool_to_genai(adk_tool)
    
    # Verify conversion - this will fail because number type not supported yet
    assert genai_declaration.name == "test_number_tool"
    assert "count" in genai_declaration.parameters.properties
    assert genai_declaration.parameters.properties["count"].type == genai.protos.Type.NUMBER


def test_adk_to_genai_object_parameter():
    """Test converting ADK tool with object parameter to GenAI format - should fail first."""
    adk_tool = adk_object_tool()
    
    # Convert to GenAI format
    genai_declaration = convert_adk_tool_to_genai(adk_tool)
    
    # Verify conversion - this will fail because object type not supported yet
    assert genai_declaration.name == "test_object_tool"
    assert "config" in genai_declaration.parameters.properties
    
    # The config parameter should be an object with nested properties
    config_param = genai_declaration.parameters.properties["config"]
    assert config_param.type == genai.protos.Type.OBJECT
    
    # Verify nested properties exist
    assert "enabled" in config_param.properties
    assert "timeout" in config_param.properties
    
    # Verify nested property types
    assert config_param.properties["enabled"].type == genai.protos.Type.BOOLEAN
    assert config_param.properties["timeout"].type == genai.protos.Type.NUMBER