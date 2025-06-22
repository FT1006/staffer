"""Tests for interactive mode functionality."""

import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_interactive_mode_basic_loop():
    """Test that interactive mode actually enters loop and calls terminal UI input."""
    # Mock the genai client at module level to prevent API key errors
    with patch('google.genai.Client') as mock_client:
        mock_client.return_value = MagicMock()
        
        # Mock the process_prompt to avoid API calls in tests
        with patch('staffer.cli.interactive.process_prompt') as mock_process:
            # Use factory to create mock terminal UI
            from tests.factories import mock_terminal_ui
            with patch('staffer.cli.interactive.get_terminal_ui') as mock_get_terminal:
                # Handle directory change prompt (if needed) + main interactive input  
                mock_terminal = mock_terminal_ui(['n', 'exit'])  # New session if prompted, then exit
                mock_get_terminal.return_value = mock_terminal
                
                from staffer.cli import interactive
                result = interactive.main()
                
                # Proves we entered the loop and actually called terminal UI
                mock_terminal.get_input.assert_called()
                assert result is None


def test_interactive_prompt_shows(capsys):
    """Test that interactive mode shows proper welcome and uses terminal UI."""
    # Mock the genai client at module level to prevent API key errors
    with patch('google.genai.Client') as mock_client:
        mock_client.return_value = MagicMock()
        
        # Mock the process_prompt to avoid API calls in tests
        with patch('staffer.cli.interactive.process_prompt'):
            # Use factory to create mock terminal UI
            from tests.factories import mock_terminal_ui
            with patch('staffer.cli.interactive.get_terminal_ui') as mock_get_terminal:
                # Handle directory change prompt (if needed) + main interactive input
                mock_terminal = mock_terminal_ui(['n', 'exit'])  # New session if prompted, then exit
                mock_get_terminal.return_value = mock_terminal
                
                from staffer.cli import interactive
                interactive.main()
                
                # Verify terminal UI methods were called
                mock_terminal.display_welcome.assert_called_once()
                mock_terminal.get_input.assert_called()


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
                        ['msg1', 'msg2'],  # Second call returns 2 messages  
                        ['msg1', 'msg2', 'msg3']  # Third call (if needed) returns 3 messages
                    ]
                    
                    # Use factory to create mock terminal UI
                    from tests.factories import mock_terminal_ui
                    with patch('staffer.cli.interactive.get_terminal_ui') as mock_get_terminal:
                        # Handle directory change prompt + 2 interactive inputs + exit
                        mock_terminal = mock_terminal_ui(['n', 'hello', 'what is my name?', 'exit'])
                        mock_get_terminal.return_value = mock_terminal
                        
                        from staffer.cli import interactive
                        interactive.main()

                    # Verify process_prompt was called for user inputs (might be 2 or 3 depending on session state)
                    assert mock_process.call_count >= 2, f"Expected at least 2 calls, got {mock_process.call_count}"

                    # Check the arguments passed to each call
                    first_call = mock_process.call_args_list[0]
                    second_call = mock_process.call_args_list[1]

                    # First call should have minimal messages (just working dir init)
                    first_messages = first_call.kwargs['messages']
                    
                    # Second call should have the history from first call
                    second_messages = second_call.kwargs['messages']
                    assert len(second_messages) == 1, "Second call should receive history from first call"
                    assert second_messages == ['msg1']