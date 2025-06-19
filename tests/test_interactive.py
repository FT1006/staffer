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
    # Set dummy API key for subprocess test to avoid auth errors
    env = os.environ.copy()
    env['GEMINI_API_KEY'] = 'dummy_key_for_testing'
    
    result = subprocess.run(
        [sys.executable, "-m", "staffer.main", "--interactive"],
        input="exit\n",
        capture_output=True,
        text=True,
        timeout=10,
        cwd=Path(__file__).parent.parent,
        env=env
    )
    
    assert result.returncode == 0
    assert "Interactive Mode" in result.stdout or "staffer>" in result.stdout


def test_message_history_persistence():
    """Interactive mode should maintain message history between prompts."""
    # Mock the Google AI modules
    with patch.dict(sys.modules, {
        'google': MagicMock(),
        'google.genai': MagicMock(),
    }):
        with patch('google.genai.Client'):
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

                        # First call should have empty messages (fresh session)
                        assert first_call.kwargs['messages'] == []
                        
                        # Second call should have the history from first call
                        assert second_call.kwargs['messages'] == ['msg1']