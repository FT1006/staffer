"""Interactive mode for Staffer - continuous prompt loop."""

from ..main import process_prompt


def main():
    """Main interactive mode entry point."""
    print("Interactive Mode - Staffer AI Assistant")
    print("Type 'exit' or 'quit' to end the session")
    print()
    
    while True:
        try:
            print("staffer> ", end="", flush=True)
            user_input = input().strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            # Process the command using existing single-command logic
            process_prompt(user_input)
            print()  # Add spacing between responses
            
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue