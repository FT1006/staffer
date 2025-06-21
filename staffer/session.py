"""Session persistence for Staffer - save and load conversation history."""

import json
import os
from datetime import datetime
from pathlib import Path
from google.genai import types


def get_session_file_path():
    """Get the path to the session file."""
    staffer_dir = Path.home() / ".staffer"
    return staffer_dir / "current_session.json"


def create_working_directory_message():
    """Create a system message with current working directory information."""
    current_dir = os.getcwd()
    timestamp = datetime.now().isoformat()
    return types.Content(
        role="model",  # Use model role since Google AI doesn't support system role
        parts=[types.Part(text=f"[Working directory: {current_dir}] (captured {timestamp})")]
    )


def serialize_message(message):
    """Convert a Google AI types.Content object to a JSON-serializable dict.
    
    Handles different message types:
    - User/model messages: Extract text content
    - Tool messages: Convert to readable function execution summary
    - Already serialized dicts: Pass through unchanged
    """
    if hasattr(message, 'role') and hasattr(message, 'parts'):
        # Handle tool messages by converting function response to readable text
        if message.role == "tool":
            for part in message.parts:
                if hasattr(part, 'function_response') and part.function_response:
                    # Extract actual response data for AI visibility
                    response_data = part.function_response.response
                    function_name = part.function_response.name
                    
                    # Convert response to readable text based on structure
                    if isinstance(response_data, dict) and "result" in response_data:
                        result = response_data["result"]
                        if isinstance(result, list):
                            # List of items (like file names) - make comma-separated
                            result_text = ", ".join(str(item) for item in result)
                        else:
                            # String or other data
                            result_text = str(result)
                    else:
                        # Fallback for other response formats
                        result_text = str(response_data)
                    
                    return {
                        "role": "model",  # Convert tool response to model message
                        "text": f"Function {function_name} result: {result_text}"
                    }
            return None  # Skip tool messages without valid function responses
            
        # Extract text from parts for user/model messages
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
    """Convert a dict back to a Google AI types.Content object.
    
    Performs validation and filtering:
    - Validates roles against Google AI requirements (user, model, tool)
    - Converts common invalid roles (assistant -> model)
    - Filters out corrupted or invalid message data
    - Returns None for invalid messages (filtered out by load_session)
    """
    if isinstance(data, dict) and "role" in data and "text" in data:
        # Validate role - Google AI only accepts: user, model, tool
        valid_roles = {"user", "model", "tool"}
        role = data["role"]
        
        # Convert common invalid roles
        if role == "assistant":
            role = "model"
        elif role not in valid_roles:
            # Skip messages with invalid roles (system, etc.)
            return None
            
        return types.Content(
            role=role,
            parts=[types.Part(text=data["text"])]
        )
    elif hasattr(data, 'role') and hasattr(data, 'parts'):
        # If it's already a Content object, validate its role too
        valid_roles = {"user", "model", "tool"}
        if hasattr(data, 'role') and data.role in valid_roles:
            return data
        else:
            return None
    else:
        # Skip invalid data (leftover mock strings, malformed dicts, etc.)
        return None


def save_session(messages):
    """Save messages to the session file."""
    # Use the new metadata-aware function
    save_session_with_metadata(messages)


def save_session_with_metadata(messages, metadata=None, session_path=None):
    """Save messages and metadata to the session file.
    
    Args:
        messages: List of message objects to save
        metadata: Optional dict with additional metadata (e.g., {"cwd": "/path"})
        session_path: Optional path to save to (for testing)
    """
    if session_path is None:
        session_path = get_session_file_path()
    else:
        session_path = Path(session_path)
    
    # Create directory if it doesn't exist
    session_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare metadata with defaults
    if metadata is None:
        metadata = {}
    
    # Always add current working directory and timestamp
    metadata["cwd"] = os.getcwd()
    metadata["created"] = datetime.now().isoformat()
    
    # Serialize messages before saving, filter out None values
    serialized_messages = [serialize_message(msg) for msg in messages]
    filtered_messages = [msg for msg in serialized_messages if msg is not None]
    
    # Save as new format with metadata
    session_data = {
        "messages": filtered_messages,
        "metadata": metadata
    }
    
    with open(session_path, 'w') as f:
        json.dump(session_data, f, indent=2)


def load_session_with_metadata(session_path=None):
    """Load messages and metadata from the session file.
    
    Args:
        session_path: Optional path to load from (for testing)
        
    Returns:
        tuple: (messages, metadata) where metadata is a dict
    """
    if session_path is None:
        session_path = get_session_file_path()
    else:
        session_path = Path(session_path)
    
    # Return empty if file doesn't exist
    if not session_path.exists():
        return [], {}
    
    try:
        with open(session_path, 'r') as f:
            data = json.load(f)
            
        # Handle backward compatibility with old format
        if isinstance(data, list):
            # Old format: just array of messages
            messages = data
            metadata = {}
        else:
            # New format: dict with messages and metadata
            messages = data.get("messages", [])
            metadata = data.get("metadata", {})
        
        # Deserialize messages after loading, filter out None values
        deserialized = [deserialize_message(msg) for msg in messages]
        filtered_messages = [msg for msg in deserialized if msg is not None]
        
        return filtered_messages, metadata
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, return empty
        return [], {}


def load_session():
    """Load messages from the session file."""
    # Use the new metadata-aware function but only return messages
    messages, _ = load_session_with_metadata()
    return messages