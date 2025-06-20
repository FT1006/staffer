"""Tests for session lifecycle commands (/reset, /session, etc.)."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.factories import user, model


def test_reset_command_clears_conversation_history():
    """Test /reset command clears conversation but keeps current directory."""
    from tests.conftest import FakeGeminiClient
    
    with patch('staffer.cli.interactive.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        # Mock session operations
        with patch('staffer.cli.interactive.load_session') as mock_load:
            with patch('staffer.cli.interactive.save_session') as mock_save:
                # Start with existing conversation history
                existing_messages = [
                    user("What files are here?"),
                    model("I can see several files in the current directory..."),
                    user("Analyze main.py"),
                    model("Here's my analysis of main.py...")
                ]
                mock_load.return_value = existing_messages
                
                from staffer.cli import interactive
                
                # Simulate user typing /reset then exit
                with patch('builtins.input', side_effect=['/reset', 'exit']):
                    interactive.main()
                
                # Verify save_session was called at least twice: 
                # 1. After working directory initialization 
                # 2. After /reset with empty messages
                # 3. After exit 
                assert mock_save.call_count >= 2
                
                # Look for the /reset save call - should be empty list
                reset_found = False
                for call in mock_save.call_args_list:
                    saved_messages = call[0][0]  # First positional argument
                    if len(saved_messages) == 0:  # Found the reset call
                        reset_found = True
                        break
                
                assert reset_found, "Should have found a save call with empty messages from /reset"


def test_session_command_shows_current_info():
    """Test /session command displays session health information."""
    from tests.conftest import FakeGeminiClient
    
    with patch('staffer.cli.interactive.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        with patch('staffer.cli.interactive.load_session') as mock_load:
            with patch('staffer.cli.interactive.save_session'):
                # Setup existing session with known messages
                test_messages = [
                    user("Hello"),
                    model("Hi there!"),
                    user("What's my current directory?")
                ]
                mock_load.return_value = test_messages
                
                from staffer.cli import interactive
                
                # Capture printed output
                with patch('builtins.print') as mock_print:
                    with patch('builtins.input', side_effect=['/session', 'exit']):
                        interactive.main()
                
                # Verify session info was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
                session_output = ' '.join(str(call) for call in print_calls)
                
                # Should show current directory
                current_dir = str(Path.cwd())
                assert current_dir in session_output or "Directory" in session_output
                
                # Should show message count
                assert "3" in session_output or "Messages" in session_output


def test_help_command_shows_available_commands():
    """Test /help command lists available session commands."""
    from tests.conftest import FakeGeminiClient
    
    with patch('staffer.cli.interactive.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        with patch('staffer.cli.interactive.load_session', return_value=[]):
            with patch('staffer.cli.interactive.save_session'):
                from staffer.cli import interactive
                
                # Capture printed output
                with patch('builtins.print') as mock_print:
                    with patch('builtins.input', side_effect=['/help', 'exit']):
                        interactive.main()
                
                # Verify help info was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
                help_output = ' '.join(str(call) for call in print_calls)
                
                # Should list available commands
                assert "/reset" in help_output
                assert "/session" in help_output
                assert "/help" in help_output


def test_unknown_slash_command_shows_error():
    """Test unknown /command shows helpful error message."""
    from tests.conftest import FakeGeminiClient
    
    with patch('staffer.cli.interactive.get_client') as mock_get_client:
        fake_client = FakeGeminiClient()
        mock_get_client.return_value = fake_client
        
        with patch('staffer.cli.interactive.load_session', return_value=[]):
            with patch('staffer.cli.interactive.save_session'):
                from staffer.cli import interactive
                
                # Capture printed output
                with patch('builtins.print') as mock_print:
                    with patch('builtins.input', side_effect=['/unknown', 'exit']):
                        interactive.main()
                
                # Verify error message was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
                output = ' '.join(str(call) for call in print_calls)
                
                # Should show error and suggest /help
                assert "Unknown command" in output or "command" in output.lower()
                assert "/help" in output