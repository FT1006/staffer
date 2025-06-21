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
        
        # Test show_spinner returns None for basic UI
        assert ui.show_spinner("Loading...") is None


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