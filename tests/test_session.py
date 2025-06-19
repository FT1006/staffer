"""Tests for session persistence functionality."""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from staffer.session import save_session, load_session
from google.genai import types


def test_session_persistence():
    """Session should persist basic message history across restarts."""
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        # Mock the session file path
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Create some test messages using Google AI types
            test_messages = [
                types.Content(role="user", parts=[types.Part(text="hello")]),
                types.Content(role="assistant", parts=[types.Part(text="Hi there!")])
            ]
            
            # Save messages
            save_session(test_messages)
            
            # Load messages back
            loaded_messages = load_session()
            
            # Verify messages were persisted correctly
            assert len(loaded_messages) == 2
            assert loaded_messages[0].role == "user"
            assert loaded_messages[0].parts[0].text == "hello"
            assert loaded_messages[1].role == "assistant"
            assert loaded_messages[1].parts[0].text == "Hi there!"


def test_load_session_no_file():
    """Loading session with no existing file should return empty list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nonexistent_file = os.path.join(temp_dir, "nonexistent.json")
        
        with patch('staffer.session.get_session_file_path', return_value=nonexistent_file):
            loaded_messages = load_session()
            assert loaded_messages == []


def test_save_session_creates_directory():
    """Save session should create directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "new_dir", "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            test_messages = [types.Content(role="user", parts=[types.Part(text="test")])]
            
            # This should create the directory
            save_session(test_messages)
            
            # Verify file was created
            assert os.path.exists(session_file)
            
            # Verify content is correct
            loaded_messages = load_session()
            assert len(loaded_messages) == 1
            assert loaded_messages[0].role == "user"
            assert loaded_messages[0].parts[0].text == "test"