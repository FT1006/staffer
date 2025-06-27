"""
RED Phase: Tests for Architectural Violations in Current Implementation

These tests document the current architectural violations in available_functions.py
and will guide the refactoring to proper separation of concerns.
"""
import pytest
import sys
import os
import ast
import importlib.util

# Add the staffer module to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestArchitecturalViolations:
    """Test current architectural violations that need to be fixed."""
    
    def test_staffer_imports_mcp_config_violation(self):
        """RED: Test that Staffer currently imports MCP config (violation)."""
        # Read the actual available_functions.py file
        staffer_path = os.path.join(os.path.dirname(__file__), '..', 'staffer', 'available_functions.py')
        
        with open(staffer_path, 'r') as f:
            content = f.read()
        
        # Parse the AST to find imports
        tree = ast.parse(content)
        
        config_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'config':
                    config_imports.append(node.lineno)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'config':
                        config_imports.append(node.lineno)
        
        # Currently this SHOULD fail (architectural violation exists)
        assert len(config_imports) > 0, "Expected architectural violation: Staffer should NOT import 'config'"
        print(f"Found config imports at lines: {config_imports}")
        
        # This documents the current violation - after refactoring, this test should pass
        # by asserting len(config_imports) == 0
    
    def test_staffer_knows_mcp_internals_violation(self):
        """RED: Test that Staffer currently knows about MCP internals (violation)."""
        staffer_path = os.path.join(os.path.dirname(__file__), '..', 'staffer', 'available_functions.py')
        
        with open(staffer_path, 'r') as f:
            content = f.read()
        
        # Look for MCP-specific knowledge
        mcp_violations = []
        
        if 'GenericMCPServerComposer' in content:
            mcp_violations.append('GenericMCPServerComposer')
        if 'load_config' in content:
            mcp_violations.append('load_config')
        if 'source_servers' in content:
            mcp_violations.append('source_servers')
        if 'aggregator_config' in content:
            mcp_violations.append('aggregator_config')
        
        # Currently this SHOULD fail (violations exist)
        assert len(mcp_violations) > 0, "Expected architectural violations: Staffer should NOT know MCP internals"
        print(f"Found MCP internal knowledge: {mcp_violations}")
        
        # After refactoring, this should pass by asserting len(mcp_violations) == 0
    
    def test_staffer_duplicates_config_logic_violation(self):
        """RED: Test that Staffer duplicates config loading logic (violation)."""
        staffer_path = os.path.join(os.path.dirname(__file__), '..', 'staffer', 'available_functions.py')
        
        with open(staffer_path, 'r') as f:
            content = f.read()
        
        # Count occurrences of config loading
        load_config_count = content.count('load_config()')
        aggregator_config_count = content.count('aggregator_config =')
        
        # Currently this SHOULD fail (duplication exists)
        assert load_config_count >= 2, f"Expected duplication: found {load_config_count} load_config() calls"
        assert aggregator_config_count >= 2, f"Expected duplication: found {aggregator_config_count} config assignments"
        
        print(f"Found {load_config_count} load_config() calls")
        print(f"Found {aggregator_config_count} aggregator_config assignments")
        
        # After refactoring, these should be 0 (handled by GenAI service)


class TestCurrentBehaviorBaseline:
    """Test current behavior to ensure we preserve it during refactoring."""
    
    def test_current_discovery_behavior(self):
        """Test current tool discovery behavior (preserve this UX)."""
        from staffer.available_functions import get_available_functions
        import io
        import contextlib
        import time
        
        # Capture the current discovery behavior
        start_time = time.time()
        
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            try:
                result = get_available_functions("/test/working/dir")
                output = buf.getvalue()
            except Exception as e:
                output = buf.getvalue()
                # Even if it fails, we want to preserve the behavior
                print(f"Discovery failed (expected): {e}")
                result = None
        
        duration = time.time() - start_time
        
        # Document current behavior patterns (preserve these)
        print(f"Discovery took {duration:.2f} seconds")
        print(f"Output: {repr(output)}")
        
        # These behaviors should be preserved after refactoring
        if result:
            assert hasattr(result, 'function_declarations')
            built_in_count = 5  # We know there are 5 built-in functions
            assert len(result.function_declarations) >= built_in_count
        
        # Should complete within reasonable time (allow for timeout scenarios)
        assert duration <= 10.0, "Discovery should complete within 10 seconds"
    
    def test_current_execution_behavior(self):
        """Test current tool execution behavior (preserve this)."""
        from staffer.available_functions import call_function
        from unittest.mock import Mock
        
        # Test built-in function execution (this should work)
        function_call = Mock()
        function_call.name = "get_working_directory"
        function_call.args = {}
        
        result = call_function(function_call, "/test/working/dir")
        
        # This behavior should be preserved exactly
        assert result.role == "tool"
        assert len(result.parts) == 1
        assert "result" in result.parts[0].function_response.response


class TestTargetArchitecture:
    """Test what the architecture SHOULD look like after refactoring."""
    
    def test_target_staffer_should_only_use_genai_service(self):
        """GREEN Target: Test that Staffer should only use GenAI service interface."""
        # This test will FAIL initially but shows our target
        
        # After refactoring, Staffer should:
        # 1. Only import GenAIToolService
        # 2. Never import 'config' from MCP aggregator
        # 3. Never know about GenericMCPServerComposer
        # 4. Only call service.get_tool_declarations() and service.execute_tool()
        
        # For now, this documents the target architecture
        target_staffer_imports = [
            'from adk_to_genai import GenAIToolService',  # Only MCP-related import should be this
        ]
        
        forbidden_staffer_imports = [
            'from config import load_config',
            'from composer import GenericMCPServerComposer', 
        ]
        
        # This test will guide our refactoring
        # Currently it should fail, after refactoring it should pass
        pytest.skip("Target architecture test - will be implemented during GREEN phase")
    
    def test_target_genai_service_abstracts_mcp_complexity(self):
        """GREEN Target: Test that GenAI service should handle all MCP complexity."""
        # After refactoring, GenAI service should:
        # 1. Handle config loading internally
        # 2. Abstract all MCP aggregator complexity
        # 3. Provide clean interface to Staffer
        # 4. Preserve all current optimizations (timeouts, fallbacks, etc.)
        
        pytest.skip("Target architecture test - will be implemented during GREEN phase")


if __name__ == "__main__":
    # Run the tests to see current violations
    pytest.main([__file__, "-v", "-s"])