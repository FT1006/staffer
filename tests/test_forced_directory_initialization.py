"""Tests for forced working directory initialization via function calls."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from google.genai import types
from staffer.session import save_session, load_session


def test_session_initialization_forces_working_directory_call():
    """Interactive session should force AI to call get_working_directory on startup."""
    
    # This test should FAIL initially because we haven't implemented the feature yet
    with patch('staffer.session.get_session_file_path') as mock_session_path:
        with patch('staffer.main.get_client') as mock_get_client:
            with patch('staffer.cli.interactive.get_client') as mock_interactive_client:
                
                # Setup test directory
                test_dir = Path("/test/working/directory")
                
                # Setup mock session file
                mock_session_path.return_value = "/tmp/test_session.json"
                
                # Create previous session without working directory context
                previous_session = [
                    types.Content(role="user", parts=[types.Part(text="hello")]),
                    types.Content(role="model", parts=[types.Part(text="Hi! How can I help?")])
                ]
                save_session(previous_session)
                
                # Setup mock LLM client
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client
                mock_interactive_client.return_value = mock_client
                
                # Mock the function call response  
                from google.genai.types import FunctionCall
                mock_function_call = FunctionCall(
                    name="get_working_directory",
                    args={}
                )
                
                mock_candidate = MagicMock()
                mock_candidate.content = types.Content(
                    role="model",
                    parts=[types.Part(function_call=mock_function_call)]
                )
                
                mock_response = MagicMock()
                mock_response.candidates = [mock_candidate]
                mock_client.models.generate_content.return_value = mock_response
                
                # This should be implemented: initialize_session_with_working_directory()
                with patch('os.getcwd', return_value=str(test_dir)):
                    from staffer.cli.interactive import initialize_session_with_working_directory
                    
                    # Load session and force working directory initialization
                    messages = load_session()
                    updated_messages = initialize_session_with_working_directory(messages)
                    
                    # Verify the function was called
                    mock_client.models.generate_content.assert_called_once()
                
                    # Verify the call included a directive to get working directory
                    call_args = mock_client.models.generate_content.call_args
                    contents = call_args[1]['contents']  # Get contents from kwargs
                    
                    # Should have added a user message asking for working directory
                    user_messages = [msg for msg in contents if msg.role == "user"]
                    assert len(user_messages) >= 2, "Should have original user message + working directory request"
                    
                    # The last user message should be about working directory
                    last_user_msg = user_messages[-1]
                    working_dir_request = last_user_msg.parts[0].text.lower()
                    assert any(phrase in working_dir_request for phrase in [
                        "working directory", 
                        "current directory",
                        "where am i"
                    ]), f"Should request working directory, got: {working_dir_request}"
                    
                    # Should have tool function available
                    config = call_args[1]['config']
                    tool_names = []
                    for tool in config.tools:
                        for decl in tool.function_declarations:
                            tool_names.append(decl.name)
                    assert "get_working_directory" in tool_names, \
                        f"get_working_directory should be available, got tools: {tool_names}"


def test_working_directory_function_result_is_preserved():
    """When get_working_directory is called, the result should be preserved in session."""
    
    test_dir = Path("/test/current/directory")
    
    # Mock function call result
    with patch('staffer.functions.get_working_directory.get_working_directory') as mock_func:
        mock_func.return_value = str(test_dir)
        
        # This should be implemented: call_function should handle get_working_directory
        from staffer.available_functions import call_function
        
        mock_function_call = MagicMock()
        mock_function_call.name = "get_working_directory"
        mock_function_call.args = {}
        
        result = call_function(mock_function_call, str(test_dir))
        
        # Verify the result contains the working directory
        assert result.role == "tool"
        response = result.parts[0].function_response.response
        assert str(test_dir) in str(response), \
            f"Function result should contain working directory {test_dir}, got: {response}"


def test_ai_knows_working_directory_after_initialization():
    """After forced initialization, AI should confidently state its working directory."""
    
    with patch('staffer.session.get_session_file_path') as mock_session_path:
        with patch('staffer.main.get_client') as mock_get_client:
            
            test_dir = Path("/users/test/project")
            mock_session_path.return_value = "/tmp/test_session.json"
            
            # Create session that has been initialized with working directory
            initialized_session = [
                types.Content(role="user", parts=[types.Part(text="Please confirm my working directory")]),
                types.Content(role="model", parts=[types.Part(text="I'll check my working directory.")]),
                types.Content(
                    role="tool",
                    parts=[types.Part(function_response=types.FunctionResponse(
                        name="get_working_directory",
                        response={"result": str(test_dir)}
                    ))]
                ),
                types.Content(role="model", parts=[types.Part(text=f"I am working in: {test_dir}")])
            ]
            
            save_session(initialized_session)
            
            # Mock AI response to location question
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            mock_candidate = MagicMock()
            mock_candidate.content = types.Content(
                role="model",
                parts=[types.Part(text=f"I am currently working in: {test_dir}")]
            )
            
            mock_response = MagicMock()
            mock_response.candidates = [mock_candidate]
            mock_response.text = f"I am currently working in: {test_dir}"
            mock_client.models.generate_content.return_value = mock_response
            
            # Test that AI can answer location questions confidently
            with patch('os.getcwd', return_value=str(test_dir)):
                from staffer.main import process_prompt
                
                messages = load_session()
                updated_messages = process_prompt("where are you?", messages=messages)
                
                # Verify AI was called
                mock_client.models.generate_content.assert_called_once()
                
                # Verify AI response contains the working directory
                ai_responses = [
                    msg.parts[0].text for msg in updated_messages
                    if msg.role == "model" and msg.parts and msg.parts[0].text
                ]
                
                location_response = " ".join(ai_responses)
                assert str(test_dir) in location_response, \
                    f"AI should know working directory {test_dir}, got: {location_response}"
                
                # Should NOT contain ignorance phrases
                ignorance_phrases = [
                    "don't know where",
                    "can't determine",
                    "unable to see"
                ]
                for phrase in ignorance_phrases:
                    assert phrase not in location_response.lower(), \
                        f"AI should not claim ignorance after initialization, found '{phrase}' in: {location_response}"


def test_initialization_works_across_directory_changes():
    """Initialization should work when user changes directories between sessions."""
    
    with patch('staffer.session.get_session_file_path') as mock_session_path:
        mock_session_path.return_value = "/tmp/test_session.json"
        
        # Simulate session in old directory
        old_dir = Path("/old/project/directory")
        old_session = [
            types.Content(role="user", parts=[types.Part(text="work in old directory")]),
            types.Content(role="model", parts=[types.Part(text=f"Working in {old_dir}")])
        ]
        save_session(old_session)
        
        # User changes to new directory
        new_dir = Path("/new/project/directory")
        
        with patch('os.getcwd', return_value=str(new_dir)):
            # This should detect directory change and force re-initialization
            from staffer.cli.interactive import should_reinitialize_working_directory
            
            messages = load_session()
            should_reinit = should_reinitialize_working_directory(messages, new_dir)
            
            # Should detect that we're in a different directory
            assert should_reinit, \
                f"Should detect directory change from {old_dir} to {new_dir}"