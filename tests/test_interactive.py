"""Tests for interactive mode functionality."""

import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_interactive_mode_basic_loop():
    """Test that interactive mode actually enters loop and calls input."""
    # Mock the genai client at module level to prevent API key errors
    with patch('google.genai.Client') as mock_client:
        mock_client.return_value = MagicMock()
        
        # Mock the process_prompt to avoid API calls in tests
        with patch('staffer.cli.interactive.process_prompt') as mock_process:
            from staffer.cli import interactive
            
            with patch('builtins.input', side_effect=['exit']) as mock_input:
                result = interactive.main()
            
            # Proves we entered the loop and actually called input
            mock_input.assert_called()
            assert result is None


def test_interactive_prompt_shows(capsys):
    """Test that interactive mode shows proper prompt to user."""
    # Mock the genai client at module level to prevent API key errors
    with patch('google.genai.Client') as mock_client:
        mock_client.return_value = MagicMock()
        
        # Mock the process_prompt to avoid API calls in tests
        with patch('staffer.cli.interactive.process_prompt'):
            from staffer.cli import interactive
            
            with patch('builtins.input', side_effect=['exit']):
                interactive.main()
            
            # Check real stdout output, not mocked
            captured = capsys.readouterr()
            assert "staffer>" in captured.out


def test_interactive_flag_detection():
    """Test CLI detects --interactive flag and routes to interactive mode."""
    # Use factory-based approach with fake_llm fixture
    from tests.conftest import FakeGeminiClient
    
    with patch('staffer.llm.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        # Mock the interactive main function to verify it gets called
        with patch('staffer.cli.interactive.main') as mock_interactive_main:
            # Test by invoking the main function directly with mocked args
            from staffer.main import main
            
            with patch('sys.argv', ['staffer', '--interactive']):
                # Should not raise exceptions and should route to interactive mode
                try:
                    main()
                    returncode = 0
                except SystemExit as e:
                    returncode = e.code if e.code is not None else 0
                    
            # Verify interactive mode was actually called (this is what we're testing)
            mock_interactive_main.assert_called_once()
            assert returncode == 0


def test_message_history_persistence():
    """Interactive mode should maintain message history between prompts."""
    # Use factory-based approach with fake_llm
    from tests.conftest import FakeGeminiClient
    
    with patch('staffer.cli.interactive.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        # Mock session loading to return empty (fresh session)
        with patch('staffer.cli.interactive.load_session', return_value=[]):
            with patch('staffer.cli.interactive.save_session'):
                # Mock process_prompt to capture calls and return growing history  
                with patch('staffer.cli.interactive.process_prompt') as mock_process:
                    # Setup side effects: return growing message history
                    mock_process.side_effect = [
                        ['msg1'],  # First call returns 1 message
                        ['msg1', 'msg2']  # Second call returns 2 messages
                    ]
                    
                    from staffer.cli import interactive

                    # Simulate user input: two prompts then exit
                    with patch('builtins.input', side_effect=['hello', 'what is my name?', 'exit']):
                        interactive.main()

                    # Verify process_prompt was called twice
                    assert mock_process.call_count == 2

                    # Check the arguments passed to each call
                    first_call = mock_process.call_args_list[0]
                    second_call = mock_process.call_args_list[1]

                    # First call should have minimal messages (just working dir init)
                    first_messages = first_call.kwargs['messages']
                    
                    # Second call should have the history from first call
                    second_messages = second_call.kwargs['messages']
                    assert len(second_messages) == 1, "Second call should receive history from first call"
                    assert second_messages == ['msg1']


def test_reset_command_clears_history_unit():
    """Unit test: /reset command clears conversation history in memory."""
    from tests.conftest import FakeGeminiClient
    from tests.factories import user, model
    
    with patch('staffer.cli.interactive.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        # Setup initial message history
        initial_messages = [
            user("what files are here?"),
            model("I can see several files..."),
            user("tell me about main.py"),
            model("The main.py file contains...")
        ]
        
        # Mock session loading to return history 
        with patch('staffer.cli.interactive.load_session', return_value=initial_messages):
            with patch('staffer.cli.interactive.save_session') as mock_save:
                with patch('staffer.cli.interactive.process_prompt') as mock_process:
                    from staffer.cli import interactive
                    
                    # User types /reset then exit
                    with patch('builtins.input', side_effect=['/reset', 'exit']):
                        interactive.main()
                    
                    # /reset should bypass LLM call
                    mock_process.assert_not_called()
                    
                    # Should save an empty message list after reset
                    mock_save.assert_called()
                    final_messages = mock_save.call_args_list[-1][0][0]  # Last call's first argument
                    
                    # After reset, messages should be empty (just working directory context)
                    assert len(final_messages) == 0 or all(
                        "working directory" in str(msg).lower() for msg in final_messages
                    ), "Reset should clear conversation history"


def test_reset_command_clears_session_file(tmp_path):
    """Integration test: /reset clears session file on disk."""
    from tests.factories import user, model
    from tests.conftest import FakeGeminiClient
    
    # Use temp directory for session storage
    session_dir = tmp_path / ".staffer" 
    session_file = session_dir / "current_session.json"
    
    with patch('staffer.session.get_session_file_path', return_value=session_file):
        # Create initial session with some history
        initial_messages = [
            user("what files are here?"),
            model("I can see several files..."),
            user("tell me about main.py"),
            model("The main.py file contains...")
        ]
        
        # Save initial session to disk
        from staffer.session import save_session
        save_session(initial_messages)
        
        # Verify session was saved
        from staffer.session import load_session
        loaded_messages = load_session()
        assert len(loaded_messages) == 4, "Initial session should have 4 messages"
        
        # Mock LLM client before importing interactive module
        with patch('staffer.llm.get_client') as mock_get_client:
            fake_client = FakeGeminiClient()
            mock_get_client.return_value = fake_client
            
            from staffer.cli import interactive
            
            # User types /reset then exit
            with patch('builtins.input', side_effect=['/reset', 'exit']):
                interactive.main()
        
        # Verify session file is now empty/minimal after reset
        final_messages = load_session() 
        assert len(final_messages) == 0, "Session should be cleared after reset"


def test_reset_command_shows_confirmation(capsys):
    """Simple test: /reset shows user confirmation message."""
    from tests.conftest import FakeGeminiClient
    
    # Mock LLM client before any imports
    with patch('staffer.llm.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        from staffer.cli import interactive
        
        with patch('staffer.cli.interactive.load_session', return_value=[]):
            with patch('staffer.cli.interactive.save_session'):
                with patch('builtins.input', side_effect=['/reset', 'exit']):
                    interactive.main()
    
    # Check printed output includes reset confirmation  
    captured = capsys.readouterr()
    assert "session cleared" in captured.out.lower() or "starting fresh" in captured.out.lower(), \
        "User should see reset confirmation"