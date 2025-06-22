"""Tests for directory context pruning functionality.

NOTE: Tests updated for 1M token context - expect NO pruning by default.
Original pruning tests preserved with _DEACTIVATED suffix.
"""

import pytest
from pathlib import Path
from google.genai import types
from staffer.main import prune_stale_dir_msgs


def test_no_pruning_with_1m_context():
    """With 1M context window, all messages should be preserved (no pruning)."""
    
    # Test scenario: User was in /Users/spaceship/project, now in /Users/spaceship/project/staffer
    old_cwd = Path("/Users/spaceship/project")
    new_cwd = Path("/Users/spaceship/project/staffer")
    
    # Simulate session with "stale" directory context (should be preserved now)
    all_messages = [
        types.Content(role="user", parts=[types.Part(text="where are you at?")]),
        types.Content(role="model", parts=[types.Part(text="I don't have access to the full path or any information beyond these items")]),
        types.Content(role="user", parts=[types.Part(text="explore Logic")]),
        types.Content(role="model", parts=[types.Part(text="I am unable to explore the Logic directory because I lack the functionality")]),
        types.Content(role="model", parts=[types.Part(text=f"[Working directory: {old_cwd}] (captured 2025-06-20T10:00:00)")]),
        types.Content(role="user", parts=[types.Part(text="list files")]),
        types.Content(role="model", parts=[types.Part(text="I apologize. It seems I am having trouble displaying the list of files correctly.")]),
        # Tool response from old directory should also be preserved
        types.Content(
            role="tool",
            parts=[types.Part(function_response=types.FunctionResponse(
                name="get_files_info",
                response={"result": f"{old_cwd}/Logic\n{old_cwd}/README.md\n{old_cwd}/staffer"}
            ))]
        ),
    ]
    
    # Apply pruning logic (should now preserve all messages)
    result_messages = prune_stale_dir_msgs(all_messages, new_cwd)
    
    # NEW EXPECTATION: All messages should be preserved with 1M context
    assert len(result_messages) == len(all_messages), \
        f"Expected all {len(all_messages)} messages preserved, got {len(result_messages)}"
    
    # OLD directory references should now be PRESERVED (not removed)
    remaining_text = " ".join(
        msg.parts[0].text for msg in result_messages 
        if msg.parts and msg.parts[0].text
    )
    
    # Verify old working directory references are PRESERVED
    assert str(old_cwd) in remaining_text, \
        f"Old working directory {old_cwd} should be PRESERVED with 1M context"
    
    # Verify tool responses from previous directories are PRESERVED
    tool_responses = [msg for msg in result_messages if msg.role == "tool"]
    found_old_tool_response = False
    for msg in tool_responses:
        if msg.parts and hasattr(msg.parts[0], 'function_response'):
            fc = msg.parts[0].function_response
            if fc and fc.name == "get_files_info":
                result = str(fc.response.get("result", ""))
                if str(old_cwd) in result:
                    found_old_tool_response = True
    
    assert found_old_tool_response, \
        f"Tool response with old directory {old_cwd} should be PRESERVED"


# def test_directory_change_prunes_stale_directory_context_DEACTIVATED():
#     """When working directory changes, stale directory context should be pruned."""
#     
#     # Test scenario: User was in /Users/spaceship/project, now in /Users/spaceship/project/staffer
#     old_cwd = Path("/Users/spaceship/project")
#     new_cwd = Path("/Users/spaceship/project/staffer")
#     
#     # Simulate session with stale directory context
#     stale_messages = [
#         types.Content(role="user", parts=[types.Part(text="where are you at?")]),
#         types.Content(role="model", parts=[types.Part(text="I don't have access to the full path or any information beyond these items")]),
#         types.Content(role="user", parts=[types.Part(text="explore Logic")]),
#         types.Content(role="model", parts=[types.Part(text="I am unable to explore the Logic directory because I lack the functionality")]),
#         types.Content(role="model", parts=[types.Part(text=f"[Working directory: {old_cwd}] (captured 2025-06-20T10:00:00)")]),
#         types.Content(role="user", parts=[types.Part(text="list files")]),
#         types.Content(role="model", parts=[types.Part(text="I apologize. It seems I am having trouble displaying the list of files correctly.")]),
#         # Add tool response from old directory to test path-based filtering
#         types.Content(
#             role="tool",
#             parts=[types.Part(function_response=types.FunctionResponse(
#                 name="get_files_info",
#                 response={"result": f"{old_cwd}/Logic\n{old_cwd}/README.md\n{old_cwd}/staffer"}
#             ))]
#         ),
#     ]
#     
#     # Apply our pruning logic
#     pruned_messages = prune_stale_dir_msgs(stale_messages, new_cwd)
#     
#     # Extract all text that AI can see
#     remaining_text = " ".join(
#         msg.parts[0].text for msg in pruned_messages 
#         if msg.parts and msg.parts[0].text
#     )
#     
#     # Verify old working directory references are removed
#     assert str(old_cwd) not in remaining_text, \
#         f"Old working directory {old_cwd} should be removed, found: {remaining_text}"
#     
#     # Verify tool responses from ancestor directories are removed
#     tool_responses = [msg for msg in pruned_messages if msg.role == "tool"]
#     for msg in tool_responses:
#         if msg.parts and hasattr(msg.parts[0], 'function_response'):
#             fc = msg.parts[0].function_response
#             if fc and fc.name == "get_files_info":
#                 result = str(fc.response.get("result", ""))
#                 # Should not contain paths from ancestor directory
#                 assert str(old_cwd) not in result, \
#                     f"Tool response should not contain ancestor path {old_cwd}: {result}"
#     
#     # User questions should be preserved (they're not contradictory)
#     user_messages = [msg for msg in pruned_messages if msg.role == "user"]
#     user_text = " ".join(
#         msg.parts[0].text for msg in user_messages 
#         if msg.parts and msg.parts[0].text
#     )
#     assert "where are you at" in user_text, "User questions should be preserved"
#     assert "explore Logic" in user_text, "User questions should be preserved"


# def test_ancestor_path_detection_DEACTIVATED():
#     """Test that ancestor paths are properly detected and filtered."""
#     
#     # Test various directory relationships
#     grandparent = Path("/home/user")
#     parent = Path("/home/user/project") 
#     current = Path("/home/user/project/staffer")
#     sibling = Path("/home/user/other-project")
#     
#     messages_with_paths = [
#         # Should be removed (ancestor paths)
#         types.Content(role="model", parts=[types.Part(text=f"Working in {grandparent}")]),
#         types.Content(role="model", parts=[types.Part(text=f"Files in {parent}")]),
#         # Should be kept (current path)
#         types.Content(role="model", parts=[types.Part(text=f"Currently in {current}")]),
#         # Should be kept (sibling path - not ancestor)
#         types.Content(role="model", parts=[types.Part(text=f"Also found {sibling}")]),
#         # Should be kept (no path reference)
#         types.Content(role="user", parts=[types.Part(text="What files are here?")]),
#     ]
#     
#     pruned = prune_stale_dir_msgs(messages_with_paths, current)
#     
#     remaining_text = " ".join(
#         msg.parts[0].text for msg in pruned 
#         if msg.parts and msg.parts[0].text
#     )
#     
#     # Messages that ONLY reference ancestor paths should be removed
#     assert "Working in /home/user" not in remaining_text  # Only grandparent
#     assert "Files in /home/user/project" not in remaining_text  # Only parent
#     
#     # Current and sibling paths should be preserved  
#     assert str(current) in remaining_text
#     assert str(sibling) in remaining_text
#     assert "What files are here?" in remaining_text


# def test_message_count_limit_DEACTIVATED():
#     """Test that message count is limited to prevent token overflow."""
#     
#     current_dir = Path("/test/dir")
#     
#     # Create many messages
#     many_messages = []
#     for i in range(150):  # More than default limit of 120
#         many_messages.append(
#             types.Content(role="user", parts=[types.Part(text=f"Message {i}")])
#         )
#     
#     pruned = prune_stale_dir_msgs(many_messages, current_dir, max_messages=120)
#     
#     # Should be limited to max_messages
#     assert len(pruned) <= 120
#     
#     # Should keep most recent messages
#     last_message_text = pruned[-1].parts[0].text
#     assert "Message 149" in last_message_text  # Last message should be preserved


# def test_preserves_valid_tool_responses_DEACTIVATED():
#     """Test that tool responses from current directory are preserved."""
#     
#     current_dir = Path("/current/dir")
#     
#     messages_with_tools = [
#         types.Content(role="user", parts=[types.Part(text="list files")]),
#         # Tool response from current directory - should be kept
#         types.Content(
#             role="tool",
#             parts=[types.Part(function_response=types.FunctionResponse(
#                 name="get_files_info", 
#                 response={"result": f"{current_dir}/file1.py\n{current_dir}/file2.txt"}
#             ))]
#         ),
#         # Tool response from parent directory - should be removed
#         types.Content(
#             role="tool",
#             parts=[types.Part(function_response=types.FunctionResponse(
#                 name="get_files_info",
#                 response={"result": f"{current_dir.parent}/other.py"}
#             ))]
#         ),
#     ]
#     
#     pruned = prune_stale_dir_msgs(messages_with_tools, current_dir)
#     
#     # Should have user message + valid tool response
#     assert len(pruned) >= 2
#     
#     # Check that current directory tool response is preserved
#     tool_responses = [msg for msg in pruned if msg.role == "tool"]
#     assert len(tool_responses) == 1  # Only current dir tool response
#     
#     preserved_tool = tool_responses[0]
#     result = str(preserved_tool.parts[0].function_response.response.get("result", ""))
#     assert str(current_dir) in result
#     assert str(current_dir.parent) not in result or str(current_dir) in result