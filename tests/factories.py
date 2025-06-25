"""Test factories for creating Google AI types.Content objects consistently."""

from google.genai import types
from google.adk.tools import BaseTool


def user(text):
    """Create a user message."""
    return types.Content(role="user", parts=[types.Part(text=text)])


def model(text):
    """Create a model message."""
    return types.Content(role="model", parts=[types.Part(text=text)])


def tool_resp(name, result):
    """Create a tool response message."""
    return types.Content(
        role="tool",
        parts=[types.Part(function_response=types.FunctionResponse(
            name=name, 
            response={"result": result}
        ))]
    )


def function_call(name, arguments=None):
    """Create a model message with function call."""
    if arguments is None:
        arguments = "{}"
    return types.Content(
        role="model",
        parts=[types.Part(function_call=types.FunctionCall(
            name=name, 
            arguments=arguments
        ))]
    )


def adk_tool(name, description, schema):
    """Create a mock ADK tool with given schema."""
    class MockAdkTool(BaseTool):
        def input_schema(self):
            return schema
        
        async def call(self, **kwargs):
            return f"MockAdkTool {name} called with: {kwargs}"
    
    return MockAdkTool(name=name, description=description)


def adk_string_tool():
    """Create ADK tool with string parameter."""
    return adk_tool(
        name="test_string_tool",
        description="A tool that takes a string parameter",
        schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "A message"}
            },
            "required": ["message"]
        }
    )


def adk_number_tool():
    """Create ADK tool with number parameter."""
    return adk_tool(
        name="test_number_tool", 
        description="A tool that takes a number parameter",
        schema={
            "type": "object",
            "properties": {
                "count": {"type": "number", "description": "A count"}
            },
            "required": ["count"]
        }
    )


def adk_object_tool():
    """Create ADK tool with nested object parameter."""
    return adk_tool(
        name="test_object_tool",
        description="A tool that takes an object parameter", 
        schema={
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "timeout": {"type": "number"}
                    }
                }
            },
            "required": ["config"]
        }
    )


def create_mock_adk_tool(name, description=None, with_schema=True):
    """Create a mock ADK tool for testing."""
    if description is None:
        description = f"Mock ADK tool: {name}"
    
    if with_schema:
        schema = {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": f"Input for {name}"}
            },
            "required": ["input"]
        }
    else:
        # For tools without schema, return empty object schema instead of None
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    return adk_tool(name, description, schema)


def create_test_server_config(name="test_server", enabled=True, priority=1):
    """Create a ServerConfig for testing."""
    from config import ServerConfig
    return ServerConfig(
        name=name,
        command="python",
        args=["-m", f"{name}_module"],
        cwd_env="PWD",
        tool_filter=[f"{name}_tool"],
        priority=priority,
        enabled=enabled
    )


def create_mock_mcp_tool(name, description=None):
    """Create a mock MCP tool (schema-less tool)."""
    if description is None:
        description = f"Mock MCP tool: {name}"
    
    class MockMCPTool:
        def __init__(self, name, description):
            self.name = name
            self.description = description
            # No input_schema method - simulates schema-less MCP tool
    
    return MockMCPTool(name, description)