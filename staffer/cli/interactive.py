"""Interactive mode for Staffer - continuous prompt loop."""

from ..main import process_prompt
from ..session import load_session, save_session, create_working_directory_message


def main():
    """Main interactive mode entry point."""
    print("Interactive Mode - Staffer AI Assistant")
    print("Type 'exit' or 'quit' to end the session")
    
    # Load previous session if it exists
    messages = load_session()
    if messages:
        print(f"Restored conversation with {len(messages)} previous messages")
    print()
    
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
                
            # Add working directory context and process the command
            messages_with_context = [create_working_directory_message()] + messages
            messages = process_prompt(user_input, messages=messages_with_context)
            print()  # Add spacing between responses
            
        except (EOFError, KeyboardInterrupt):
            # Save session before exiting on Ctrl+C
            save_session(messages)
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue