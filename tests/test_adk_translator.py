"""Tests for ADK to GenAI tool translation."""
import pytest
import google.generativeai as genai
from staffer.adk.translator import convert_adk_tool_to_genai
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