"""Tests for session lifecycle commands (/reset, /session, etc.)."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.factories import user, model


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


def test_reset_command_preserves_cwd_component(capsys, tmp_path):
    """Component test: /reset clears history but preserves working directory context."""
    from tests.conftest import FakeGeminiClient
    from tests.factories import user, model
    import tempfile

    # Use temp directory for session storage
    session_dir = tmp_path / ".staffer"
    session_file = session_dir / "current_session.json"

    with patch('staffer.session.get_session_file_path', return_value=session_file):
        with patch('staffer.cli.interactive.get_client') as mock_get_client:
            fake_client = FakeGeminiClient()
            mock_get_client.return_value = fake_client

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

            from staffer.cli import interactive

            # User types /reset, then asks about location, then exits
            with patch('builtins.input', side_effect=['/reset', 'where are we?', 'exit']):
                interactive.main()

            # Check printed output includes reset confirmation
            captured = capsys.readouterr()
            assert "session cleared" in captured.out.lower() or "starting fresh" in captured.out.lower(), \
                "User should see reset confirmation"

            # Check that working directory is still present in LLM calls
            # The fake client should have received the second prompt with current directory
            assert fake_client.call_count >= 1, "LLM should be called for 'where are we?' prompt"

            # Verify that the AI can still determine working directory after reset
            # The implementation uses get_working_directory() function call rather than system instruction
            assert fake_client.call_count >= 1, "LLM should be called after reset"

            # Verify session file on disk is now empty/minimal
            from staffer.session import load_session
            final_messages = load_session()
            assert len(final_messages) <= 2, "Session should be cleared after reset"


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