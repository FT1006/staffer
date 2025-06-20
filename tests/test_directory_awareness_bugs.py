"""Component tests targeting the exact directory awareness bugs from HANDOVER_DIRECTORY_BUG.md"""

import pytest
from unittest.mock import patch
from tests.factories import user, model, tool_resp
from tests.conftest import pushd, assert_cwd_in_prompt
from staffer.session import save_session, load_session
from staffer.main import build_prompt


def test_cwd_header_updates_on_dir_change(tmp_path, fake_llm):
    """AI should know current directory even after changing directories between sessions."""
    session_file = tmp_path / "current_session.json"
    
    with patch('staffer.session.get_session_file_path', return_value=str(session_file)):
        # Step 1: Create session in directory A
        dir_a = tmp_path / "dir_a"
        dir_a.mkdir()
        (dir_a / "file_a.txt").write_text("content A")
        
        with pushd(dir_a):
            session_a = [
                user("what files are here?"),
                model("I'll check the files."),
                tool_resp("get_files_info", "file_a.txt"),
                model("I found: file_a.txt")
            ]
            save_session(session_a)
        
        # Step 2: Change to directory B (simulate: cd .. && cd project)
        dir_b = tmp_path / "dir_b"  
        dir_b.mkdir()
        (dir_b / "file_b.txt").write_text("content B")
        
        with pushd(dir_b):
            # Step 3: Load session and build prompt (what interactive.py does)
            loaded_messages = load_session()
            prompt = build_prompt(loaded_messages, working_directory=str(dir_b))
            
            # Step 4: Verify AI sees current directory, not stale directory
            assert_cwd_in_prompt(prompt, dir_b.name)
            
            # The AI should NOT be confused by stale file listings from dir_a
            # without current directory context
            if "file_a.txt" in prompt:
                assert dir_b.name in prompt, "If stale files present, current dir must be clear"


def test_get_files_info_called_after_session_restore(tmp_path, fake_llm):
    """AI should confidently use get_files_info function after session restore."""
    session_file = tmp_path / "current_session.json"
    
    with patch('staffer.session.get_session_file_path', return_value=str(session_file)):
        # Create a large session to simulate real usage
        large_session = []
        for i in range(20):  # 40 messages total
            large_session.extend([
                user(f"user message {i}"),
                model(f"model response {i}")
            ])
        
        # Add some tool usage history
        large_session.extend([
            user("list files please"),
            tool_resp("get_files_info", "some_file.py"),
            model("I found: some_file.py")
        ])
        
        save_session(large_session)
        
        # Test: simulate asking AI to explore directory after session restore
        with pushd(tmp_path):
            # Spy on actual function calls
            called = {}
            def spy_get_files_info(path="."):
                called["get_files_info"] = True
                return ["spied_file.py"]
            
            with patch("staffer.available_functions.get_files_info", spy_get_files_info):
                from staffer.cli.interactive import main as interactive_main
                
                # Simulate user asking to explore (reproduces the "Logic" directory bug)
                with patch("builtins.input", side_effect=["explore current directory", "exit"]):
                    interactive_main()
            
            # Verify the tool was actually called (not just refused)
            assert called.get("get_files_info"), \
                "AI should use get_files_info confidently, not claim it 'lacks functionality'"


def test_system_prompt_contains_functions_and_directory(tmp_path, fake_llm):
    """System prompt should contain both working directory and function descriptions."""
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    
    with pushd(test_dir):
        # Build prompt like process_prompt does
        messages = [user("hello")]
        prompt = build_prompt(messages, working_directory=str(test_dir))
        
        # Verify working directory is in system prompt
        assert_cwd_in_prompt(prompt, test_dir.name)
        
        # Verify function descriptions are in system prompt 
        assert "get_files_info()" in prompt, "System prompt should describe get_files_info function"
        assert "get_file_content(path)" in prompt, "System prompt should describe get_file_content function"
        assert "write_file(path, content)" in prompt, "System prompt should describe write_file function"
        
        # Verify encouraging language about function usage
        assert "use them confidently" in prompt, "Should encourage AI to use functions"


def test_session_file_not_polluted_with_working_directory_messages(tmp_path, fake_llm):
    """Session file should not contain multiple working directory messages."""
    session_file = tmp_path / "current_session.json"
    
    with patch('staffer.session.get_session_file_path', return_value=str(session_file)):
        # Simulate what happens in interactive.py - multiple interactions
        with pushd(tmp_path):
            from staffer.cli.interactive import main as interactive_main
            
            # Simulate multiple interactions that could pollute session
            inputs = ["hello", "what files are here?", "list directories", "exit"]
            with patch("builtins.input", side_effect=inputs):
                interactive_main()
        
        # Check raw session file content
        import json
        with open(session_file, 'r') as f:
            raw_data = json.load(f)
        
        # Count working directory pollution messages
        wd_messages = [
            msg for msg in raw_data 
            if isinstance(msg, dict) and "Working directory:" in msg.get("text", "")
        ]
        
        # Should be zero - working directory info should be in system prompt, not saved messages
        assert len(wd_messages) == 0, \
            f"Session file should not be polluted with {len(wd_messages)} working directory messages"


def test_tool_results_visible_to_ai_after_restore(tmp_path, fake_llm):
    """Function results should be preserved in a form the AI can actually see."""
    session_file = tmp_path / "current_session.json"
    
    with patch('staffer.session.get_session_file_path', return_value=str(session_file)):
        # Save session with tool responses
        session_with_tools = [
            user("what files are here?"),
            tool_resp("get_files_info", ["project.py", "data.csv", "README.md"])
        ]
        save_session(session_with_tools)
        
        # Load and check what AI can see
        loaded_messages = load_session()
        
        # Extract text that AI can actually see
        ai_visible_text = []
        for msg in loaded_messages:
            if hasattr(msg, 'parts') and msg.parts:
                for part in msg.parts:
                    if hasattr(part, 'text') and part.text:
                        ai_visible_text.append(part.text)
        
        full_context = " ".join(ai_visible_text)
        
        # AI should see actual file names, not generic "[Function executed successfully]"
        assert "project.py" in full_context, \
            f"AI should see actual results, got: '{full_context}'"
        assert "data.csv" in full_context, \
            f"AI should see actual results, got: '{full_context}'"
        assert "README.md" in full_context, \
            f"AI should see actual results, got: '{full_context}'"


def test_directory_change_detection_bug(tmp_path, fake_llm):
    """AI should update working directory when user changes directories between interactions."""
    session_file = tmp_path / "current_session.json"
    
    with patch('staffer.session.get_session_file_path', return_value=str(session_file)):
        # Step 1: Start session in directory A
        dir_a = tmp_path / "project"
        dir_a.mkdir()
        (dir_a / "project_file.py").write_text("# project file")
        
        with pushd(dir_a):
            # Simulate first interaction
            from staffer.main import process_prompt
            messages = process_prompt("where am I?")
            save_session(messages)
        
        # Step 2: User changes to subdirectory (simulate: cd learn-pub-sub-starter)
        dir_b = dir_a / "learn-pub-sub-starter"
        dir_b.mkdir()
        (dir_b / "starter_file.go").write_text("// starter file")
        
        with pushd(dir_b):
            # Step 3: Continue session in new directory
            loaded_messages = load_session()
            
            # This should build prompt with CURRENT directory (dir_b), not old directory (dir_a)
            from staffer.main import build_prompt
            prompt = build_prompt(loaded_messages, working_directory=str(dir_b))
            
            # The prompt should reflect the NEW working directory
            assert str(dir_b) in prompt, \
                f"System prompt should show current directory {dir_b}, got: {prompt}"
            assert "learn-pub-sub-starter" in prompt, \
                f"System prompt should show current directory name, got: {prompt}"
            
            # Simulate asking "where am I?" in new directory
            new_messages = process_prompt("where am I?", messages=loaded_messages)
            
            # Extract AI's response about location
            ai_responses = [
                msg.parts[0].text for msg in new_messages 
                if msg.role == "model" and msg.parts and msg.parts[0].text
            ]
            
            location_response = " ".join(ai_responses)
            
            # AI should state the NEW directory, not the old one
            assert str(dir_b) in location_response, \
                f"AI should state current directory {dir_b}, but said: '{location_response}'"
            assert str(dir_a) not in location_response or str(dir_b) in location_response, \
                f"AI should not have stale directory reference without current directory, got: '{location_response}'"