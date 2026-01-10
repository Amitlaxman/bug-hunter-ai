import json
import os
import re
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

def get_files_info(working_directory, directory=None):
    abs_working_dir = os.path.abspath(working_directory)
    directory = directory or "."
    abs_directory = os.path.abspath(os.path.join(abs_working_dir, directory))
    if not abs_directory.startswith(abs_working_dir):
        return f'Error: "{directory}" is not in the working directory'

    final_response = ""
    contents = os.listdir(abs_directory)
    for content in contents:
        content_path = os.path.join(abs_directory, content)
        is_dir = os.path.isdir(content_path)
        size = os.path.getsize(content_path)
        final_response += f"- {content}: file_size={size} bytes, is_dir={is_dir}\n"
    return final_response

def get_file_content(working_directory, file_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(abs_working_dir, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'

    try:
        with open(abs_file_path, "r") as file:
            file_content_string = file.read(int(os.getenv("MAX_CHARS")))
            if len(file_content_string) >= int(os.getenv("MAX_CHARS")):
                file_content_string += f"\n...File '{file_path}' truncated at {int(os.getenv("MAX_CHARS"))} characters"
        return file_content_string
    except Exception as e:
        return f'Error: {e}'

def write_file(working_directory, file_path, content):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(abs_working_dir, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'

    parent_dir = os.path.dirname(abs_file_path)
    if not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception as e:
            return f'Could not create parent dirs: {parent_dir} = {e}'
    try:
        with open(abs_file_path, "w") as file:
            file.write(content)
        return f'File "{file_path}" written successfully'
    except Exception as e:
        return f'Could not write to file: {file_path}, {e}'

def run_python_file(working_directory, file_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(abs_working_dir, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'
    if not file_path.endswith(".py"):
        return f'Error: "{file_path}" is not a Python file'

    try:
        output = subprocess.run(
            [sys.executable, file_path],
            cwd=abs_working_dir,
            timeout=30,
            capture_output=True,
            text=True
        )
        final_string = f"STDOUT: {output.stdout}\nSTDERR: {output.stderr}\n"
        if not output.stdout and not output.stderr:
            final_string += "No output produced.\n"
        if output.returncode != 0:
            final_string += f"Process exited with code {output.returncode}\n"
        return final_string
    except subprocess.TimeoutExpired:
        return f'Error: Python file execution timed out after 30 seconds'
    except Exception as e:
        return f'Error executing Python file: {e}'

def call_tool(fn_name, fn_args, working_directory, verbose=False):
    fn = globals().get(fn_name)
    if not fn:
        return f"Error: Unknown function '{fn_name}'"
    
    try:
        return fn(working_directory, **fn_args)
    except TypeError as e:
        return f"Error: Missing required arguments - {e}"
    except Exception as e:
        return f"Error: {e}"

def get_api_response(client, messages, tools, max_retries=5):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=os.getenv("MODEL"),
                messages=messages,
                tools=tools
            )
        except Exception as e:
            error_str = str(e)
            if "does not support tools" in error_str or "tool" in error_str.lower():
                print(f"# Error: Model does not support function calling")
                print(f"# Try a different model or install one that supports tools:")
                print(f"#   ollama pull llama3.2:3b")
                return None
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"# API error, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"# Error: API unavailable after {max_retries} attempts")
                print(f"# {e}")
                return None
    return None

def parse_and_execute_text_tool_call(content, messages, working_directory, verbose=False):
    content = content.strip()
    tool_call_match = re.search(r'\{[^}]*"name"\s*:\s*"([^"]+)"[^}]*"arguments"\s*:\s*(\{[^}]+\})', content)

    if tool_call_match:
        fn_name = tool_call_match.group(1)
        try:
            fn_args = json.loads(tool_call_match.group(2))
        except json.JSONDecodeError:
            fn_args = {}

        print(f"# Calling function: {fn_name}")
        if verbose:
            print(f"  Arguments: {fn_args}")

        result = call_tool(fn_name, fn_args, working_directory, verbose)

        if verbose:
            result_str = str(result)
            print(f"  Result: {result_str[:200]}..." if len(result_str) > 200 else f"  Result: {result}")

        messages.append({
            "role": "assistant",
            "content": content
        })
        messages.append({
            "role": "user",
            "content": f"Tool result: {result}\n\nRemember: Respond in English only."
        })
        return True
    else:
        print("# Final response:")
        print(content)
        return False

def handle_structured_tool_calls(message, messages, working_directory, verbose=False):
    messages.append(message)

    for tool_call in message.tool_calls:
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        print(f"# Calling function: {fn_name}")
        if verbose:
            print(f"  Arguments: {fn_args}")

        result = call_tool(fn_name, fn_args, working_directory, verbose)

        if verbose:
            result_str = str(result)
            print(f"  Result: {result_str[:200]}..." if len(result_str) > 200 else f"  Result: {result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })
        messages.append({
            "role": "user",
            "content": "Remember: Respond in English only."
        })