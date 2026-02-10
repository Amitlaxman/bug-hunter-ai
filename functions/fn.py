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
                print(f"\n{'='*70}")
                print("ERROR: Model does not support function calling")
                print(f"{'='*70}")
                print("Try a different model or install one that supports tools:")
                print("   ollama pull llama3.2:3b")
                print(f"{'='*70}\n")
                return None
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"API error, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"\n{'='*70}")
                print(f"ERROR: API unavailable after {max_retries} attempts")
                print(f"{'='*70}")
                print(f"   {e}")
                print(f"{'='*70}\n")
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

        print(f"\n{'='*70}")
        print(f"TOOL CALL: {fn_name}")
        print(f"{'='*70}")
        if verbose:
            print(f"Arguments:")
            print(f"   {json.dumps(fn_args, indent=2)}")

        result = call_tool(fn_name, fn_args, working_directory, verbose)

        if verbose:
            result_str = str(result)
            if len(result_str) > 500:
                print(f"Result (truncated, {len(result_str)} chars):")
                print(f"   {result_str[:500]}...")
            else:
                print(f"Result:")
                # Format multi-line results nicely
                lines = result_str.split('\n')
                if len(lines) > 1:
                    for line in lines[:20]:  # Show first 20 lines
                        print(f"   {line}")
                    if len(lines) > 20:
                        print(f"   ... ({len(lines) - 20} more lines)")
                else:
                    print(f"   {result_str}")
        print(f"{'='*70}\n")

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
        print(f"\n{'='*70}")
        print("FINAL RESPONSE")
        print(f"{'='*70}")
        print(content)
        print(f"{'='*70}\n")
        return False

def handle_structured_tool_calls(message, messages, working_directory, verbose=False):
    messages.append(message)

    for idx, tool_call in enumerate(message.tool_calls, 1):
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        print(f"\n{'='*70}")
        print(f"🔧 TOOL CALL #{idx}: {fn_name}")
        print(f"{'='*70}")
        if verbose:
            print(f"Arguments:")
            print(f"   {json.dumps(fn_args, indent=2)}")

        result = call_tool(fn_name, fn_args, working_directory, verbose)

        if verbose:
            result_str = str(result)
            if len(result_str) > 500:
                print(f"Result (truncated, {len(result_str)} chars):")
                print(f"   {result_str[:500]}...")
            else:
                print(f"Result:")
                # Format multi-line results nicely
                lines = result_str.split('\n')
                if len(lines) > 1:
                    for line in lines[:20]:  # Show first 20 lines
                        print(f"   {line}")
                    if len(lines) > 20:
                        print(f"   ... ({len(lines) - 20} more lines)")
                else:
                    print(f"   {result_str}")
        print(f"{'='*70}\n")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })
        messages.append({
            "role": "user",
            "content": "Remember: Respond in English only."
        })