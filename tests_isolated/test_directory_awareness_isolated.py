"""Isolated directory awareness tests - require aggressive mocking before CI."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.conftest import pushd
from tests.factories import user, model, tool_resp
from staffer.session import save_session


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