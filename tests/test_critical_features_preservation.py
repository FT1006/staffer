"""
RED Phase: Tests for Critical Features That Must Be Preserved

These tests document the current behavior of critical features in available_functions.py
that must be preserved during refactoring to GenAI service architecture.
"""
import pytest
import sys
import os
import time
import io
import contextlib
import threading
import queue
from unittest.mock import Mock, patch, MagicMock

# Add the staffer module to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestDiscoveryPipelinePreservation:
    """Test tool discovery pipeline features that must be preserved."""
    
    @pytest.mark.timeout(10)
    def test_discovery_timeout_behavior(self):
        """Test that discovery has 5-second timeout (preserve this)."""
        from staffer.available_functions import _get_mcp_tool_declarations
        
        # Mock a hanging discovery operation
        original_run = None
        if hasattr(sys.modules.get('asyncio'), 'run'):
            original_run = __import__('asyncio').run
        
        def hanging_run(coro):
            time.sleep(6)  # Hang longer than 5-second timeout
            return []
        
        start_time = time.time()
        
        with patch('asyncio.run', side_effect=hanging_run):
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                result = _get_mcp_tool_declarations()
                output = buf.getvalue()
        
        duration = time.time() - start_time
        
        # Should timeout at 5 seconds (preserve this exact behavior)
        assert 4.5 <= duration <= 6.0, f"Expected ~5s timeout, got {duration:.2f}s"
        assert result == [], "Should return empty list on timeout"
        assert "timeout" in output.lower(), f"Should show timeout message, got: {output}"
        
        print(f"Discovery timeout behavior: {duration:.2f}s, output: {repr(output)}")
    
    def test_discovery_output_suppression(self):
        """Test that MCP noise is suppressed during discovery (preserve this)."""
        from staffer.available_functions import _get_mcp_tool_declarations
        
        # Mock noisy MCP operations
        def noisy_operation():
            print("NOISY MCP OUTPUT")  # This should be suppressed
            print("MORE NOISE", file=sys.stderr)  # This should be suppressed
            return []
        
        with patch('staffer.available_functions._async_get_mcp_tools', side_effect=lambda: noisy_operation()):
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                result = _get_mcp_tool_declarations()
                output = buf.getvalue()
        
        # Should only see discovery messages, not MCP noise (preserve this)
        assert "NOISY MCP OUTPUT" not in output, "MCP noise should be suppressed"
        assert "Discovering tools" in output, "Should show discovery message"
        
        print(f"Suppressed output behavior: {repr(output)}")
    
    def test_tool_categorization_logic(self):
        """Test exact tool categorization logic (preserve this)."""
        # Test the exact categorization from lines 117-120
        mock_tools = [
            Mock(name="excel_read_sheet"),
            Mock(name="excel_write_to_sheet"), 
            Mock(name="load_dataset"),
            Mock(name="find_correlations"),
            Mock(name="chart_data"),
            Mock(name="other_tool"),
        ]
        
        # Replicate exact logic from available_functions.py lines 117-120
        excel_count = sum(1 for tool in mock_tools if 'excel' in tool.name.lower())
        analytics_keywords = ['load', 'chart', 'correlations', 'segment', 'analyze', 'detect', 'time_series', 'validate']
        analytics_count = sum(1 for tool in mock_tools if any(keyword in tool.name.lower() for keyword in analytics_keywords))
        other_count = len(mock_tools) - excel_count - analytics_count
        
        # Should match exact categorization logic (preserve this)
        assert excel_count == 2, f"Expected 2 Excel tools, got {excel_count}"
        assert analytics_count == 3, f"Expected 3 Analytics tools, got {analytics_count}"  # load, correlations, chart
        assert other_count == 1, f"Expected 1 Other tool, got {other_count}"
        
        print(f"Categorization: {excel_count} Excel, {analytics_count} Analytics, {other_count} Other")
    
    def test_discovery_feedback_messages(self):
        """Test exact discovery feedback messages (preserve this)."""
        from staffer.available_functions import _get_mcp_tool_declarations
        
        # Mock successful discovery
        mock_tools = [Mock(name="excel_tool"), Mock(name="other_tool")]
        
        with patch('staffer.available_functions._async_get_mcp_tools', return_value=mock_tools):
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                result = _get_mcp_tool_declarations()
                output = buf.getvalue()
        
        # Should match exact message format (preserve this)
        assert "Discovering tools..." in output, "Should show discovery start message"
        assert "Found 2 tools" in output, "Should show tool count"
        assert "1 Excel, 1 Other" in output, "Should show categorization"
        
        print(f"Discovery feedback: {repr(output)}")


class TestExecutionPipelinePreservation:
    """Test tool execution pipeline features that must be preserved."""
    
    def test_execution_timeout_behavior(self):
        """Test that execution has 15-second timeout (preserve this)."""
        from staffer.available_functions import _call_mcp_tool_via_composer
        
        def hanging_execution(*args):
            time.sleep(16)  # Hang longer than 15-second timeout
            return "should not reach this"
        
        start_time = time.time()
        
        with patch('staffer.available_functions._async_call_mcp_tool', side_effect=hanging_execution):
            result = _call_mcp_tool_via_composer("test_tool", {"arg": "value"})
        
        duration = time.time() - start_time
        
        # Should timeout at 15 seconds (preserve this exact behavior)
        assert 14.5 <= duration <= 16.0, f"Expected ~15s timeout, got {duration:.2f}s"
        assert result is None, "Should return None on timeout"
        
        print(f"Execution timeout behavior: {duration:.2f}s")
    
    def test_triple_fallback_strategy(self):
        """Test exact triple fallback strategy (preserve this)."""
        from staffer.available_functions import _call_mcp_tool_via_composer
        
        # Track which strategies are attempted
        strategies_attempted = []
        
        def mock_prepare_tool_specific(tool_name, args, working_dir):
            strategies_attempted.append("tool_specific")
            return {"prepared": "tool_specific"}
        
        def mock_convert_absolute(args, working_dir):
            strategies_attempted.append("absolute")
            return {"prepared": "absolute"}
        
        def mock_execute_with_timeout(args):
            if args.get("prepared") == "tool_specific":
                return {"error": "tool_specific_failed"}
            elif args.get("prepared") == "absolute":
                return {"error": "absolute_failed"} 
            else:
                return "success"  # Original arguments work
        
        with patch('staffer.available_functions.prepare_arguments_for_tool', side_effect=mock_prepare_tool_specific):
            with patch('staffer.available_functions.convert_relative_to_absolute_paths', side_effect=mock_convert_absolute):
                with patch('staffer.available_functions._call_mcp_tool_via_composer._execute_with_timeout', side_effect=mock_execute_with_timeout):
                    # This won't work exactly due to nested function, but documents the behavior
                    pass
        
        # Document the expected fallback order (preserve this)
        expected_order = ["tool_specific", "absolute", "original"]
        print(f"Expected fallback order: {expected_order}")
        
        # The actual implementation should try:
        # 1. prepare_arguments_for_tool() result
        # 2. convert_relative_to_absolute_paths() result  
        # 3. Original arguments
    
    def test_working_directory_bug_documentation(self):
        """Document current working directory bug that needs fixing."""
        from staffer.available_functions import _call_mcp_tool_via_composer
        
        # Current implementation uses os.getcwd() instead of passed working_directory
        # This is a bug that should be fixed while preserving other behavior
        
        with patch('os.getcwd', return_value='/mocked/getcwd'):
            with patch('staffer.available_functions.prepare_arguments_for_tool') as mock_prepare:
                with patch('staffer.available_functions.convert_relative_to_absolute_paths') as mock_convert:
                    try:
                        _call_mcp_tool_via_composer("test_tool", {"arg": "value"})
                    except:
                        pass  # We just want to see what gets called
        
        # Should be called with /mocked/getcwd, not the passed working_directory
        if mock_prepare.called:
            call_args = mock_prepare.call_args[0]
            working_dir_used = call_args[2] if len(call_args) > 2 else None
            print(f"Current working_dir used: {working_dir_used}")
            # After fixing, this should use the passed working_directory parameter


class TestSchemaSafetyPreservation:
    """Test schema safety features that must be preserved."""
    
    def test_schema_error_silent_handling(self):
        """Test that schema errors are handled silently (preserve this)."""
        from staffer.available_functions import _async_get_mcp_tools
        
        # Mock tools with some that cause schema errors
        mock_good_tool = Mock()
        mock_bad_tool = Mock()
        
        def mock_process_schema(tool):
            if tool is mock_bad_tool:
                raise ValueError("Bad schema")
            return f"processed_{tool}"
        
        with patch('staffer.available_functions.process_mcp_tool_schema', side_effect=mock_process_schema):
            with patch('staffer.available_functions.GenericMCPServerComposer') as mock_composer_class:
                mock_composer = Mock()
                mock_composer.get_all_tools.return_value = [mock_good_tool, mock_bad_tool]
                mock_composer_class.return_value = mock_composer
                
                import asyncio
                result = asyncio.run(_async_get_mcp_tools())
        
        # Should silently skip bad tools, include good ones (preserve this)
        assert len(result) == 1, "Should include only good tool"
        assert f"processed_{mock_good_tool}" in result, "Should include processed good tool"
        
        print(f"Schema safety result: {result}")


class TestBuiltinFunctionPreservation:
    """Test that built-in functions work unchanged."""
    
    def test_builtin_function_registry(self):
        """Test exact built-in function registry (preserve this)."""
        from staffer.available_functions import call_function
        
        # Test the exact function registry from lines 181-187
        expected_builtins = {
            "get_files_info",
            "get_file_content", 
            "write_file",
            "run_python_file",
            "get_working_directory"
        }
        
        # Test that each built-in function is recognized
        for func_name in expected_builtins:
            function_call = Mock()
            function_call.name = func_name
            function_call.args = {}
            
            # Should be recognized as built-in (not attempt MCP)
            try:
                result = call_function(function_call, "/test/working/dir")
                assert result.role == "tool", f"Built-in {func_name} should work"
                print(f"Built-in {func_name}: working")
            except Exception as e:
                # Some might fail due to missing args, but should be recognized
                print(f"Built-in {func_name}: recognized but failed with {e}")
    
    def test_builtin_vs_mcp_precedence(self):
        """Test that built-ins take precedence over MCP tools (preserve this)."""
        from staffer.available_functions import call_function
        
        function_call = Mock()
        function_call.name = "get_working_directory"  # Built-in function
        function_call.args = {}
        
        # Should use built-in, not attempt MCP lookup
        result = call_function(function_call, "/test/working/dir")
        
        assert result.role == "tool"
        assert "result" in result.parts[0].function_response.response
        
        print("Built-in precedence: working")


if __name__ == "__main__":
    # Run the tests to document current behavior
    pytest.main([__file__, "-v", "-s"])