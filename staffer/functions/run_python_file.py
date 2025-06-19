import os
import subprocess
from google.genai import types

def run_python_file(working_directory, file_path):
    working_dir_abs_path = os.path.abspath(working_directory)
    file_abs_path = os.path.abspath(os.path.join(working_dir_abs_path, file_path))
    if not file_abs_path.startswith(working_dir_abs_path):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
    if not os.path.exists(file_abs_path):
        return f'Error: File "{file_path}" not found.'
    if not file_abs_path.endswith('.py'):
        return f'Error: File "{file_path}" is not a Python file.'
    try:
        args = ["python", file_abs_path]
        result = subprocess.run(args, timeout=30, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Process exited with code {result.returncode}"
        elif result.stdout is None:
            return "No output produced"
        return f'STDOUT: {result.stdout}\nSTDERR: {result.stderr}'
    except Exception as e:
        return f"Error: executing Python file: {e}"
    
schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Runs a Python file",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python file to run, relative to the working directory.",
            ),
        },
    ),
)