from google.genai import types
import asyncio

from .functions.get_files_info import schema_get_files_info, get_files_info
from .functions.get_file_content import schema_get_file_content, get_file_content
from .functions.write_file import schema_write_file, write_file
from .functions.run_python_file import schema_run_python_file, run_python_file
from .functions.get_working_directory import schema_get_working_directory, get_working_directory
from .mcp_client import StafferMCPClient


available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
        schema_get_working_directory,
    ]
)

def get_available_functions(working_dir):
    return available_functions


def get_available_functions_with_mcp(working_dir):
    """Merge built-in functions with MCP-discovered tools.
    
    Args:
        working_dir: Current working directory (not used but kept for compatibility)
        
    Returns:
        types.Tool with combined function declarations
    """
    # Get built-in functions
    built_in_declarations = list(available_functions.function_declarations)
    
    # Discover MCP tools
    mcp_declarations = _discover_mcp_tools()
    
    # Combine both
    combined_declarations = built_in_declarations + mcp_declarations
    
    return types.Tool(function_declarations=combined_declarations)


def _discover_mcp_tools():
    """Discover tools from MCP aggregator and convert to GenAI format.
    
    Returns:
        List of types.FunctionDeclaration objects for MCP tools
    """
    try:
        # Try to get current event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, we can't run another one
            # Return empty list for now - this is a limitation we'd need to address
            return []
        except RuntimeError:
            # No event loop running, we can create a new one
            return asyncio.run(_async_discover_mcp_tools())
    except Exception:
        # Graceful fallback when MCP discovery fails
        return []


async def _async_discover_mcp_tools():
    """Async helper to discover MCP tools."""
    # Create MCP client with aggregator configuration
    mcp_client = StafferMCPClient({
        'aggregator_path': '/Users/spaceship/project/staffer/mcp-aggregator',
        'aggregator_config': 'test_config.yaml',
        'timeout': 10.0
    })
    
    # Discover tools
    mcp_tools = await mcp_client.list_tools()
    
    # Convert to GenAI function declarations
    declarations = []
    for tool in mcp_tools:
        try:
            # Create function declaration from MCP tool
            func_decl = types.FunctionDeclaration(
                name=tool['name'],
                description=tool.get('description', f"MCP tool: {tool['name']}"),
                parameters=tool.get('inputSchema', {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            )
            declarations.append(func_decl)
        except Exception:
            # Skip malformed tools
            continue
    
    return declarations

def call_function(function_call_part, working_directory, verbose=False):
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    args = function_call_part.args or {}
    function_name = function_call_part.name.lower()

    function_dict = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "run_python_file": run_python_file,
        "get_working_directory": get_working_directory
    }

    if function_name not in function_dict:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )
    
    function_result = function_dict[function_name](working_directory, **args)

    return types.Content(
    role="tool",
    parts=[
        types.Part.from_function_response(
            name=function_name,
            response={"result": function_result},
        )
    ],
)