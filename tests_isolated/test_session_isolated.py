"""Isolated session tests - require aggressive mocking before CI."""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
from google.genai import types
from staffer.session import save_session


def test_working_directory_is_visible_after_restore():
    """AI should know the working directory without having to ask or infer."""
    # Mock Google AI modules to avoid dependency issues
    with patch.dict(sys.modules, {
        'google': MagicMock(),
        'google.genai': MagicMock(),
    }):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = os.path.join(temp_dir, "current_session.json")

            with patch('staffer.session.get_session_file_path', return_value=session_file):
                # Create a previous session (simulate user has been working)
                previous_session = [
                    types.Content(role="user", parts=[types.Part(text="hello")])
                ]
                save_session(previous_session)

                # Test: what happens when interactive mode loads this session
                # and processes a new prompt asking about working directory?
                with patch('staffer.main.process_prompt') as mock_process:
                    # Mock process_prompt to capture what messages it receives
                    mock_process.return_value = []  # Return empty for simplicity

                    from staffer.cli.interactive import main as interactive_main

                    # Simulate user asking about working directory after session restore
                    with patch('builtins.input', side_effect=['what directory am I in?', 'exit']):
                        interactive_main()

                    # Verify that process_prompt was called
                    assert mock_process.called, "process_prompt should be called when user asks question"

                    # Get the messages that were passed to process_prompt
                    call_args = mock_process.call_args
                    if call_args:
                        messages = call_args[1]['messages']  # keyword argument
                        
                        # Check that working directory context is included
                        # Should have: restored session + working directory context + user question
                        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
                        
                        # Look for working directory context in the messages
                        has_working_dir_context = any(
                            hasattr(msg, 'role') and msg.role == 'tool' and 
                            any(hasattr(part, 'function_response') and 
                                part.function_response and 
                                'get_working_directory' in str(part.function_response.name)
                                for part in msg.parts)
                            for msg in messages
                        )
                        
                        assert has_working_dir_context, \
                            "Working directory should be visible in restored session context"