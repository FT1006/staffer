"""Enhanced terminal UI for Staffer interactive mode."""

from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.syntax import Syntax
from yaspin import yaspin


class TerminalUI:
    """Enhanced terminal interface with rich features."""
    
    def __init__(self):
        """Initialize the terminal UI components."""
        self.console = Console()
        # Create history file in user's home directory
        history_path = Path.home() / '.staffer' / 'command_history'
        history_path.parent.mkdir(exist_ok=True)
        self.history = FileHistory(str(history_path))
        
    def get_input(self, session_info: dict) -> str:
        """Get user input with rich prompt and history.
        
        Args:
            session_info: Dictionary with session information like cwd, message_count
            
        Returns:
            User input string
        """
        prompt_text = self._build_prompt(session_info)
        return prompt(
            prompt_text,
            history=self.history,
            multiline=False,
            wrap_lines=True
        )
    
    def _build_prompt(self, session_info: dict) -> str:
        """Build contextual prompt string.
        
        Args:
            session_info: Dictionary with session information
            
        Returns:
            Formatted prompt string
        """
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
        """Shorten a path for display.
        
        Args:
            path: Full path string
            
        Returns:
            Shortened path string
        """
        path_obj = Path(path)
        home = Path.home()
        
        # Replace home directory with ~
        try:
            relative = path_obj.relative_to(home)
            return f"~/{relative}"
        except ValueError:
            # Not under home directory
            parts = path_obj.parts
            if len(parts) > 3:
                # Show first and last two parts
                return f"{parts[0]}/.../{parts[-2]}/{parts[-1]}"
            return str(path_obj)
    
    def show_spinner(self, message: str):
        """Show processing spinner.
        
        Args:
            message: Message to display with spinner
            
        Returns:
            Spinner context manager
        """
        return yaspin(text=message, color="cyan")
    
    def display_code(self, code: str, language: str = "python"):
        """Display syntax-highlighted code.
        
        Args:
            code: Code string to display
            language: Programming language for syntax highlighting
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def display_success(self, message: str):
        """Display success message.
        
        Args:
            message: Success message to display
        """
        self.console.print(f"✅ {message}", style="green")
    
    def display_warning(self, message: str):
        """Display warning message.
        
        Args:
            message: Warning message to display
        """
        self.console.print(f"⚠️  {message}", style="yellow")
    
    def display_error(self, message: str):
        """Display error message.
        
        Args:
            message: Error message to display
        """
        self.console.print(f"❌ {message}", style="red")
    
    def display_function_call(self, function_name: str):
        """Display function call indicator.
        
        Args:
            function_name: Name of the function being called
        """
        self.console.print(f"🔧 Calling {function_name}...", style="dim")
    
    def print(self, text: str, style: str = None):
        """Print text with optional style.
        
        Args:
            text: Text to print
            style: Optional rich style string
        """
        self.console.print(text, style=style)