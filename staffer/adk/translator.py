"""Translator for converting ADK tools to Google GenAI format."""
import google.generativeai as genai
from google.adk.tools import BaseTool
from typing import Dict, Any


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
            prop_type = prop_schema.get("type")
            
            # Handle string type
            if prop_type == "string":
                genai_properties[prop_name] = genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    description=prop_schema.get("description", "")
                )
            # Handle number type
            elif prop_type == "number":
                genai_properties[prop_name] = genai.protos.Schema(
                    type=genai.protos.Type.NUMBER,
                    description=prop_schema.get("description", "")
                )
    
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