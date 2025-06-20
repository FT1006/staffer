"""Unit tests for TerminalUI features."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile


class TestTerminalUIFeatures:
    """Test individual TerminalUI features in isolation."""
    
    def test_command_history_persistence(self, tmp_path):
        """Test that command history is persisted between sessions."""
        from staffer.ui.terminal import TerminalUI
        
        # Use temp directory for history
        history_file = tmp_path / ".staffer" / "command_history"
        
        with patch('staffer.ui.terminal.Path.home', return_value=tmp_path):
            # First session - add commands
            ui1 = TerminalUI()
            
            # Simulate adding commands to history
            with patch('prompt_toolkit.prompt', side_effect=["cmd1", "cmd2", "exit"]) as mock_prompt:
                ui1.get_input({})
                ui1.get_input({})
                
            # Second session - history should be available
            ui2 = TerminalUI()
            # Verify history file was created
            assert history_file.exists()
    
    def test_prompt_building_with_context(self):
        """Test rich prompt includes directory and message count."""
        from staffer.ui.terminal import TerminalUI
        
        ui = TerminalUI()
        
        # Test basic prompt
        session_info = {
            'cwd': '/home/user/project',
            'message_count': 5
        }
        prompt = ui._build_prompt(session_info)
        
        assert '~/project' in prompt  # Path shortened
        assert '[5 msgs]' in prompt  # Message count shown
        assert 'staffer' in prompt  # App name
        
    def test_high_token_warning_in_prompt(self):
        """Test warning indicator appears for high message count."""
        from staffer.ui.terminal import TerminalUI
        
        ui = TerminalUI()
        
        # Test high message count warning
        session_info = {
            'cwd': '/home/user/project',
            'message_count': 45  # > 40 threshold
        }
        prompt = ui._build_prompt(session_info)
        
        assert '⚠️' in prompt  # Warning emoji
        assert '[45 msgs]' in prompt
        
    def test_spinner_context_manager(self):
        """Test spinner works as context manager."""
        from staffer.ui.terminal import TerminalUI
        
        ui = TerminalUI()
        
        # Test spinner creation
        spinner = ui.show_spinner("Processing...")
        
        # Should be a context manager
        assert hasattr(spinner, '__enter__')
        assert hasattr(spinner, '__exit__')
        
    def test_display_methods_format_correctly(self):
        """Test display methods add proper formatting."""
        from staffer.ui.terminal import TerminalUI
        
        ui = TerminalUI()
        
        # Mock the console to capture output
        ui.console = Mock()
        
        # Test success message
        ui.display_success("Operation complete")
        ui.console.print.assert_called_with("✅ Operation complete", style="green")
        
        # Test warning message
        ui.display_warning("High memory usage")
        ui.console.print.assert_called_with("⚠️  High memory usage", style="yellow")
        
        # Test error message
        ui.display_error("File not found")
        ui.console.print.assert_called_with("❌ File not found", style="red")
        
    def test_syntax_highlighting(self):
        """Test code display with syntax highlighting."""
        from staffer.ui.terminal import TerminalUI
        from rich.syntax import Syntax
        
        ui = TerminalUI()
        ui.console = Mock()
        
        # Test code display
        code = "def hello():\n    print('world')"
        ui.display_code(code, "python")
        
        # Verify Syntax object was created and printed
        ui.console.print.assert_called_once()
        syntax_arg = ui.console.print.call_args[0][0]
        assert isinstance(syntax_arg, Syntax)
        
    def test_path_shortening(self):
        """Test path shortening for display."""
        from staffer.ui.terminal import TerminalUI
        
        ui = TerminalUI()
        
        # Test home directory replacement
        home = str(Path.home())
        assert ui._shorten_path(home + "/projects/myapp") == "~/projects/myapp"
        
        # Test long path shortening
        long_path = "/very/long/path/to/deeply/nested/directory"
        shortened = ui._shorten_path(long_path)
        assert "..." in shortened
        assert shortened.startswith("/very/")
        assert shortened.endswith("/nested/directory")