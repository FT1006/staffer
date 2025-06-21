"""Tests for directory change detection feature."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from staffer.session import save_session_with_metadata, load_session_with_metadata


class TestSessionMetadata:
    """Test session metadata support for directory tracking."""
    
    def test_session_stores_working_directory_metadata(self):
        """Test that save_session_with_metadata stores cwd in metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "test_session.json"
            
            messages = [
                {"role": "user", "text": "hello"},
                {"role": "model", "text": "hi"}
            ]
            
            # Mock os.getcwd to return a predictable path
            with patch('os.getcwd', return_value='/home/user/project'):
                save_session_with_metadata(messages, session_path=session_file)
            
            # Read the file and verify structure
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            assert "messages" in data
            assert data["messages"] == messages
            assert "metadata" in data
            assert data["metadata"]["cwd"] == "/home/user/project"
            assert "created" in data["metadata"]
    
    def test_load_session_returns_messages_and_metadata(self):
        """Test that load_session_with_metadata returns both messages and metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "test_session.json"
            
            # Create a session file with metadata
            session_data = {
                "messages": [
                    {"role": "user", "text": "hello"},
                    {"role": "model", "text": "hi"}
                ],
                "metadata": {
                    "cwd": "/home/user/project",
                    "created": "2024-01-01T00:00:00"
                }
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
            
            # Load and verify
            messages, metadata = load_session_with_metadata(session_path=session_file)
            
            # Verify we got Content objects back with correct data
            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[0].parts[0].text == "hello"
            assert messages[1].role == "model"
            assert messages[1].parts[0].text == "hi"
            assert metadata == session_data["metadata"]
    
    def test_backward_compatibility_with_old_sessions(self):
        """Test that load_session_with_metadata handles old format gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "old_session.json"
            
            # Create an old-style session file (just array of messages)
            old_messages = [
                {"role": "user", "text": "hello"},
                {"role": "model", "text": "hi"}
            ]
            
            with open(session_file, 'w') as f:
                json.dump(old_messages, f)
            
            # Load and verify it returns empty metadata
            messages, metadata = load_session_with_metadata(session_path=session_file)
            
            # Verify we got Content objects back with correct data
            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[0].parts[0].text == "hello"
            assert messages[1].role == "model"
            assert messages[1].parts[0].text == "hi"
            assert metadata == {}
    
    def test_save_without_metadata_uses_current_directory(self):
        """Test that save_session_with_metadata adds cwd automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "test_session.json"
            
            messages = [{"role": "user", "text": "test"}]
            
            with patch('os.getcwd', return_value='/test/dir'):
                save_session_with_metadata(messages, session_path=session_file)
            
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            assert data["metadata"]["cwd"] == "/test/dir"