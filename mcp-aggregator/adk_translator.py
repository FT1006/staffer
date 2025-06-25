"""Translator for converting ADK tools to Google GenAI format."""
import google.generativeai as genai
from google.adk.tools import BaseTool
from typing import Dict, Any


def _convert_schema_to_genai(prop_schema: Dict[str, Any]) -> genai.protos.Schema:
    """
    Recursively convert a JSON schema property to GenAI Schema format.
    
    Args:
        prop_schema: JSON schema property definition
        
    Returns:
        GenAI Schema object
    """
    prop_type = prop_schema.get("type")
    description = prop_schema.get("description", "")
    
    # Handle primitive types
    if prop_type == "string":
        return genai.protos.Schema(type=genai.protos.Type.STRING, description=description)
    elif prop_type == "number":
        return genai.protos.Schema(type=genai.protos.Type.NUMBER, description=description)
    elif prop_type == "boolean":
        return genai.protos.Schema(type=genai.protos.Type.BOOLEAN, description=description)
    
    # Handle object type with nested properties
    elif prop_type == "object":
        nested_properties = {}
        if "properties" in prop_schema:
            for nested_name, nested_schema in prop_schema["properties"].items():
                nested_properties[nested_name] = _convert_schema_to_genai(nested_schema)
        
        return genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            description=description,
            properties=nested_properties,
            required=prop_schema.get("required", [])
        )
    
    # Handle array type
    elif prop_type == "array":
        items_schema = prop_schema.get("items", {"type": "string"})
        items_genai_schema = _convert_schema_to_genai(items_schema)
        
        return genai.protos.Schema(
            type=genai.protos.Type.ARRAY,
            description=description,
            items=items_genai_schema
        )
    
    # Default fallback for unsupported types
    else:
        return genai.protos.Schema(type=genai.protos.Type.STRING, description=description)


def convert_adk_tool_to_genai(adk_tool: BaseTool) -> genai.protos.FunctionDeclaration:
    """
    Convert an ADK tool to Google GenAI function declaration format.
    
    Args:
        adk_tool: The ADK tool to convert
        
    Returns:
        GenAI FunctionDeclaration compatible with Staffer
    """
    # Get the tool schema - ADK tools have input_schema() method
    schema = adk_tool.input_schema()
    
    # Convert JSON schema properties to GenAI format
    genai_properties = {}
    
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            genai_properties[prop_name] = _convert_schema_to_genai(prop_schema)
    
    # Create GenAI function declaration
    return genai.protos.FunctionDeclaration(
        name=adk_tool.name,
        description=adk_tool.description,
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties=genai_properties,
            required=schema.get("required", [])
        )
    )