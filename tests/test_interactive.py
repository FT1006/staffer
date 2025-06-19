"""Tests for interactive mode functionality."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


def test_interactive_mode_basic_loop():
    """Test that interactive mode actually enters loop and calls input."""
    from staffer.cli import interactive
    
    with patch('builtins.input', side_effect=['exit']) as mock_input:
        result = interactive.main()
    
    # Proves we entered the loop and actually called input
    mock_input.assert_called()
    assert result is None


def test_interactive_prompt_shows(capsys):
    """Test that interactive mode shows proper prompt to user."""
    from staffer.cli import interactive
    
    with patch('builtins.input', side_effect=['exit']):
        interactive.main()
    
    # Check real stdout output, not mocked
    captured = capsys.readouterr()
    assert "staffer>" in captured.out


def test_interactive_flag_detection():
    """Test CLI detects --interactive flag and routes to interactive mode."""
    result = subprocess.run(
        [sys.executable, "-m", "staffer.main", "--interactive"],
        input="exit\n",
        capture_output=True,
        text=True,
        timeout=10,
        cwd=Path(__file__).parent.parent
    )
    
    assert result.returncode == 0
    assert "Interactive Mode" in result.stdout or "staffer>" in result.stdout