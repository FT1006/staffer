"""Session persistence for Staffer - save and load conversation history."""

import json
import os
from pathlib import Path
from google.genai import types


def get_session_file_path():
    """Get the path to the session file."""
    staffer_dir = Path.home() / ".staffer"
    return staffer_dir / "current_session.json"


def serialize_message(message):
    """Convert a Google AI types.Content object to a JSON-serializable dict."""
    if hasattr(message, 'role') and hasattr(message, 'parts'):
        # Extract text from parts (simplified for now)
        text_parts = []
        for part in message.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        return {
            "role": message.role,
            "text": " ".join(text_parts) if text_parts else ""
        }
    else:
        # If it's already a dict, return as-is
        return message


def deserialize_message(data):
    """Convert a dict back to a Google AI types.Content object."""
    if isinstance(data, dict) and "role" in data and "text" in data:
        return types.Content(
            role=data["role"],
            parts=[types.Part(text=data["text"])]
        )
    else:
        # If it's already a Content object, return as-is
        return data


def save_session(messages):
    """Save messages to the session file."""
    session_file = get_session_file_path()
    session_path = Path(session_file)
    
    # Create directory if it doesn't exist
    session_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Serialize messages before saving
    serialized_messages = [serialize_message(msg) for msg in messages]
    
    # Save messages as JSON
    with open(session_path, 'w') as f:
        json.dump(serialized_messages, f, indent=2)


def load_session():
    """Load messages from the session file."""
    session_file = get_session_file_path()
    session_path = Path(session_file)
    
    # Return empty list if file doesn't exist
    if not session_path.exists():
        return []
    
    try:
        with open(session_path, 'r') as f:
            serialized_messages = json.load(f)
            # Deserialize messages after loading
            return [deserialize_message(msg) for msg in serialized_messages]
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, return empty list
        return []