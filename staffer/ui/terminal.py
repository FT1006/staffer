"""Enhanced terminal UI for Staffer interactive mode."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import nullcontext

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.shortcuts import confirm
    from rich.console import Console
    from rich.syntax import Syntax
    from yaspin import yaspin
    ENHANCED_MODE_AVAILABLE = True
except ImportError:
    ENHANCED_MODE_AVAILABLE = False


class TerminalUI:
    """Enhanced terminal interface with rich features."""
    
    def __init__(self):
        if not ENHANCED_MODE_AVAILABLE:
            raise ImportError("Enhanced terminal features not available. Install: pip install prompt-toolkit rich yaspin")
        
        self.console = Console()
        
        # Create history directory if it doesn't exist
        history_dir = Path.home() / '.staffer'
        history_dir.mkdir(exist_ok=True)
        self.history = FileHistory(str(history_dir / 'command_history'))
        
    def get_input(self, session_info: Dict[str, Any]) -> str:
        """Get user input with rich prompt and history."""
        prompt_text = self._build_prompt(session_info)
        return prompt(
            prompt_text,
            history=self.history,
            multiline=False,
            wrap_lines=True
        )
    
    def _build_prompt(self, session_info: Dict[str, Any]) -> str:
        """Build contextual prompt string."""
        cwd = session_info.get('cwd', '~')
        msg_count = session_info.get('message_count', 0)
        
        # Shorten directory path
        short_cwd = self._shorten_path(cwd)
        
        # Build status indicators
        status = f"[{msg_count} msgs]"
        if msg_count > 40:  # High token warning
            status += " ⚠️"
            
        return f"staffer {short_cwd} {status}> "
    
    def _shorten_path(self, path: str) -> str:
        """Shorten path for display in prompt."""
        home = str(Path.home())
        if path.startswith(home):
            path = path.replace(home, '~', 1)
        
        # Keep only last 2 directories if path is too long
        parts = Path(path).parts
        if len(parts) > 3:
            return str(Path(*parts[-2:]))
        return path
    
    def show_spinner(self, message: str):
        """Show processing spinner."""
        return yaspin(text=message, color="cyan")
    
    def display_code(self, code: str, language: str = "python"):
        """Display syntax-highlighted code."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def display_success(self, message: str):
        """Display success message."""
        self.console.print(f"✅ {message}", style="green")
    
    def display_warning(self, message: str):
        """Display warning message."""
        self.console.print(f"⚠️  {message}", style="yellow")
    
    def display_error(self, message: str):
        """Display error message."""
        self.console.print(f"❌ {message}", style="red")
    
    def display_function_call(self, function_name: str):
        """Display function call indicator."""
        self.console.print(f"🔧 Calling {function_name}...", style="dim cyan")
    
    def display_ai_response(self, response: str):
        """Display AI response with potential code highlighting."""
        # Simple code block detection and highlighting
        lines = response.split('\n')
        in_code_block = False
        code_lines = []
        language = "text"
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_lines:
                        code = '\n'.join(code_lines)
                        self.display_code(code, language)
                        code_lines = []
                    in_code_block = False
                else:
                    # Start of code block
                    language = line.strip()[3:] or "text"
                    in_code_block = True
            elif in_code_block:
                code_lines.append(line)
            else:
                # Regular text
                if line.strip():
                    self.console.print(line)
                else:
                    self.console.print()
        
        # Handle unterminated code block
        if in_code_block and code_lines:
            code = '\n'.join(code_lines)
            self.display_code(code, language)
    
    def display_welcome(self):
        """Display welcome message."""
        self.console.print("🚀 Staffer - AI in Folders", style="bold blue")
        self.console.print("Enhanced terminal mode enabled", style="dim")


class BasicTerminalUI:
    """Fallback terminal interface for environments without rich features."""
    
    def get_input(self, session_info: Dict[str, Any]) -> str:
        """Get basic user input."""
        msg_count = session_info.get('message_count', 0)
        return input(f"staffer [{msg_count} msgs]> ")
    
    def show_spinner(self, message: str):
        """Basic processing indicator."""
        print(f"⚡ {message}")
        # Return a no-op context manager for compatibility
        return nullcontext()
    
    def display_code(self, code: str, language: str = "python"):
        """Display code without highlighting."""
        print(code)
    
    def display_success(self, message: str):
        """Display success message."""
        print(f"✅ {message}")
    
    def display_warning(self, message: str):
        """Display warning message."""
        print(f"⚠️  {message}")
    
    def display_error(self, message: str):
        """Display error message."""
        print(f"❌ {message}")
    
    def display_function_call(self, function_name: str):
        """Display function call indicator."""
        print(f"🔧 Calling {function_name}...")
    
    def display_ai_response(self, response: str):
        """Display AI response as plain text."""
        print(response)
    
    def display_welcome(self):
        """Display welcome message."""
        print("🚀 Staffer - AI in Folders")
        print("Basic terminal mode")


def get_terminal_ui() -> 'TerminalUI':
    """Get appropriate terminal UI based on available features."""
    if ENHANCED_MODE_AVAILABLE:
        try:
            return TerminalUI()
        except Exception:
            pass
    
    return BasicTerminalUI()