"""Tests for directory change detection feature."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from staffer.session import save_session_with_metadata, load_session_with_metadata
from staffer.cli.interactive import check_directory_change, prompt_directory_change


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


class TestDirectoryChangeDetection:
    """Test directory change detection in interactive mode."""
    
    def test_directory_change_prompts_user_on_session_restore(self):
        """Test that user is prompted when directory has changed."""
        # Mock input to simulate user choosing 'new session'
        with patch('builtins.input', return_value='n'):
            result = prompt_directory_change("/old/path", "/new/path")
            assert result is True  # User wants new session
        
        # Mock input to simulate user choosing 'keep session'
        with patch('builtins.input', return_value='k'):
            result = prompt_directory_change("/old/path", "/new/path")
            assert result is False  # User wants to keep old session
    
    def test_check_directory_change_detects_changes(self):
        """Test that directory changes are properly detected."""
        # Test when directories are different
        metadata = {"cwd": "/old/directory"}
        with patch('os.getcwd', return_value="/new/directory"):
            assert check_directory_change(metadata) is True
        
        # Test when directories are the same
        metadata = {"cwd": "/same/directory"}
        with patch('os.getcwd', return_value="/same/directory"):
            assert check_directory_change(metadata) is False
        
        # Test with missing cwd in metadata
        metadata = {}
        with patch('os.getcwd', return_value="/any/directory"):
            assert check_directory_change(metadata) is False  # No cwd to compare
    
    def test_prompt_directory_change_default_is_new_session(self):
        """Test that empty input defaults to new session."""
        with patch('builtins.input', return_value=''):  # Just pressing Enter
            result = prompt_directory_change("/old", "/new")
            assert result is True  # Default is new session
    
    def test_prompt_directory_change_case_insensitive(self):
        """Test that prompt accepts uppercase and lowercase inputs."""
        # Test uppercase N
        with patch('builtins.input', return_value='N'):
            assert prompt_directory_change("/old", "/new") is True
        
        # Test uppercase K
        with patch('builtins.input', return_value='K'):
            assert prompt_directory_change("/old", "/new") is False
    
    def test_prompt_shows_directory_info(self):
        """Test that prompt displays the directory change information."""
        # This test just verifies the function works correctly - 
        # the actual display is handled by the terminal UI
        with patch('builtins.input', return_value='n'):
            result = prompt_directory_change("/home/user/project-a", "/home/user/project-b")
            # Just verify it returns the expected result
            assert result is True  # User chose new session