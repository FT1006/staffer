import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from available_functions import get_available_functions, call_function

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

available_functions = get_available_functions()

if len(sys.argv) == 1:
    print("Error: No prompt provided")
    exit(1)

prompt = sys.argv[1]
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

verbose = len(sys.argv) > 2 and "--verbose" in sys.argv

if verbose:
    print(f"User prompt: {prompt}")

if res.function_calls:
    for function_call_part in res.function_calls:
        if verbose:
            function_call_result = call_function(function_call_part, verbose=True)
        else:
            function_call_result = call_function(function_call_part)
        if not function_call_result.parts[0].function_response.response:
            sys.exit(1)
        else:
            print(f"-> {function_call_result.parts[0].function_response.response}")
else:
    print(res.text)

if verbose:
    print(f"Prompt tokens: {promptTokens}")
    print(f"Response tokens: {responseTokens}")