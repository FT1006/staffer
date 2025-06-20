"""Fixtures shared across component tests; they do not hit the real Gemini API."""

import pytest
import contextlib
import os
from unittest.mock import MagicMock

try:
    from google.genai import types
except ImportError:
    pytest.skip("google.genai not available", allow_module_level=True)


class FakeGemini:
    """Fake Gemini client for testing that returns configurable responses."""
    
    def __init__(self, fc_name="get_files_info", fc_response=None):
        self.fc_name = fc_name
        self.fc_response = fc_response or {"result": ["test_file.py"]}
        self.call_count = 0
        self.last_request = None
    
    def generate_content(self, model=None, contents=None, config=None, **kwargs):
        """Generate a fake response with function call."""
        self.call_count += 1
        self.last_request = {
            'model': model,
            'contents': contents,
            'config': config,
            'kwargs': kwargs
        }
        
        # Create mock response
        response = MagicMock()
        response.text = f"I'll use {self.fc_name} to help you."
        response.usage_metadata.prompt_token_count = 10
        response.usage_metadata.candidates_token_count = 5
        response.usage_metadata.total_token_count = 15
        
        # Create candidate with function call
        candidate = MagicMock()
        candidate.content = types.Content(
            role="model",
            parts=[types.Part(
                function_call=types.FunctionCall(
                    name=self.fc_name, 
                    arguments="{}"
                )
            )]
        )
        candidate.finish_reason = "function_call"
        
        response.candidates = [candidate]
        return response


class FakeGeminiModels:
    """Fake models namespace for FakeGemini."""
    
    def __init__(self, gemini_instance):
        self.gemini = gemini_instance
    
    def generate_content(self, **kwargs):
        return self.gemini.generate_content(**kwargs)


class FakeGeminiClient:
    """Fake client that mimics Google AI client structure."""
    
    def __init__(self, fc_name="get_files_info", fc_response=None):
        self.gemini = FakeGemini(fc_name, fc_response)
        self.models = FakeGeminiModels(self.gemini)


@contextlib.contextmanager
def pushd(path):
    """Context manager to temporarily change directory."""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def fake_llm(monkeypatch):
    """Patch llm.get_client() so every call returns a FakeGeminiClient."""
    from staffer import llm
    original_factory = llm._client_factory          # capture

    fake_client = FakeGeminiClient()

    # Replace factory so llm.get_client() yields our fake
    monkeypatch.setattr(llm, "_client_factory", lambda: fake_client, raising=False)

    yield fake_client

    # Restore after test
    monkeypatch.setattr(llm, "_client_factory", original_factory, raising=False)


@pytest.fixture
def temp_cwd(tmp_path, monkeypatch):
    """Fixture that provides a temporary working directory."""
    with pushd(tmp_path):
        yield tmp_path


def assert_cwd_in_prompt(prompt, expected_cwd):
    """Helper to assert working directory is in prompt."""
    assert str(expected_cwd) in prompt, f"Expected {expected_cwd} in prompt: {prompt}"