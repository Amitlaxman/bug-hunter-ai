> uv run main.py "fix my temperature app, it's not starting correctly"
# Calling function: get_files_info
# Calling function: get_file_content
# Calling function: write_file
# Calling function: run_python_file
# Calling function: write_file
# Calling function: run_python_file
# Final response:
# Great! The temperature app now seems to be working correctly. The output shows the expression and the result in a formatted way.


python -m uv run main.py "Fix the bug in temperature.py - celsius_to_fahrenheit formula is wrong. Test: 0°C should equal 32°F" --verbose

python -m uv run main.py "0°C should equal 32°F" --verbose

uv run main.py "0°C should equal 32°F" --verbose

uv run main.py "0°C should equal 32°F"


-----------------------------


Step-by-Step Flow
Step 1: Setup
Load environment variables from .env
Create an Ollama client pointing to localhost:11434
Define the system prompt with project structure and instructions
Parse the user's prompt from command line args
Step 2: Initialize Messages
Create a messages array with:
System message (instructions for the AI)
User message (the bug to fix)
Step 3: Send to LLM
Send messages + available tools to qwen2.5:14b via Ollama
The LLM analyzes the request and decides what tool to call
Step 4: Agentic Loop
If the LLM returns tool_calls:
Parse the function name and arguments
Execute the function (e.g., get_files_info, get_file_content, write_file)
Add the tool result to messages
Go back to Step 3 (send updated messages to LLM)
If no tool_calls:
Print the final response
Exit the loop
Example Execution
User: "Fix the bug in pkg/calculator.py"         
         ↓
LLM → tool_call: get_files_info(".")         
         ↓
Result: [main.py, pkg/, tests.py...]
         ↓
LLM → tool_call: get_file_content("pkg/calculator.py")
         ↓
Result: [shows "+": lambda a, b: a - b (the bug)]
         ↓
LLM → tool_call: write_file("pkg/calculator.py", fixed_content)
         ↓
Result: "File written successfully"
         ↓
LLM → tool_call: run_python_file("main.py")
         ↓
Result: "STDOUT: 25.0"
         ↓
LLM → Final response: "Bug fixed!"
         ↓
EXIT


Key Components
Component	Purpose
WORKING_DIRECTORY	All file operations are relative to ./calculator
tools[]	JSON schema describing available functions for the LLM
function_map{}	Maps function names to actual Python functions
messages[]	Conversation history that grows with each tool call