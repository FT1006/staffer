from google.genai import types
import asyncio
import os
import threading
import queue

from .functions.get_files_info import schema_get_files_info, get_files_info
from .functions.get_file_content import schema_get_file_content, get_file_content
from .functions.write_file import schema_write_file, write_file
from .functions.run_python_file import schema_run_python_file, run_python_file
from .functions.get_working_directory import schema_get_working_directory, get_working_directory

# Import MCP aggregator components
try:
    import sys
    # Get the staffer project root directory and add mcp-aggregator to path
    staffer_root = os.path.dirname(os.path.dirname(__file__))
    mcp_aggregator_path = os.path.join(staffer_root, 'mcp-aggregator')
    sys.path.insert(0, mcp_aggregator_path)
    from composer import GenericMCPServerComposer
except ImportError as e:
    print(f"Warning: Could not import MCP components: {e}")
    GenericMCPServerComposer = None


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
    """Get all available functions - built-in and MCP tools.
    
    Args:
        working_dir: Current working directory
        
    Returns:
        types.Tool with combined function declarations
    """
    # Get built-in function declarations
    built_in_declarations = list(available_functions.function_declarations)
    
    # Get MCP tool declarations
    mcp_declarations = _get_mcp_tool_declarations()
    
    # Combine and return
    combined_declarations = built_in_declarations + mcp_declarations
    return types.Tool(function_declarations=combined_declarations)


def _get_mcp_tool_declarations():
    """Get MCP tool declarations from composer.
    
    Returns:
        List of types.FunctionDeclaration for MCP tools
    """
    # Temporarily disable MCP integration to avoid schema validation issues
    # TODO: Fix GenAI schema conversion for MCP tools
    print("MCP tool integration temporarily disabled due to schema validation issues")
    return []
    
    # Skip MCP integration if components not available
    if not GenericMCPServerComposer:
        return []
    
    try:
        # Get default config path
        config_path = os.getenv('MCP_CONFIG_PATH', 
                              os.path.join(os.path.dirname(__file__), '..', 'mcp-aggregator', 'production.yaml'))
        
        # Get MCP tools via composer
        def _run_discovery():
            try:
                return asyncio.run(_async_get_mcp_tools(config_path))
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
        thread.join(timeout=5)  # 5 second timeout
        
        if thread.is_alive():
            print("MCP tool discovery timed out")
            return []
        
        try:
            return result_queue.get_nowait()
        except queue.Empty:
            return []
            
    except Exception as e:
        print(f"MCP integration error: {e}")
        return []


async def _async_get_mcp_tools(config_path):
    """Async helper to get MCP tools from composer."""
    # Initialize composer
    composer = GenericMCPServerComposer.from_config(config_path)
    
    # Get all tools from MCP servers (these are already GenAI FunctionDeclaration objects)
    genai_tools = await composer.get_all_tools()
    
    # The composer already returns GenAI FunctionDeclaration objects, so just return them
    return genai_tools


# Remove old MCP client code since we're using composer directly

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
    
    # If not built-in, try MCP tools via composer
    mcp_result = None
    mcp_error = None
    
    try:
        mcp_result = _call_mcp_tool_via_composer(function_call_part.name, args)
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


def _call_mcp_tool_via_composer(tool_name: str, arguments: dict):
    """Execute MCP tool through composer directly.
    
    Returns:
        Tool result or None if tool not available
    """
    # Skip MCP execution if components not available
    if not GenericMCPServerComposer:
        return None
    
    try:
        # Get config path
        config_path = os.getenv('MCP_CONFIG_PATH', 
                              os.path.join(os.path.dirname(__file__), '..', 'mcp-aggregator', 'production.yaml'))
        
        def _run_mcp_tool():
            """Run MCP tool via composer."""
            try:
                return asyncio.run(_async_call_mcp_tool(config_path, tool_name, arguments))
            except Exception as e:
                return {"error": str(e)}
        
        # Use thread to avoid event loop conflicts
        result_queue = queue.Queue()
        
        def thread_worker():
            result = _run_mcp_tool()
            result_queue.put(result)
        
        thread = threading.Thread(target=thread_worker)
        thread.start()
        thread.join(timeout=15)  # 15 second timeout
        
        if thread.is_alive():
            return {"error": "MCP tool execution timed out"}
        
        try:
            result = result_queue.get_nowait()
            if isinstance(result, dict) and "error" in result:
                return None  # Will be handled as failure
            return result
        except queue.Empty:
            return None
            
    except Exception as e:
        print(f"MCP tool execution error: {e}")
        return None


async def _async_call_mcp_tool(config_path: str, tool_name: str, arguments: dict):
    """Async helper to execute MCP tool via composer."""
    # Initialize composer
    composer = GenericMCPServerComposer.from_config(config_path)
    
    # Execute tool
    result = await composer.call_tool(tool_name, arguments)
    
    return result