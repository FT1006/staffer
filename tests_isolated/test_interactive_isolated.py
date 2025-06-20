"""Isolated tests for interactive mode - require aggressive mocking before CI."""

import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


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

                        # Verify process_prompt was called twice (for two user inputs)
                        assert mock_process.call_count == 2

                        # Verify the second call received the accumulated history
                        second_call_args = mock_process.call_args_list[1]
                        messages_arg = second_call_args[1]['messages']  # keyword argument
                        assert len(messages_arg) == 1, "Second call should receive history from first call"