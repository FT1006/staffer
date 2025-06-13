import os
from google.genai import types

def get_file_content(working_directory, file_path):
    working_dir_abs_path = os.path.abspath(working_directory)
    file_abs_path = os.path.abspath(os.path.join(working_dir_abs_path, file_path))
    if not file_abs_path.startswith(working_dir_abs_path):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
    if not os.path.isfile(file_abs_path):
        return f'Error: File not found or is not a regular file: "{file_path}"'
    try:
        with open(file_abs_path, 'r') as file:
            MAX_CHARS = 10000
            file_content_string = file.read(MAX_CHARS)
            if len(file_content_string) == MAX_CHARS:
                return f'{file_content_string}...File "{file_path}" truncated at {MAX_CHARS} characters'
            else:
                return file_content_string
    except Exception as e:
        return f'Error: {e}'
    
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Gets the content of a file",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to get the content of, relative to the working directory.",
            ),
        },
    ),
)