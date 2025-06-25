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
    import threading
    import queue
    
    def _run_discovery():
        """Run MCP discovery in separate thread."""
        try:
            return asyncio.run(_async_discover_mcp_tools())
        except Exception as e:
            print(f"MCP tool discovery failed: {e}")
            return []
    
    # Use thread to avoid event loop conflicts
    result_queue = queue.Queue()
    
    def thread_worker():
        result = _run_discovery()
        result_queue.put(result)
    
    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join(timeout=10)  # 10 second timeout for discovery
    
    if thread.is_alive():
        print("MCP tool discovery timed out")
        return []
    
    try:
        return result_queue.get_nowait()
    except queue.Empty:
        return []


async def _async_discover_mcp_tools():
    """Async helper to discover MCP tools."""
    import os
    
    # Create MCP client with environment-based configuration
    mcp_client = StafferMCPClient({
        'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH', '/Users/spaceship/project/staffer/mcp-aggregator'),
        'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG', 'test_config.yaml'),
        'timeout': float(os.getenv('MCP_TIMEOUT', '10.0'))
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

    # Built-in function registry
    function_dict = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "run_python_file": run_python_file,
        "get_working_directory": get_working_directory
    }

    # First, try built-in functions
    if function_name in function_dict:
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
    
    # If not built-in, try MCP tools
    mcp_result = None
    mcp_error = None
    
    try:
        mcp_result = _call_mcp_tool(function_call_part.name, args)
    except Exception as e:
        mcp_error = str(e)
    
    if mcp_result:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"result": mcp_result},
                )
            ],
        )
    
    # Neither built-in nor MCP tool found - provide helpful error
    error_msg = f"Unknown function: {function_name}"
    if mcp_error:
        error_msg += f" (MCP error: {mcp_error})"
    elif mcp_result is None:
        error_msg += " (MCP aggregator not available)"
    
    if verbose:
        print(f"Function execution failed: {error_msg}")
    
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"error": error_msg},
            )
        ],
    )


def _call_mcp_tool(tool_name: str, arguments: dict):
    """Execute MCP tool through StafferMCPClient.
    
    Returns:
        Tool result or None if tool not available
    """
    import os
    import threading
    import queue
    
    # Create MCP client with environment-based configuration
    mcp_client = StafferMCPClient({
        'aggregator_path': os.getenv('MCP_AGGREGATOR_PATH', '/Users/spaceship/project/staffer/mcp-aggregator'),
        'aggregator_config': os.getenv('MCP_AGGREGATOR_CONFIG', 'test_config.yaml'),
        'timeout': float(os.getenv('MCP_TIMEOUT', '10.0'))
    })
    
    # Handle async execution regardless of current event loop state
    def _run_mcp_tool():
        """Run MCP tool in separate thread to avoid event loop conflicts."""
        try:
            return asyncio.run(mcp_client.call_tool(tool_name, arguments))
        except Exception as e:
            return {"error": str(e)}
    
    # Execute in separate thread to avoid event loop conflicts
    result_queue = queue.Queue()
    
    def thread_worker():
        result = _run_mcp_tool()
        result_queue.put(result)
    
    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join(timeout=15)  # 15 second timeout
    
    if thread.is_alive():
        # Timeout occurred
        return {"error": "MCP tool execution timed out"}
    
    try:
        result = result_queue.get_nowait()
        if isinstance(result, dict) and "error" in result:
            return None  # Will be handled as failure
        return result
    except queue.Empty:
        return None