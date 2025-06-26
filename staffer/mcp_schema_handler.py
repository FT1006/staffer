"""
MCP Schema Handler - Centralized schema validation and fallback management.

This module handles the complexity of MCP tool schema validation, cyclical reference
detection, and provides intelligent fallback schemas for tools with problematic schemas.
"""

from google.genai import types
import os


def sanitize_schema(schema):
    """Sanitize schema to remove problematic properties while preserving structure.
    
    Similar to gemini-cli's sanitizeParameters function.
    """
    if not schema:
        return schema
    
    # Create a copy to avoid modifying the original
    if hasattr(schema, '_pb'):
        # It's already a GenAI Schema object, we need to work with it carefully
        # For now, return as-is since GenAI schemas are already sanitized
        return schema
    
    # For dict-based schemas, do the sanitization
    if isinstance(schema, dict):
        sanitized = {}
        for key, value in schema.items():
            # Skip problematic properties
            if key in ['$schema', 'additionalProperties']:
                continue
            
            # Handle anyOf with default (Vertex AI issue)
            if key == 'anyOf' and 'default' in schema:
                # Remove default when anyOf is present
                continue
            
            # Recursively sanitize nested schemas
            if key == 'properties' and isinstance(value, dict):
                sanitized_props = {}
                for prop_name, prop_schema in value.items():
                    sanitized_props[prop_name] = sanitize_schema(prop_schema)
                sanitized[key] = sanitized_props
            elif key == 'items':
                sanitized[key] = sanitize_schema(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    return schema


def create_fallback_schema_for_tool(tool_name: str, tool_description: str) -> types.Schema:
    """Create appropriate fallback schema based on tool name and description.
    
    Args:
        tool_name: Name of the MCP tool
        tool_description: Description of what the tool does
        
    Returns:
        A simplified but functional schema for the tool
    """
    # Excel tools - specific schemas based on function
    if 'excel' in tool_name.lower():
        return _create_excel_fallback_schema(tool_name)
    
    # Analytics/Data tools
    if any(keyword in tool_name.lower() for keyword in ['analytics', 'data', 'chart', 'plot']):
        return _create_analytics_fallback_schema(tool_name, tool_description)
    
    # File operation tools
    if any(keyword in tool_name.lower() for keyword in ['read', 'write', 'load', 'save']):
        return _create_file_operation_fallback_schema(tool_name, tool_description)
    
    # Generic fallback for unknown tools
    return _create_generic_fallback_schema(tool_name, tool_description)


def _create_excel_fallback_schema(tool_name: str) -> types.Schema:
    """Create fallback schema for Excel tools based on their specific function."""
    
    if tool_name == 'excel_read_sheet':
        return types.Schema(
            type=types.Type.OBJECT,
            properties={
                "fileAbsolutePath": types.Schema(
                    type=types.Type.STRING,
                    description="Absolute path to the Excel file"
                ),
                "sheetName": types.Schema(
                    type=types.Type.STRING,
                    description="Sheet name in the Excel file"
                ),
                "range": types.Schema(
                    type=types.Type.STRING,
                    description="Range of cells to read (e.g., 'A1:C10'). Optional - defaults to first page"
                ),
                "showFormula": types.Schema(
                    type=types.Type.BOOLEAN,
                    description="Show formula instead of value. Optional - defaults to false"
                )
            },
            required=["fileAbsolutePath", "sheetName"]
        )
    
    elif tool_name == 'excel_write_to_sheet':
        return types.Schema(
            type=types.Type.OBJECT,
            properties={
                "fileAbsolutePath": types.Schema(
                    type=types.Type.STRING,
                    description="Absolute path to the Excel file"
                ),
                "sheetName": types.Schema(
                    type=types.Type.STRING,
                    description="Sheet name in the Excel file"
                ),
                "range": types.Schema(
                    type=types.Type.STRING,
                    description="Range of cells to write to (e.g., 'A1:C10')"
                ),
                "values": types.Schema(
                    type=types.Type.STRING,
                    description="Values to write (as JSON array of arrays)"
                )
            },
            required=["fileAbsolutePath", "sheetName", "range", "values"]
        )
    
    elif tool_name == 'excel_copy_sheet':
        return types.Schema(
            type=types.Type.OBJECT,
            properties={
                "fileAbsolutePath": types.Schema(
                    type=types.Type.STRING,
                    description="Absolute path to the Excel file"
                ),
                "sourceSheetName": types.Schema(
                    type=types.Type.STRING,
                    description="Name of the sheet to copy from"
                ),
                "targetSheetName": types.Schema(
                    type=types.Type.STRING,
                    description="Name of the new sheet to create"
                )
            },
            required=["fileAbsolutePath", "sourceSheetName", "targetSheetName"]
        )
    
    else:
        # Default Excel schema for tools like excel_describe_sheets
        return types.Schema(
            type=types.Type.OBJECT,
            properties={
                "fileAbsolutePath": types.Schema(
                    type=types.Type.STRING,
                    description="Absolute path to the Excel file"
                )
            },
            required=["fileAbsolutePath"]
        )


def _create_analytics_fallback_schema(tool_name: str, tool_description: str) -> types.Schema:
    """Create fallback schema for analytics/data tools."""
    
    # Common analytics parameters
    properties = {
        "dataset": types.Schema(
            type=types.Type.STRING,
            description="Dataset name or file path to analyze"
        )
    }
    required = ["dataset"]
    
    # Add tool-specific parameters based on name
    if 'load' in tool_name.lower():
        properties["filePath"] = types.Schema(
            type=types.Type.STRING,
            description="Path to the data file to load"
        )
        required = ["filePath"]
    
    elif 'chart' in tool_name.lower() or 'plot' in tool_name.lower():
        properties.update({
            "chartType": types.Schema(
                type=types.Type.STRING,
                description="Type of chart to create (e.g., 'bar', 'line', 'scatter')"
            ),
            "xColumn": types.Schema(
                type=types.Type.STRING,
                description="Column to use for X-axis"
            ),
            "yColumn": types.Schema(
                type=types.Type.STRING,
                description="Column to use for Y-axis"
            )
        })
        required.extend(["chartType", "xColumn", "yColumn"])
    
    elif 'correlations' in tool_name.lower():
        properties["columns"] = types.Schema(
            type=types.Type.STRING,
            description="Columns to analyze for correlations (comma-separated)"
        )
    
    return types.Schema(
        type=types.Type.OBJECT,
        properties=properties,
        required=required
    )


def _create_file_operation_fallback_schema(tool_name: str, tool_description: str) -> types.Schema:
    """Create fallback schema for file operation tools."""
    
    properties = {
        "filePath": types.Schema(
            type=types.Type.STRING,
            description="Path to the file"
        )
    }
    required = ["filePath"]
    
    # Add operation-specific parameters
    if 'write' in tool_name.lower() or 'save' in tool_name.lower():
        properties["content"] = types.Schema(
            type=types.Type.STRING,
            description="Content to write to the file"
        )
        required.append("content")
    
    elif 'read' in tool_name.lower():
        properties["format"] = types.Schema(
            type=types.Type.STRING,
            description="Format to read the file in (optional)"
        )
    
    return types.Schema(
        type=types.Type.OBJECT,
        properties=properties,
        required=required
    )


def _create_generic_fallback_schema(tool_name: str, tool_description: str) -> types.Schema:
    """Create generic fallback schema for unknown tools."""
    
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "input": types.Schema(
                type=types.Type.STRING,
                description=f"Input parameters for {tool_name} (as JSON string if needed)"
            )
        },
        required=[]
    )


def process_mcp_tool_schema(tool) -> types.FunctionDeclaration:
    """Process an MCP tool and return a safe FunctionDeclaration.
    
    Args:
        tool: MCP tool with potentially problematic schema
        
    Returns:
        A safe FunctionDeclaration with either the original schema or a fallback
    """
    try:
        # For tools with proper schemas, try to preserve them
        if hasattr(tool, 'parameters') and tool.parameters:
            # Try to use the original schema first
            try:
                safe_decl = types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.parameters
                )
                # Test if the declaration is valid by trying to access its properties
                _ = safe_decl.parameters.type
                return safe_decl
            
            except Exception as schema_error:
                # Schema has issues (like cyclical references), fall back to simplified schema
                # Quietly log but don't print to avoid UI clutter
                pass
        
        # Create fallback schema
        fallback_schema = create_fallback_schema_for_tool(tool.name, tool.description)
        
        return types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=fallback_schema
        )
        
    except Exception as e:
        # Quietly handle errors without cluttering UI
        # Last resort - generic schema
        generic_schema = _create_generic_fallback_schema(tool.name, getattr(tool, 'description', ''))
        return types.FunctionDeclaration(
            name=tool.name,
            description=getattr(tool, 'description', f"MCP tool: {tool.name}"),
            parameters=generic_schema
        )