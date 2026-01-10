def tool(name, description, **params):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {k: {"type": "string", "description": v} for k, v in params.items()},
                "required": list(params.keys())
            }
        }
    }

tools = [
    tool("get_files_info", "List files in directory", directory="Directory path"),
    tool("get_file_content", "Read file contents", file_path="Path to file"),
    tool("write_file", "Write content to file", file_path="Path to file", content="Content to write"),
    tool("run_python_file", "Execute Python file", file_path="Path to Python file"),
]
