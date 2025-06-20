import os
import argparse
import re
from pathlib import Path
from google.genai import types
import sys
from .available_functions import get_available_functions, call_function
from .llm import get_client

def prune_stale_dir_msgs(msgs, cwd: Path):
    """Filter stale directory context with ancestor path detection. Returns new list, no mutation."""
    cwd_str = str(cwd)
    
    # Get all ancestor paths to filter out
    ancestor_paths = []
    current = cwd.parent
    while current != current.parent:  # Stop at filesystem root
        ancestor_paths.append(str(current))
        current = current.parent
    
    kept = []
    for m in msgs:
        skip_message = False
        
        if m.role == "model" and m.parts:
            text = m.parts[0].text or ""
            
            # Drop old cwd headers
            if "[Working directory:" in text and cwd_str not in text:
                skip_message = True
                
            # Drop messages that reference ancestor paths but not current path
            elif cwd_str not in text:
                for ancestor_path in ancestor_paths:
                    if ancestor_path in text:
                        skip_message = True
                        break
                
        # Enhanced tool response filtering
        elif m.role == "tool" and m.parts:
            fc = getattr(m.parts[0], "function_response", None)
            if fc and getattr(fc, "name", "") == "get_files_info":
                result = str(getattr(fc, "response", {}).get("result", ""))
                # Drop tool responses from ancestor directories
                if not result.startswith(cwd_str):
                    for ancestor_path in ancestor_paths:
                        if ancestor_path in result:
                            skip_message = True
                            break
        
        if not skip_message:
            kept.append(m)
    
    return kept


def build_prompt(messages, working_directory=None):
    """Build system prompt with working directory and function info."""
    if working_directory is None:
        working_directory = Path.cwd()
    else:
        working_directory = Path(working_directory)
    
    # Double header weight for salience without per-turn spam
    cwd_header_1 = f"[cwd: {working_directory}]"
    cwd_header_2 = f"⚠️ You are now working in {working_directory}. Always answer with this full path."
    
    return f"""{cwd_header_1}
{cwd_header_2}

You are a helpful AI coding agent working in: {working_directory}

When asked about your location or "where you are", you should state: {working_directory}

You can perform the following operations:

- List files and directories using get_files_info()
- Read file contents using get_file_content(path)  
- Execute Python files using run_python_file(path, args)
- Write or overwrite files using write_file(path, content)

All paths you provide should be relative to the working directory: {working_directory}

You have access to these functions - use them confidently to explore directories, read files, and accomplish tasks."""


def process_prompt(prompt, verbose=False, messages=None):
    """Process a single prompt using the AI agent."""
    if messages is None:
        messages = []
    working_directory = Path(os.getcwd())
    available_functions = get_available_functions(str(working_directory))

    if verbose:
        print(f"Working directory: {working_directory}")
        print(f"User prompt: {prompt}")

    # Filter stale directory context from conversation history
    clean_messages = prune_stale_dir_msgs(messages, working_directory)
    system_prompt = build_prompt(clean_messages, working_directory)

    # Add current user prompt to cleaned messages
    current_message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )
    clean_messages.append(current_message)

    client = get_client()
    
    for i in range(20):
        function_called = False
        res = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=clean_messages,
            config=types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt
            )   
        )    

        promptTokens = res.usage_metadata.prompt_token_count
        responseTokens = res.usage_metadata.candidates_token_count

        if res.candidates:
            for candidate in res.candidates:
                # Add assistant response to cleaned message history
                clean_messages.append(candidate.content)
                for part in candidate.content.parts:
                    if part.function_call:
                        function_called = True
                        if verbose:
                            function_call_result = call_function(part.function_call, working_directory, verbose=True)
                        else:
                            function_call_result = call_function(part.function_call, working_directory)
                        if not function_call_result.parts[0].function_response.response:
                            sys.exit(1)
                        else:
                            clean_messages.append(types.Content(
                                role="tool",
                                parts=[types.Part(function_response=types.FunctionResponse(
                                    name=part.function_call.name,
                                    response=function_call_result.parts[0].function_response.response
                                ))]
                            ))
            if not function_called:
                print(f"-> {res.text}")
                break
        i+=1

    if verbose:
        print(f"Prompt tokens: {promptTokens}")
        print(f"Response tokens: {responseTokens}")
    
    return clean_messages


def main():
    parser = argparse.ArgumentParser(
        description="Staffer - AI coding agent that works in any directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  staffer "analyze this codebase"
  staffer "fix the bug in main.py" --verbose
  staffer "create a test file for the utils module"
  staffer --interactive """
    )
    parser.add_argument("prompt", nargs='?', help="The task or question for the AI agent")
    parser.add_argument("--verbose", action="store_true", help="Show detailed function call information")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")
    parser.add_argument("--version", action="version", version="Staffer 0.1.0")
    
    args = parser.parse_args()
    
    # Handle interactive mode
    if args.interactive:
        from .cli.interactive import main as interactive_main
        interactive_main()
        return
    
    # Require prompt for single command mode
    if not args.prompt:
        parser.error("prompt is required unless using --interactive mode")
    
    process_prompt(args.prompt, args.verbose)

if __name__ == "__main__":
    main()