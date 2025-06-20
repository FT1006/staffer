"""Tests for interactive mode terminal UI integration."""

import pytest
from unittest.mock import Mock, patch


def test_interactive_loop_uses_terminal_ui():
    """Smoke test that interactive.main() delegates input/output to TerminalUI."""
    from staffer.cli import interactive
    
    # Minimal stub to track calls
    class DummyUI:
        def __init__(self):
            self.calls = []
            
        def get_input(self, info):
            self.calls.append(("get_input", info))
            return "exit"
            
        def show_spinner(self, msg):
            class _Spinner:
                def __enter__(inner_self):
                    self.calls.append(("spinner_enter", msg))
                    return inner_self
                def __exit__(inner_self, *args):
                    self.calls.append(("spinner_exit", msg))
            return _Spinner()
            
        def print(self, text, style=None):
            self.calls.append(("print", text, style))
            
        def display_success(self, msg):
            self.calls.append(("success", msg))
    
    dummy = DummyUI()
    
    with patch.object(interactive, 'TerminalUI', return_value=dummy):
        with patch.object(interactive, 'process_prompt', return_value=[]):
            with patch.object(interactive, 'load_session', return_value=[]):
                with patch.object(interactive, 'save_session'):
                    with patch.object(interactive, 'get_client', return_value=Mock()):
                        interactive.main()
    
    # Verify we actually used the UI object
    assert any(call[0] == "get_input" for call in dummy.calls), "Should use TerminalUI.get_input"
    assert any(call[0] == "print" for call in dummy.calls), "Should use TerminalUI.print"