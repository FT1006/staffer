"""Interactive mode for Staffer - continuous prompt loop."""

import os
from pathlib import Path
from google.genai import types
from ..main import process_prompt
from ..session import load_session, save_session, create_working_directory_message
from ..available_functions import get_available_functions, call_function
from ..llm import get_client
# TerminalUI will be added in slice 5


def should_reinitialize_working_directory(messages, current_dir):
    """Check if we need to reinitialize working directory based on message history."""
    # For now, always reinitialize to ensure fresh context
    # TODO: Could add smarter detection based on last working directory call
    return True


def initialize_session_with_working_directory(messages):
    """Force AI to call get_working_directory to establish current location."""
    working_directory = Path(os.getcwd())
    available_functions = get_available_functions(str(working_directory))
    
    # Add explicit directive to get working directory
    init_prompt = "You MUST call get_working_directory() to confirm your current working directory before proceeding."
    current_message = types.Content(
        role="user",
        parts=[types.Part(text=init_prompt)]
    )
    
    conversation = messages + [current_message]
    
    # Enhanced system instruction to force function call
    system_prompt = """On every new interactive session initialization, your FIRST ACTION must be calling get_working_directory(). 
Do not proceed with any other requests until you've explicitly called and confirmed the working directory.

You MUST call get_working_directory() immediately when asked to confirm your working directory."""
    
    client = get_client()
    
    # Force the function call
    for i in range(3):  # Try up to 3 times
        res = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=conversation,
            config=types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt
            )
        )
        
        if res.candidates:
            for candidate in res.candidates:
                conversation.append(candidate.content)
                for part in candidate.content.parts:
                    if part.function_call and part.function_call.name == "get_working_directory":
                        # Function called! Execute it and add result
                        function_result = call_function(part.function_call, str(working_directory))
                        conversation.append(function_result)
                        
                        # Add confirmation message
                        confirmation = types.Content(
                            role="model",
                            parts=[types.Part(text=f"🛠️ **Confirmed working directory**: {working_directory}")]
                        )
                        conversation.append(confirmation)
                        
                        # Return only the original messages + new working directory context (skip init prompt)
                        return messages + conversation[len(messages) + 1:]
        
        # If no function call, break
        if not any(part.function_call for candidate in res.candidates for part in candidate.content.parts if part.function_call):
            break
    
    # If function wasn't called, return original messages
    return messages


def process_command(user_input, messages):
    """Process special commands. Returns (handled, updated_messages)."""
    if user_input.startswith('/'):
        return handle_slash_command(user_input, messages)
    return False, messages


def handle_slash_command(command, messages):
    """Handle slash commands. Returns (handled, updated_messages)."""
    if command == '/reset':
        print("Session cleared. Starting fresh in", os.getcwd())
        return True, []  # Clear all messages
    # Future commands like /session will be added here
    return False, messages


def main():
    """Main interactive mode entry point."""
    print("Interactive Mode - Staffer AI Assistant")
    print("Type 'exit' or 'quit' to end the session")
    
    # Load previous session if it exists
    messages = load_session()
    if messages:
        print(f"Restored conversation with {len(messages)} previous messages")
    
    # Force working directory initialization
    current_dir = Path(os.getcwd())
    if should_reinitialize_working_directory(messages, current_dir):
        print("Initializing working directory context...")
        messages = initialize_session_with_working_directory(messages)
        save_session(messages)
    
    while True:
        try:
            print("staffer> ", end="", flush=True)
            user_input = input().strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                # Save session before exiting
                save_session(messages)
                print("Goodbye!")
                break
            
            # Check for special commands first
            handled, messages = process_command(user_input, messages)
            if handled:
                # Save session after command
                save_session(messages)
                print()  # Add spacing
                continue
                
            # Process the command (working directory info now in system prompt)
            messages = process_prompt(user_input, messages=messages)
            print()  # Add spacing between responses
            
        except (EOFError, KeyboardInterrupt):
            # Save session before exiting on Ctrl+C
            save_session(messages)
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue