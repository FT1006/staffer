"""
MCP Path Handler - Centralized path conversion and file parameter management.

This module handles the complexity of converting relative paths to absolute paths
for MCP tools that may have different path requirements, with intelligent fallback
strategies.
"""

import os
from typing import Dict, Any


def convert_relative_to_absolute_paths(arguments: dict, working_directory: str) -> dict:
    """Convert relative paths to absolute paths for file parameters.
    
    Args:
        arguments: Dictionary of function arguments
        working_directory: Current working directory to resolve relative paths from
        
    Returns:
        Dictionary with relative paths converted to absolute paths
    """
    # Common file parameter names across different MCP servers
    file_param_names = {
        'fileAbsolutePath', 'filePath', 'inputFile', 'outputFile', 'outputPath',
        'configFile', 'relativePath', 'dataFile', 'csvFile', 'jsonFile',
        'file', 'path', 'input_file', 'output_file', 'dataset', 'filename'
    }
    
    result = {}
    for key, value in arguments.items():
        if key in file_param_names and isinstance(value, str):
            # Convert relative paths to absolute, leave absolute paths unchanged
            if not os.path.isabs(value):
                result[key] = os.path.abspath(os.path.join(working_directory, value))
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result


def detect_file_parameters(arguments: dict) -> bool:
    """Detect if arguments contain file parameters that might need path conversion.
    
    Args:
        arguments: Dictionary of function arguments
        
    Returns:
        True if file parameters are detected, False otherwise
    """
    file_param_names = {
        'fileAbsolutePath', 'filePath', 'inputFile', 'outputFile', 'outputPath',
        'configFile', 'relativePath', 'dataFile', 'csvFile', 'jsonFile',
        'file', 'path', 'input_file', 'output_file', 'dataset', 'filename'
    }
    
    return any(key in file_param_names for key in arguments.keys())


def validate_file_paths(arguments: dict, require_existing: bool = False) -> Dict[str, str]:
    """Validate file paths in arguments and return any issues found.
    
    Args:
        arguments: Dictionary of function arguments
        require_existing: If True, check that files actually exist
        
    Returns:
        Dictionary of parameter names to error messages (empty if all valid)
    """
    file_param_names = {
        'fileAbsolutePath', 'filePath', 'inputFile', 'outputFile', 'outputPath',
        'configFile', 'relativePath', 'dataFile', 'csvFile', 'jsonFile',
        'file', 'path', 'input_file', 'output_file', 'dataset', 'filename'
    }
    
    errors = {}
    
    for key, value in arguments.items():
        if key in file_param_names and isinstance(value, str):
            # Check if it's a valid path format
            if not value.strip():
                errors[key] = "Path cannot be empty"
                continue
            
            # Check if file exists (for input operations)
            if require_existing and key in {'fileAbsolutePath', 'filePath', 'inputFile', 'dataFile', 'csvFile', 'jsonFile', 'dataset'}:
                if not os.path.exists(value):
                    errors[key] = f"File does not exist: {value}"
    
    return errors


def get_tool_path_strategy(tool_name: str) -> str:
    """Determine the path handling strategy for a specific tool.
    
    Args:
        tool_name: Name of the MCP tool
        
    Returns:
        Strategy string: 'absolute_required', 'relative_preferred', 'flexible'
    """
    # Tools that typically require absolute paths
    absolute_required_tools = {
        'excel_read_sheet', 'excel_write_to_sheet', 'excel_describe_sheets',
        'excel_copy_sheet', 'excel_create_table'
    }
    
    # Tools that work better with relative paths
    relative_preferred_tools = {
        'load_dataset', 'read_csv', 'write_csv'
    }
    
    if tool_name in absolute_required_tools:
        return 'absolute_required'
    elif tool_name in relative_preferred_tools:
        return 'relative_preferred'
    else:
        return 'flexible'


def prepare_arguments_for_tool(tool_name: str, arguments: dict, working_directory: str) -> dict:
    """Prepare arguments for a specific tool based on its path requirements.
    
    Args:
        tool_name: Name of the MCP tool
        arguments: Original function arguments
        working_directory: Current working directory
        
    Returns:
        Arguments prepared for the specific tool's path requirements
    """
    strategy = get_tool_path_strategy(tool_name)
    
    if strategy == 'absolute_required':
        # Convert all relative paths to absolute
        return convert_relative_to_absolute_paths(arguments, working_directory)
    
    elif strategy == 'relative_preferred':
        # Keep relative paths relative, but resolve them relative to working directory
        result = {}
        file_param_names = {
            'fileAbsolutePath', 'filePath', 'inputFile', 'outputFile', 'outputPath',
            'configFile', 'relativePath', 'dataFile', 'csvFile', 'jsonFile',
            'file', 'path', 'input_file', 'output_file', 'dataset', 'filename'
        }
        
        for key, value in arguments.items():
            if key in file_param_names and isinstance(value, str):
                # If it's already absolute, convert to relative if possible
                if os.path.isabs(value):
                    try:
                        result[key] = os.path.relpath(value, working_directory)
                    except ValueError:
                        # Can't make it relative (different drives on Windows), keep absolute
                        result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    else:  # flexible
        # Return arguments as-is for flexible tools
        return arguments.copy()