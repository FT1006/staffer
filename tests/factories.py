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


def session_metadata(cwd=None, timestamp=None):
    """Create session metadata for testing."""
    import os
    from datetime import datetime
    
    if cwd is None:
        cwd = os.getcwd()
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    return {
        'cwd': str(cwd),
        'timestamp': timestamp
    }


def mock_terminal_ui(input_sequence=None):
    """Create a mock terminal UI with predictable input sequence."""
    from unittest.mock import MagicMock
    
    if input_sequence is None:
        input_sequence = ['exit']
    
    mock_terminal = MagicMock()
    mock_terminal.get_input.side_effect = input_sequence
    mock_terminal.show_spinner.return_value = MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
    
    # Add all the terminal UI methods that might be called
    mock_terminal.display_welcome = MagicMock()
    mock_terminal.display_success = MagicMock()
    mock_terminal.display_info = MagicMock()
    mock_terminal.display_error = MagicMock()
    
    return mock_terminal