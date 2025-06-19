import os
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from .available_functions import get_available_functions, call_function

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

def process_prompt(prompt, verbose=False):
    """Process a single prompt using the AI agent."""
    working_directory = os.getcwd()
    available_functions = get_available_functions(working_directory)

    if verbose:
        print(f"Working directory: {working_directory}")
        print(f"User prompt: {prompt}")

    system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

    messages = [
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ]

    for i in range(20):
        function_called = False
        res = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt
            )   
        )    

        promptTokens = res.usage_metadata.prompt_token_count
        responseTokens = res.usage_metadata.candidates_token_count

        if res.candidates:
            for candidate in res.candidates:
                for part in candidate.content.parts:
                    messages.append(part)
                    if part.function_call:
                        function_called = True
                        if verbose:
                            function_call_result = call_function(part.function_call, working_directory, verbose=True)
                        else:
                            function_call_result = call_function(part.function_call, working_directory)
                        if not function_call_result.parts[0].function_response.response:
                            sys.exit(1)
                        else:
                            messages.append(types.Content(
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