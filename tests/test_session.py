"""Tests for session persistence functionality."""

import json
import os
import sys
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
                types.Content(role="model", parts=[types.Part(text="Hi there!")])
            ]
            
            # Save messages
            save_session(test_messages)
            
            # Load messages back
            loaded_messages = load_session()
            
            # Verify messages were persisted correctly
            assert len(loaded_messages) == 2
            assert loaded_messages[0].role == "user"
            assert loaded_messages[0].parts[0].text == "hello"
            assert loaded_messages[1].role == "model"
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


def test_session_with_function_calls():
    """Sessions should handle function call and response messages."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Create messages including a tool message with function response
            test_messages = [
                types.Content(role="user", parts=[types.Part(text="list files")]),
                types.Content(role="model", parts=[types.Part(text="I'll list the files for you.")]),
                types.Content(
                    role="tool",
                    parts=[types.Part(function_response=types.FunctionResponse(
                        name="get_files_info",
                        response={"result": "file1.txt, file2.py"}
                    ))]
                ),
                types.Content(role="model", parts=[types.Part(text="Here are the files: file1.txt, file2.py")])
            ]
            
            # Save and load the session
            save_session(test_messages)
            loaded_messages = load_session()
            
            # Should preserve the essential conversation flow
            assert len(loaded_messages) >= 3  # User request, model responses, function context
            assert loaded_messages[0].role == "user"
            assert loaded_messages[0].parts[0].text == "list files"
            
            # Function call context should be preserved somehow
            has_function_context = any("get_files_info" in msg.parts[0].text for msg in loaded_messages if msg.parts[0].text)
            assert has_function_context, "Function call context should be preserved"


def test_corrupted_session_recovery():
    """Should gracefully handle corrupted session files with mixed data types."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Create a corrupted session file with mixed data types (like from our bug)
            corrupted_data = [
                "msg1",  # Invalid string
                "msg2",  # Invalid string  
                {"role": "user", "text": "hello"},  # Valid message
                {"role": "invalid", "text": "bad role"},  # Invalid role
                {"invalid": "structure"},  # Invalid structure
                {"role": "model", "text": "response"}  # Valid message
            ]
            
            # Write corrupted data directly
            with open(session_file, 'w') as f:
                json.dump(corrupted_data, f)
            
            # Should load gracefully, filtering out invalid entries
            loaded_messages = load_session()
            
            # Should only contain valid messages
            assert len(loaded_messages) == 2
            assert loaded_messages[0].role == "user"
            assert loaded_messages[0].parts[0].text == "hello"
            assert loaded_messages[1].role == "model"
            assert loaded_messages[1].parts[0].text == "response"


def test_function_response_preservation():
    """Function call results should be preserved across sessions for context."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Session with function call that lists files
            test_messages = [
                types.Content(role="user", parts=[types.Part(text="what files are here?")]),
                types.Content(role="model", parts=[types.Part(text="I'll check the files for you.")]),
                types.Content(
                    role="tool", 
                    parts=[types.Part(function_response=types.FunctionResponse(
                        name="get_files_info",
                        response={"result": "important.txt, config.json"}
                    ))]
                ),
                types.Content(role="model", parts=[types.Part(text="I found: important.txt, config.json")])
            ]
            
            save_session(test_messages)
            loaded_messages = load_session()
            
            # After loading, the AI should have context about what files exist
            # This should be preserved in some form for follow-up questions
            all_text = " ".join(msg.parts[0].text for msg in loaded_messages if msg.parts[0].text)
            
            # Should contain reference to the files that were found
            assert "important.txt" in all_text or "config.json" in all_text, \
                "Function call results should be preserved for context"


def test_invalid_role_filtering():
    """Invalid roles should be filtered out during deserialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Manually create session with invalid role
            invalid_data = [
                {"role": "user", "text": "hello"},
                {"role": "assistant", "text": "should become model"},  # Invalid role for Google AI
                {"role": "system", "text": "invalid role"},  # Invalid role
                {"role": "model", "text": "valid response"}
            ]
            
            with open(session_file, 'w') as f:
                json.dump(invalid_data, f)
            
            loaded_messages = load_session()
            
            # Should only load messages with valid roles (user, model, tool)
            valid_roles = {msg.role for msg in loaded_messages}
            assert valid_roles.issubset({"user", "model", "tool"}), \
                f"Found invalid roles: {valid_roles - {'user', 'model', 'tool'}}"


def test_ai_remembers_file_listing_across_sessions():
    """AI should remember file listings from tool calls across session restarts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Simulate a session where user asks for file listing
            test_messages = [
                types.Content(role="user", parts=[types.Part(text="what files are here?")]),
                types.Content(role="model", parts=[types.Part(text="I'll check the files for you.")]),
                types.Content(
                    role="tool",
                    parts=[types.Part(function_response=types.FunctionResponse(
                        name="get_files_info",
                        response={"result": "data.csv\nreport.py\nanalysis.ipynb"}
                    ))]
                ),
                types.Content(role="model", parts=[types.Part(text="I found: data.csv, report.py, analysis.ipynb")])
            ]
            
            # Save session
            save_session(test_messages)
            
            # Simulate session restart - load previous session
            loaded_messages = load_session()
            
            # Convert back to text to check if file listing is preserved
            all_text = " ".join(
                msg.parts[0].text for msg in loaded_messages 
                if msg.parts and msg.parts[0].text
            )
            
            # AI should have access to the file listing information
            assert "data.csv" in all_text, "File listing should be preserved across sessions"
            assert "report.py" in all_text, "File listing should be preserved across sessions" 
            assert "analysis.ipynb" in all_text, "File listing should be preserved across sessions"
            
            # Verify the tool context is meaningful for follow-up questions
            # The AI should be able to answer "what files did I have?" from this context
            has_file_context = any(
                "data.csv" in (msg.parts[0].text or "") for msg in loaded_messages
                if msg.parts and msg.parts[0].text
            )
            assert has_file_context, "Tool results should provide meaningful context for AI"


def test_ai_can_answer_about_previous_file_listing():
    """AI should be able to answer questions about previously seen file listings."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Create session with tool response containing detailed file info
            initial_session = [
                types.Content(role="user", parts=[types.Part(text="list the files here")]),
                types.Content(role="model", parts=[types.Part(text="I'll list the files for you.")]),
                types.Content(
                    role="tool",
                    parts=[types.Part(function_response=types.FunctionResponse(
                        name="get_files_info", 
                        response={"result": [
                            {"name": "important_data.csv", "size": 1024},
                            {"name": "analysis_script.py", "size": 2048}, 
                            {"name": "results.txt", "size": 512}
                        ]}
                    ))]
                ),
                types.Content(role="model", parts=[types.Part(text="I found 3 files: important_data.csv (1024 bytes), analysis_script.py (2048 bytes), and results.txt (512 bytes).")])
            ]
            
            save_session(initial_session)
            
            # Simulate restart - load session
            loaded_messages = load_session()
            
            # Check that tool results are preserved in a meaningful way
            # Current implementation converts tool responses to generic text
            tool_messages = [msg for msg in loaded_messages if msg.role == "model"]
            
            # The AI should have specific file information available
            found_specific_files = False
            for msg in tool_messages:
                if msg.parts and msg.parts[0].text:
                    text = msg.parts[0].text
                    if "important_data.csv" in text and "1024" in text:
                        found_specific_files = True
                        break
            
            assert found_specific_files, "Specific file details should be preserved for AI context"
            
            # Verify that function call context is preserved somehow
            # Even if simplified, the AI should have access to the fact that get_files_info was called
            has_function_context = any(
                "get_files_info" in (msg.parts[0].text or "") for msg in loaded_messages
                if msg.parts and msg.parts[0].text
            )
            assert has_function_context, "Function call context should be preserved"


def test_function_response_becomes_visible_text_after_restore():
    """Function responses should be converted to text the AI can actually see."""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_file = os.path.join(temp_dir, "current_session.json")
        
        with patch('staffer.session.get_session_file_path', return_value=session_file):
            # Save ONLY a tool response with NO model summary  
            # This simulates the real scenario where we have raw function data
            raw_tool_session = [
                types.Content(role="user", parts=[types.Part(text="what files are here?")]),
                types.Content(
                    role="tool",
                    parts=[types.Part(function_response=types.FunctionResponse(
                        name="get_files_info",
                        response={"result": ["project.py", "data.csv", "README.md", "config.json"]}
                    ))]
                )
                # NOTE: No model message with file listing text - this is the key difference
            ]
            
            save_session(raw_tool_session)
            loaded_messages = load_session()
            
            # Test what the serialization/deserialization actually produces
            # This tests the current transformation layer
            ai_visible_text = []
            for msg in loaded_messages:
                if hasattr(msg, 'parts') and msg.parts:
                    for part in msg.parts:
                        if hasattr(part, 'text') and part.text:
                            ai_visible_text.append(part.text)
            
            full_context = " ".join(ai_visible_text)
            
            # The AI should be able to see the actual file names, not just 
            # "[Function get_files_info executed successfully]"
            assert "project.py" in full_context, \
                f"AI should see actual file names in context, got: '{full_context}'"
            assert "data.csv" in full_context, \
                f"AI should see actual file names in context, got: '{full_context}'"
            assert "README.md" in full_context, \
                f"AI should see actual file names in context, got: '{full_context}'"
            assert "config.json" in full_context, \
                f"AI should see actual file names in context, got: '{full_context}'"
            
            # Should not contain the old generic placeholder
            assert "[Function get_files_info executed successfully]" not in full_context, \
                "Should contain actual results, not generic placeholder"


def test_working_directory_is_visible_after_restore():
    """AI should know the working directory without having to ask or infer."""
    # Mock Google AI modules to avoid dependency issues
    with patch.dict(sys.modules, {
        'google': MagicMock(),
        'google.genai': MagicMock(),
    }):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = os.path.join(temp_dir, "current_session.json")
            
            with patch('staffer.session.get_session_file_path', return_value=session_file):
                # Create a previous session (simulate user has been working)
                previous_session = [
                    types.Content(role="user", parts=[types.Part(text="hello")])
                ]
                save_session(previous_session)
                
                # Test: what happens when interactive mode loads this session 
                # and processes a new prompt asking about working directory?
                with patch('staffer.main.process_prompt') as mock_process:
                    # Mock process_prompt to capture what messages it receives
                    mock_process.return_value = []  # Return empty for simplicity
                    
                    from staffer.cli.interactive import main as interactive_main
                    
                    # Simulate user asking about working directory after session restore
                    with patch('builtins.input', side_effect=['what directory am I in?', 'exit']):
                        interactive_main()
                    
                    # Check what messages were passed to process_prompt
                    assert mock_process.call_count == 1, "process_prompt should be called once"
                    
                    call_args = mock_process.call_args
                    messages_sent_to_ai = call_args.kwargs.get('messages', [])
                    
                    # Extract text that AI can see
                    ai_visible_text = []
                    for msg in messages_sent_to_ai:
                        if hasattr(msg, 'parts') and msg.parts:
                            for part in msg.parts:
                                if hasattr(part, 'text') and part.text:
                                    ai_visible_text.append(part.text)
                    
                    full_context = " ".join(ai_visible_text)
                    current_dir = os.getcwd()
                    
                    # The AI should see the working directory in the context
                    assert current_dir in full_context, \
                        f"AI should see working directory '{current_dir}' in context, got: '{full_context}'"


def test_directory_change_removes_stale_context():
    """When working directory changes, stale directory context should be pruned."""
    from pathlib import Path
    from staffer.main import prune_stale_dir_msgs
    
    # Simulate session from /Users/spaceship/project with AI claiming ignorance
    old_cwd = Path("/Users/spaceship/project")
    new_cwd = Path("/Users/spaceship/project/staffer")
    
    stale_messages = [
        types.Content(role="user", parts=[types.Part(text="where are you at?")]),
        types.Content(role="model", parts=[types.Part(text="I don't have access to the full path or any information beyond these items")]),
        types.Content(role="user", parts=[types.Part(text="explore Logic")]),
        types.Content(role="model", parts=[types.Part(text="I am unable to explore the Logic directory because I lack the functionality")]),
        types.Content(role="model", parts=[types.Part(text=f"[Working directory: {old_cwd}] (captured 2025-06-20T10:00:00)")]),
        types.Content(
            role="tool",
            parts=[types.Part(function_response=types.FunctionResponse(
                name="get_files_info",
                response={"result": f"{old_cwd}/Logic\n{old_cwd}/README.md"}
            ))]
        ),
    ]
    
    # Test pruning when CWD changes to subdirectory
    pruned = prune_stale_dir_msgs(stale_messages, new_cwd)
    
    # Verify stale directory context is removed
    remaining_text = " ".join(
        msg.parts[0].text for msg in pruned 
        if msg.parts and msg.parts[0].text
    )
    
    # Should NOT contain old directory path
    assert str(old_cwd) not in remaining_text, \
        f"Stale directory context should be removed, but found: {remaining_text}"
    
    # Tool responses from ancestor directories should be removed
    tool_responses = [msg for msg in pruned if msg.role == "tool"]
    for msg in tool_responses:
        if msg.parts and hasattr(msg.parts[0], 'function_response'):
            fc = msg.parts[0].function_response
            if fc and fc.name == "get_files_info":
                result = str(fc.response.get("result", ""))
                # Should not start with ancestor path
                assert not result.startswith(str(old_cwd)), \
                    f"Tool response from ancestor directory should be removed: {result}"