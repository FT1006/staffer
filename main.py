import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.write_file import schema_write_file
from functions.run_python_file import schema_run_python_file

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
    ]
)

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

if len(sys.argv) > 2 and "--verbose" in sys.argv:
    print(f"User prompt: {prompt}")
    print(res.text)
    print(f"Prompt tokens: {promptTokens}")
    print(f"Response tokens: {responseTokens}")
elif res.function_calls:
    for function_call_part in res.function_calls:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
else:
    print(res.text)