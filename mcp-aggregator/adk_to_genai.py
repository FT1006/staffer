"""GenAI service layer for MCP tool integration.

This service handles all concerns related to converting MCP tools 
for use with GenAI-engineered agents like Staffer.
"""
import os
import asyncio
import google.generativeai as genai
from google.adk.tools import BaseTool
from typing import Dict, List, Any, Optional


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


class GenAIToolService:
    """Pure adapter layer for GenAI agents to interact with MCP tools.
    
    This service provides GenAI-specific formatting and interfaces while
    delegating all MCP business logic to the Composer. Clean separation:
    - Composer: Owns MCP concerns (config, discovery, execution)  
    - GenAIToolService: Owns GenAI formatting and interface adaptation
    """
    
    def __init__(self, composer=None):
        """Initialize the GenAI service adapter.
        
        Args:
            composer: GenericMCPServerComposer instance (dependency injection)
        """
        self.composer = composer
    
    @classmethod
    def from_config(cls, config_path: str = "aggregation.yaml"):
        """Create service with composer from config file.
        
        Args:
            config_path: Path to MCP aggregator config file
            
        Returns:
            GenAIToolService with initialized composer
        """
        # Import here to avoid circular imports
        from composer import GenericMCPServerComposer
        
        # Get absolute path to config
        config_dir = os.path.dirname(__file__)
        full_config_path = os.path.join(config_dir, config_path)
        
        # Create composer and inject it
        composer = GenericMCPServerComposer.from_config(full_config_path)
        return cls(composer)
    
    async def get_tool_declarations(self):
        """Get tool declarations in Staffer-compatible format.
        
        Pure adapter method: delegates to composer, converts format for GenAI.
        
        Returns:
            List of types.FunctionDeclaration ready for GenAI agents
        """
        if not self.composer:
            raise ValueError("GenAIToolService not initialized. Use from_config() or inject composer.")
        
        # Delegate to composer for MCP business logic (gets raw ADK tools)
        adk_tools = await self.composer.get_all_tools()
        
        # GenAI service responsibility: convert ADK tools to GenAI format
        import google.genai.types as types
        
        declarations = []
        for adk_tool in adk_tools:
            try:
                # Convert ADK tool to GenAI format using our converter
                if hasattr(adk_tool, 'input_schema'):
                    # ADK FunctionTool - use full converter
                    genai_proto = convert_adk_tool_to_genai(adk_tool)
                else:
                    # Tool without schema - create flexible declaration
                    genai_proto = self._create_flexible_declaration(adk_tool)
                
                # Convert from genai.protos.FunctionDeclaration to types.FunctionDeclaration
                declaration = types.FunctionDeclaration(
                    name=genai_proto.name,
                    description=genai_proto.description,
                    parameters=genai_proto.parameters
                )
                declarations.append(declaration)
            except Exception as e:
                # Skip problematic tools gracefully - GenAI adapter concern
                print(f"GenAI format conversion failed for tool {getattr(adk_tool, 'name', 'unknown')}: {e}")
                continue
        
        return declarations
    
    async def execute_tool(self, tool_name: str, arguments: dict, working_directory: str = None):
        """Execute a tool via composer with GenAI-specific argument preparation.
        
        Pure adapter method: handles GenAI concerns, delegates execution to composer.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments 
            working_directory: Current working directory for path resolution (GenAI concern)
            
        Returns:
            Tool execution result or None if failed
        """
        if not self.composer:
            raise ValueError("GenAIToolService not initialized. Use from_config() or inject composer.")
        
        try:
            # GenAI-specific concern: prepare arguments with path resolution
            if working_directory:
                prepared_args = self._prepare_genai_arguments(arguments, working_directory)
            else:
                prepared_args = arguments
            
            # Delegate actual execution to composer (MCP concern)
            result = await self.composer.call_tool(tool_name, prepared_args)
            return result
            
        except Exception as e:
            # GenAI-specific error handling
            print(f"GenAI tool execution failed: {e}")
            return None
    
    def _prepare_genai_arguments(self, arguments: dict, working_directory: str) -> dict:
        """Prepare arguments for GenAI tools with path resolution.
        
        This is a GenAI-specific concern because GenAI agents work with relative paths
        but MCP tools often need absolute paths. Pure adapter logic.
        """
        prepared_args = arguments.copy()
        
        # Convert relative paths to absolute - GenAI convenience feature
        for key, value in prepared_args.items():
            if isinstance(value, str) and value:
                # Handle common path parameters that GenAI agents use
                if key in ['file_path', 'path'] or '_path' in key:
                    if not os.path.isabs(value):
                        prepared_args[key] = os.path.join(working_directory, value)
                # Handle potential file paths in other parameters
                elif ('/' in value or '\\' in value) and not os.path.isabs(value):
                    potential_abs_path = os.path.join(working_directory, value)
                    if os.path.exists(potential_abs_path):
                        prepared_args[key] = potential_abs_path
        
        return prepared_args
    
    def _create_flexible_declaration(self, tool: Any) -> Any:
        """Create GenAI declaration for tool without schema.
        
        This is a GenAI-specific concern for handling tools that don't have
        proper schemas - create a flexible string parameter.
        """
        return genai.protos.FunctionDeclaration(
            name=getattr(tool, 'name', 'unknown_tool'),
            description=getattr(tool, 'description', 'Tool'),
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    'input': genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description='Tool input parameters as JSON string'
                    )
                }
            )
        )