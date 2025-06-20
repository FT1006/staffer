"""Test factories for creating Google AI types.Content objects consistently."""

from google.genai import types


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