import os
from google.genai import types

def write_file(working_directory, file_path, content):
    working_dir_abs_path = os.path.abspath(working_directory)
    file_abs_path = os.path.abspath(os.path.join(working_dir_abs_path, file_path))
    if not file_abs_path.startswith(working_dir_abs_path):
        return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'
    if not os.path.exists(os.path.dirname(file_abs_path)):
        try:
            os.makedirs(os.path.dirname(file_abs_path))
        except Exception as e:
            return f'Error: {e}'
    try:
        with open(file_abs_path, 'w') as file:
            file.write(content)
    except Exception as e:
        return f'Error: {e}'
    return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes to a file",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to write to, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to the file.",
            ),
        },
    ),
)