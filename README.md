# Staffer - Global AI Coding Agent

Staffer is an intelligent AI assistant that uses Google's Gemini AI model to help with development tasks in any directory. It operates as a global command-line agent that can interact with files, execute code, and perform development workflows within the current working directory.

## Features

- **Global CLI Tool**: Works in any directory, automatically detects working directory
- **Interactive Mode**: Continuous conversation mode for iterative development
- **Single Command Mode**: Quick one-off tasks and automation
- **Agentic AI Loop**: Performs up to 20 iterations of reasoning and action-taking
- **Secure Operations**: All operations are constrained to the current working directory
- **File Operations**: Read, write, and execute Python files with safety constraints
- **Function Calling**: Uses Google's Gemini function calling for structured interactions
- **Token Tracking**: Monitors AI model usage for performance analysis

## Prerequisites

- Python 3.8+
- Google Gemini API key (get one at [Google AI Studio](https://aistudio.google.com/app/apikey))

## Installation

### Step 1: Clone and Install

```bash
git clone https://github.com/your-username/staffer.git
cd staffer
pip install -e .
```

### Step 2: Set up API Key

Create a `.env` file in the staffer directory with your Gemini API key:

```bash
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

Or set it as an environment variable:

```bash
export GEMINI_API_KEY=your_actual_api_key_here
```

## Usage

Once installed, you can use `staffer` command from anywhere:

### Single Command Mode (default)

```bash
# Navigate to any project directory
cd /path/to/your/project

# Use Staffer with natural language prompts
staffer "analyze this codebase"
staffer "create a simple Python calculator"
staffer "run the tests and fix any failures"

# Verbose mode for debugging
staffer "Add multiplication support to the calculator" --verbose

# Get help
staffer --help
```

### Interactive Mode

For ongoing conversations and iterative development:

```bash
# Start interactive mode
staffer --interactive

# Example interactive session:
staffer> what files are in this project?
-> [AI analyzes and lists files]

staffer> explain the main.py file
-> [AI reads and explains the code]

staffer> add error handling to the API functions
-> [AI implements error handling]

staffer> exit
Goodbye!
```

## Examples

```bash
# Web development
cd my-website
staffer "optimize the CSS for better performance"

# Python projects
cd my-python-app
staffer "add type hints to all functions in main.py"

# Data analysis
cd data-project
staffer "create a visualization of the sales data in data.csv"

# DevOps
cd infrastructure
staffer "update the Docker configuration for production"
```

## Architecture

### Core Components

- **`staffer/cli.py`**: Command-line entry point
- **`staffer/main.py`**: Main application logic and agentic loop
- **`staffer/available_functions.py`**: Function registry and security enforcement
- **`staffer/functions/`**: Sandboxed file system operations
  - `get_files_info.py`: Directory listing and file information
  - `get_file_content.py`: File reading with size limits
  - `write_file.py`: File creation and modification
  - `run_python_file.py`: Python code execution with timeout

### Security Model

- **Directory Sandboxing**: All operations restricted to current working directory
- **Path Validation**: Prevents directory traversal attacks  
- **Execution Limits**: 30-second timeout for Python file execution
- **File Size Limits**: 10,000 character limit for file reading

### Available Functions

The AI agent can perform these operations:

| Function             | Description             | Constraints                    |
| -------------------- | ----------------------- | ------------------------------ |
| `get_files_info`   | List directory contents | Current directory and subdirs  |
| `get_file_content` | Read file contents      | Max 10,000 characters         |
| `write_file`       | Create/modify files     | Current directory and subdirs  |
| `run_python_file`  | Execute Python scripts  | 30-second timeout             |

## Development

### Testing

```bash
# Test the original calculator example
cd calculator
python tests.py

# Test the CLI tool in any directory
staffer "list files in this directory" --verbose

# Test with the included calculator project
cd calculator
staffer "explain how the calculator works"
```

### Adding New Functions

1. Create function implementation in `staffer/functions/`
2. Add function schema to `staffer/available_functions.py`
3. Register function in the function dictionary
4. Test with the AI agent

## Dependencies

- **`google-genai==1.12.1`**: Google Gemini AI SDK
- **`python-dotenv==1.1.0`**: Environment variable management

## Example Project: Calculator

The repository includes a working calculator example in the `calculator/` directory that demonstrates Staffer's capabilities:

```bash
# Navigate to the calculator project
cd calculator

# Let Staffer analyze and explain the code
staffer "analyze this calculator project and explain how it works"

# Ask Staffer to run tests
staffer "run the tests and tell me the results"

# Have Staffer add new features
staffer "add a square root function to the calculator"
```

## Troubleshooting

### Common Issues

1. **Missing API Key**: 
   ```bash
   # Check if API key is set
   echo $GEMINI_API_KEY
   # Or create .env file
   echo "GEMINI_API_KEY=your_key_here" > .env
   ```

2. **Command not found**: 
   ```bash
   # Reinstall in development mode
   pip install -e .
   # Check if staffer is in PATH
   which staffer
   ```

3. **Permission Errors**: Check that the current directory is writable

4. **Timeout Issues**: Long-running Python scripts will timeout after 30 seconds

### Debug Mode

Use the `--verbose` flag to see detailed AI reasoning and function call traces:

```bash
staffer "your prompt here" --verbose
```

This will show:
- Current working directory
- Detailed function calls with arguments
- Token usage statistics

## Comparison with Claude Code

Staffer now provides a similar user experience to Claude Code:

- **Directory Flexibility**: Works in any directory, not hardcoded paths
- **Global Command**: Available system-wide after installation
- **Automatic Context**: Detects and uses current working directory
- **Clean CLI**: Proper argument parsing and help text