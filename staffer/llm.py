"""LLM client abstraction for dependency injection."""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def _default_client_factory():
    """Default factory that creates real Google AI client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


# Client factory - can be replaced for testing
_client_factory = _default_client_factory


def get_client():
    """Get the current LLM client (real or fake)."""
    return _client_factory()


def set_client_factory(factory):
    """Set a custom client factory (for testing)."""
    global _client_factory
    _client_factory = factory