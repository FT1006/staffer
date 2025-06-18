# Staffer - CLI & File-based AI Agent

Staffer is an intelligent AI assistant that uses Google's Gemini AI model to help with Python development tasks. It operates as a command-line agent that can interact with files, execute code, and perform development workflows within a secure sandbox environment.

## Features

- **Agentic AI Loop**: Performs up to 20 iterations of reasoning and action-taking
- **Secure Sandbox**: All operations are constrained to the `calculator/` working directory
- **File Operations**: Read, write, and execute Python files with safety constraints
- **Function Calling**: Uses Google's Gemini function calling for structured interactions
- **Token Tracking**: Monitors AI model usage for performance analysis

## Prerequisites

- Python 3.x
- Google Gemini API key

## Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd staffer
   ```
2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment**

   ```bash
   # Create .env file with your Gemini API key
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

## Usage

Run Staffer with natural language prompts:

```bash
# Basic usage
python main.py "Create a simple Python calculator"

# Verbose mode for debugging
python main.py "Run the tests for the calculator" --verbose

# Complex development tasks
python main.py "Add multiplication support to the calculator and write tests for it"
```

## Architecture

### Core Components

- **`main.py`**: Command-line interface and agentic loop controller
- **`available_functions.py`**: Function registry and security enforcement
- **`functions/`**: Sandboxed file system operations
  - `get_files_info.py`: Directory listing and file information
  - `get_file_content.py`: File reading with size limits
  - `write_file.py`: File creation and modification
  - `run_python_file.py`: Python code execution with timeout
- **`calculator/`**: Example application demonstrating capabilities

### Security Model

- **Directory Sandboxing**: All operations restricted to `calculator/` subdirectory
- **Path Validation**: Prevents directory traversal attacks
- **Execution Limits**: 30-second timeout for Python file execution
- **File Size Limits**: 10,000 character limit for file reading

### Available Functions

The AI agent can perform these operations:

| Function             | Description             | Constraints            |
| -------------------- | ----------------------- | ---------------------- |
| `get_files_info`   | List directory contents | Sandbox directory only |
| `get_file_content` | Read file contents      | Max 10,000 characters  |
| `write_file`       | Create/modify files     | Sandbox directory only |
| `run_python_file`  | Execute Python scripts  | 30-second timeout      |

## Example Application

The included calculator demonstrates Staffer's capabilities:

- **Expression Evaluation**: Handles complex mathematical expressions
- **ASCII Art Rendering**: Decorative output formatting
- **Comprehensive Testing**: Full unit test coverage
- **Command-line Interface**: User-friendly calculator tool

```bash
# Try the calculator
cd calculator
python main.py "2 + 3 * 4"
```

## Development

### Testing

```bash
# Run main tests
python tests.py

# Run calculator tests
python calculator/tests.py
```

### Adding New Functions

1. Create function implementation in `functions/`
2. Add function schema to `available_functions.py`
3. Register function in the `AVAILABLE_FUNCTIONS` dictionary
4. Test with the AI agent

## Dependencies

- **`google-genai==1.12.1`**: Google Gemini AI SDK
- **`python-dotenv==1.1.0`**: Environment variable management

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `GEMINI_API_KEY` is set in your environment
2. **Permission Errors**: Check that the `calculator/` directory is writable
3. **Timeout Issues**: Long-running Python scripts will timeout after 30 seconds

### Debug Mode

Use the `--verbose` flag to see detailed AI reasoning and function call traces:

```bash
python main.py "your prompt here" --verbose
```
