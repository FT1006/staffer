#!/usr/bin/env python3
"""Simple test for directory change detection without API calls."""

import os
import json
from pathlib import Path

# Create a test session with metadata in the new format
test_session = {
    "messages": [
        {"role": "user", "text": "hello"},
        {"role": "model", "text": "hi there"}
    ],
    "metadata": {
        "cwd": "/Users/spaceship/project/staffer-slice4",
        "created": "2025-06-21T18:00:00"
    }
}

# Save it to the session file
session_file = Path.home() / ".staffer" / "current_session.json"
session_file.parent.mkdir(exist_ok=True)

with open(session_file, 'w') as f:
    json.dump(test_session, f, indent=2)

print("Created test session in new format")
print(f"Session saved to: {session_file}")
print(f"Session working directory: {test_session['metadata']['cwd']}")
print(f"Current working directory: {os.getcwd()}")

# Now test the loading
from staffer.cli.interactive import load_session_with_metadata, check_directory_change

messages, metadata = load_session_with_metadata()
print(f"\nLoaded metadata: {metadata}")
print(f"Directory change detected: {check_directory_change(metadata)}")

# Change to calculator directory and test again
os.chdir("calculator")
print(f"\nChanged to: {os.getcwd()}")
print(f"Directory change detected: {check_directory_change(metadata)}")

if check_directory_change(metadata):
    print("✅ Directory change detection working!")
else:
    print("❌ Directory change detection not working")