"""Tests for slice 5 terminal UI enhancements."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from staffer.ui.terminal import TerminalUI, BasicTerminalUI, get_terminal_ui
from tests.factories import user, model


class TestTerminalUI:
    """Test the terminal UI components."""
    
    def test_get_terminal_ui_returns_basic_when_deps_missing(self):
        """Test that get_terminal_ui returns BasicTerminalUI when dependencies are missing."""
        with patch('staffer.ui.terminal.ENHANCED_MODE_AVAILABLE', False):
            ui = get_terminal_ui()
            assert isinstance(ui, BasicTerminalUI)
    
    def test_basic_terminal_ui_methods(self):
        """Test basic terminal UI provides all required methods."""
        ui = BasicTerminalUI()
        
        # Test get_input
        with patch('builtins.input', return_value='test input'):
            session_info = {'message_count': 5}
            result = ui.get_input(session_info)
            assert result == 'test input'
        
        # Test display methods (just ensure they don't crash)
        ui.display_welcome()
        ui.display_success("Success!")
        ui.display_warning("Warning!")
        ui.display_error("Error!")
        ui.display_function_call("test_function")
        ui.display_ai_response("Test response")
        ui.display_code("print('hello')", "python")
        
        # Test show_spinner returns a context manager
        spinner = ui.show_spinner("Loading...")
        assert spinner is not None
        # Test it works as context manager
        with spinner:
            pass  # Should not raise
    
    def test_enhanced_terminal_ui_prompt_building(self):
        """Test enhanced terminal prompt building with path shortening."""
        # This test will only run if dependencies are available
        try:
            ui = TerminalUI()
        except ImportError:
            pytest.skip("Enhanced terminal dependencies not available")
        
        # Test home directory shortening
        from pathlib import Path
        home = str(Path.home())
        
        session_info = {
            'cwd': home + '/projects/myapp',
            'message_count': 10
        }
        prompt = ui._build_prompt(session_info)
        assert '~/projects/myapp' in prompt
        assert '[10 msgs]' in prompt
        
        # Test high message count warning
        session_info['message_count'] = 50
        prompt = ui._build_prompt(session_info)
        assert '⚠️' in prompt
        
        # Test path shortening for deep paths
        session_info['cwd'] = '/very/long/path/to/some/deep/directory'
        prompt = ui._build_prompt(session_info)
        assert 'deep/directory' in prompt
    
    def test_enhanced_terminal_ai_response_parsing(self):
        """Test AI response parsing with code block detection."""
        try:
            ui = TerminalUI()
        except ImportError:
            pytest.skip("Enhanced terminal dependencies not available")
        
        # Mock the console to capture output
        with patch.object(ui, 'console') as mock_console, \
             patch.object(ui, 'display_code') as mock_display_code:
            
            # Test response with code block
            response = """Here's a Python function:

```python
def hello():
    print("Hello, World!")
```

That's the code!"""
            
            ui.display_ai_response(response)
            
            # Verify code was displayed with syntax highlighting
            mock_display_code.assert_called_once_with(
                'def hello():\n    print("Hello, World!")',
                'python'
            )


class TestTerminalUIIntegration:
    """Test terminal UI integration with interactive mode."""
    
    def test_interactive_mode_with_terminal(self, fake_llm, temp_cwd):
        """Test that interactive mode properly integrates terminal UI."""
        # Create test files
        (temp_cwd / "test.py").write_text("print('hello')")
        
        # Mock terminal UI with controlled inputs
        mock_terminal = Mock(spec=BasicTerminalUI)
        mock_terminal.get_input.side_effect = ['list files', 'exit']
        mock_terminal.show_spinner.return_value = MagicMock(__enter__=Mock(), __exit__=Mock())
        
        # Mock session functions
        with patch('staffer.cli.interactive.get_terminal_ui', return_value=mock_terminal), \
             patch('staffer.cli.interactive.load_session', return_value=[]), \
             patch('staffer.cli.interactive.save_session'):
            
            # Import and run interactive mode
            from staffer.cli.interactive import main
            main()
        
        # Verify terminal UI methods were called appropriately
        mock_terminal.display_welcome.assert_called_once()
        assert mock_terminal.get_input.call_count == 2
        
        # Verify success messages
        success_calls = [call[0][0] for call in mock_terminal.display_success.call_args_list]
        assert any("Type 'exit' or 'quit'" in call for call in success_calls)
        assert "Session saved" in success_calls
        assert "Goodbye!" in success_calls
    
    def test_process_prompt_with_terminal(self, fake_llm, temp_cwd):
        """Test that process_prompt uses terminal for visual feedback."""
        mock_terminal = Mock(spec=BasicTerminalUI)
        
        # Configure fake LLM to call a function
        fake_llm.gemini.fc_name = "get_files_info"
        fake_llm.gemini.call_function_once = True
        
        from staffer.main import process_prompt
        
        # Process a prompt with terminal
        messages = process_prompt("list files", terminal=mock_terminal)
        
        # Verify function call was displayed
        mock_terminal.display_function_call.assert_called_with("get_files_info")
        
        # Verify AI response was displayed through terminal
        mock_terminal.display_ai_response.assert_called()
    
    def test_terminal_graceful_fallback(self):
        """Test that terminal falls back gracefully when enhanced mode fails."""
        # Force enhanced mode to be available but fail on instantiation
        with patch('staffer.ui.terminal.ENHANCED_MODE_AVAILABLE', True), \
             patch('staffer.ui.terminal.TerminalUI', side_effect=Exception("Failed")):
            
            ui = get_terminal_ui()
            assert isinstance(ui, BasicTerminalUI)
    
    def test_spinner_context_manager(self):
        """Test spinner works as context manager in basic mode."""
        ui = BasicTerminalUI()
        
        # Basic UI spinner returns None, so context manager should be no-op
        with ui.show_spinner("Processing...") as spinner:
            assert spinner is None
    
    def test_terminal_ui_with_empty_session(self, fake_llm, temp_cwd):
        """Test terminal UI handles empty session correctly."""
        mock_terminal = Mock(spec=BasicTerminalUI)
        mock_terminal.get_input.side_effect = ['exit']
        mock_terminal.show_spinner.return_value = MagicMock(__enter__=Mock(), __exit__=Mock())
        
        with patch('staffer.cli.interactive.get_terminal_ui', return_value=mock_terminal), \
             patch('staffer.cli.interactive.load_session', return_value=[]), \
             patch('staffer.cli.interactive.save_session'):
            
            from staffer.cli.interactive import main
            main()
        
        # Should not show "restored conversation" message for empty session
        success_calls = [call[0][0] for call in mock_terminal.display_success.call_args_list]
        assert not any("Restored conversation" in call for call in success_calls)