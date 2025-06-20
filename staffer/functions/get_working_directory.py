"""Function to get current working directory."""

from pathlib import Path
from google.genai import types


def get_working_directory(working_directory):
    """Returns the current working directory as a string."""
    return str(Path(working_directory).resolve())


# Schema for Google AI function calling
schema_get_working_directory = types.FunctionDeclaration(
    name="get_working_directory",
    description="Returns the current working directory path. MUST be called at session start.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={},
        required=[]
    )
)