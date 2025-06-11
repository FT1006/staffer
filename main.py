import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

if len(sys.argv) == 1:
    print("Error: No prompt provided")
    exit(1)

prompt = sys.argv[1]

messages = [
    types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )
]

res = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents=messages
)    

promptTokens = res.usage_metadata.prompt_token_count
responseTokens = res.usage_metadata.candidates_token_count

if len(sys.argv) > 2 and "--verbose" in sys.argv:
    print(f"User prompt: {prompt}")
    print(res.text)
    print(f"Prompt tokens: {promptTokens}")
    print(f"Response tokens: {responseTokens}")
else:
    print(res.text)