import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from functions.fn import get_api_response, handle_structured_tool_calls, parse_and_execute_text_tool_call
from openai import OpenAI  # type: ignore
from prompts import get_system_prompt
from tools import tools


load_dotenv()


def main():
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    if len(sys.argv) < 2:
        print("Usage: python main.py <prompt> [--verbose]")
        sys.exit(1)

    verbose = "--verbose" in sys.argv
    prompt = sys.argv[1]

    messages = [
        {"role": "system", "content": get_system_prompt(os.getenv("WORKING_DIRECTORY"))},
        {"role": "user", "content": f"{prompt}\n\nIMPORTANT: Respond in English only."}
    ]

    while True:
        response = get_api_response(client, messages, tools, int(os.getenv("MAX_RETRIES")))
        if not response:
            return

        message = response.choices[0].message

        if message.tool_calls:
            handle_structured_tool_calls(message, messages, os.getenv("WORKING_DIRECTORY"), verbose)
        elif message.content:
            if not parse_and_execute_text_tool_call(message.content, messages, os.getenv("WORKING_DIRECTORY"), verbose):
                break
        else:
            print("# Final response: (empty)")
            break

    if verbose and response.usage:
        print(f"\nPrompt tokens: {response.usage.prompt_tokens}")
        print(f"Response tokens: {response.usage.completion_tokens}")

if __name__ == "__main__":
    main()