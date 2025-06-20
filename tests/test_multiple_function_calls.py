"""Tests for handling multiple function calls in a single AI response."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from google.genai import types
from staffer.main import process_prompt
from tests.factories import tool_resp


def test_multiple_function_calls_in_single_turn():
    """AI should be able to make multiple function calls in one response without errors."""
    
    with patch('staffer.main.get_client') as mock_get_client:
        with patch('staffer.main.call_function') as mock_call_function:
            # Setup working directory
            test_dir = Path("/test/directory")
            
            # Mock client
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # Create mock function calls using proper types
            from google.genai.types import FunctionCall
            
            mock_get_files_call = FunctionCall(name="get_files_info", args={})
            mock_get_content_call1 = FunctionCall(name="get_file_content", args={"file_path": "file1.py"})
            mock_get_content_call2 = FunctionCall(name="get_file_content", args={"file_path": "file2.py"})
            
            # Mock AI response with multiple function calls
            mock_candidate = MagicMock()
            mock_candidate.content = types.Content(
                role="model",
                parts=[
                    types.Part(function_call=mock_get_files_call),
                    types.Part(function_call=mock_get_content_call1), 
                    types.Part(function_call=mock_get_content_call2)
                ]
            )
            
            mock_response_with_functions = MagicMock()
            mock_response_with_functions.candidates = [mock_candidate]
            mock_response_with_functions.usage_metadata.prompt_token_count = 100
            mock_response_with_functions.usage_metadata.candidates_token_count = 50
            mock_response_with_functions.text = ""
            
            # Create final response (no function calls) to break the loop
            mock_final_candidate = MagicMock()
            mock_final_candidate.content = types.Content(
                role="model",
                parts=[types.Part(text="Here are the files and their contents.")]
            )
            
            mock_response_final = MagicMock()
            mock_response_final.candidates = [mock_final_candidate]
            mock_response_final.usage_metadata.prompt_token_count = 50
            mock_response_final.usage_metadata.candidates_token_count = 25
            mock_response_final.text = "Here are the files and their contents."
            
            # Use side_effect to simulate proper response sequence
            mock_client.models.generate_content.side_effect = [
                mock_response_with_functions,  # First call has function calls
                mock_response_final           # Second call breaks loop
            ]
            
            # Mock function call results using factories
            mock_results = [
                tool_resp("get_files_info", "file1.py\nfile2.py"),
                tool_resp("get_file_content", "# File 1 content"),
                tool_resp("get_file_content", "# File 2 content")
            ]
            
            mock_call_function.side_effect = mock_results
            
            # Test: This should NOT raise an error about function response parts mismatch
            with patch('os.getcwd', return_value=str(test_dir)):
                result_messages = process_prompt("list and read files", messages=[])
                
                # Verify that function was called multiple times
                assert mock_call_function.call_count == 3, \
                    f"Expected 3 function calls, got {mock_call_function.call_count}"
                
                # Verify that the conversation includes all responses
                # Should have: user message + model response + tool message
                assert len(result_messages) >= 3, \
                    f"Expected at least 3 messages, got {len(result_messages)}"
                
                # Find the tool message
                tool_messages = [msg for msg in result_messages if msg.role == "tool"]
                assert len(tool_messages) == 1, \
                    f"Expected exactly 1 tool message, got {len(tool_messages)}"
                
                # Verify the tool message has correct number of parts
                tool_message = tool_messages[0]
                assert len(tool_message.parts) == 3, \
                    f"Expected 3 function response parts, got {len(tool_message.parts)}"


def test_single_function_call_still_works():
    """Single function calls should continue to work as before."""
    
    with patch('staffer.main.get_client') as mock_get_client:
        with patch('staffer.main.call_function') as mock_call_function:
            test_dir = Path("/test/directory")
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # Single function call
            from google.genai.types import FunctionCall
            mock_function_call = FunctionCall(name="get_files_info", args={})
            
            mock_candidate = MagicMock()
            mock_candidate.content = types.Content(
                role="model",
                parts=[types.Part(function_call=mock_function_call)]
            )
            
            mock_response_with_functions = MagicMock()
            mock_response_with_functions.candidates = [mock_candidate]
            mock_response_with_functions.usage_metadata.prompt_token_count = 100
            mock_response_with_functions.usage_metadata.candidates_token_count = 50
            mock_response_with_functions.text = ""
            
            # Create final response (no function calls) to break the loop
            mock_final_candidate = MagicMock()
            mock_final_candidate.content = types.Content(
                role="model",
                parts=[types.Part(text="Files listed successfully.")]
            )
            
            mock_response_final = MagicMock()
            mock_response_final.candidates = [mock_final_candidate]
            mock_response_final.usage_metadata.prompt_token_count = 30
            mock_response_final.usage_metadata.candidates_token_count = 15
            mock_response_final.text = "Files listed successfully."
            
            mock_client.models.generate_content.side_effect = [
                mock_response_with_functions,
                mock_response_final
            ]
            
            # Mock single function result using factory
            mock_result = tool_resp("get_files_info", "file1.py\nfile2.py")
            mock_call_function.return_value = mock_result
            
            with patch('os.getcwd', return_value=str(test_dir)):
                result_messages = process_prompt("list files", messages=[])
                
                # Should work without error
                assert mock_call_function.call_count == 1
                assert len(result_messages) >= 2  # user + model + tool


def test_function_response_parts_match_function_calls():
    """The number of function response parts should match the number of function call parts."""
    
    with patch('staffer.main.get_client') as mock_get_client:
        with patch('staffer.main.call_function') as mock_call_function:
            test_dir = Path("/test/directory")
            
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # Three function calls
            from google.genai.types import FunctionCall
            function_calls = [
                FunctionCall(name="get_files_info", args={}),
                FunctionCall(name="get_file_content", args={"file_path": "file1.py"}),
                FunctionCall(name="get_file_content", args={"file_path": "file2.py"})
            ]
            
            mock_candidate = MagicMock()
            mock_candidate.content = types.Content(
                role="model",
                parts=[types.Part(function_call=call) for call in function_calls]
            )
            
            mock_response_with_functions = MagicMock()
            mock_response_with_functions.candidates = [mock_candidate]
            mock_response_with_functions.usage_metadata.prompt_token_count = 100
            mock_response_with_functions.usage_metadata.candidates_token_count = 50
            mock_response_with_functions.text = ""
            
            # Create final response (no function calls) to break the loop
            mock_final_candidate = MagicMock()
            mock_final_candidate.content = types.Content(
                role="model",
                parts=[types.Part(text="All function calls completed.")]
            )
            
            mock_response_final = MagicMock()
            mock_response_final.candidates = [mock_final_candidate]
            mock_response_final.usage_metadata.prompt_token_count = 40
            mock_response_final.usage_metadata.candidates_token_count = 20
            mock_response_final.text = "All function calls completed."
            
            mock_client.models.generate_content.side_effect = [
                mock_response_with_functions,
                mock_response_final
            ]
            
            # Mock function results using factories
            mock_results = [
                tool_resp(call.name, f"result for {call.name}") for call in function_calls
            ]
            mock_call_function.side_effect = mock_results
            
            with patch('os.getcwd', return_value=str(test_dir)):
                result_messages = process_prompt("multiple calls", messages=[])
                
                # Find the tool message in results
                tool_messages = [msg for msg in result_messages if msg.role == "tool"]
                
                # Should have exactly one tool message with multiple parts
                assert len(tool_messages) == 1, \
                    f"Expected 1 tool message, got {len(tool_messages)}"
                
                tool_message = tool_messages[0]
                
                # Should have same number of function response parts as function calls
                assert len(tool_message.parts) == len(function_calls), \
                    f"Expected {len(function_calls)} response parts, got {len(tool_message.parts)}"
                
                # Each part should be a function response
                for part in tool_message.parts:
                    assert hasattr(part, 'function_response'), \
                        "Each part should be a function response"
                    assert part.function_response is not None, \
                        "Function response should not be None"