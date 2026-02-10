import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from functions.fn import (
    get_api_response,
    handle_structured_tool_calls,
    parse_and_execute_text_tool_call,
)
from agent_core.llm_client import make_client
from prompts import get_system_prompt
from tools import tools


load_dotenv()


def main():
    client = make_client()

    if len(sys.argv) < 2:
        print("Usage: python main.py <prompt> [--verbose]")
        sys.exit(1)

    verbose = "--verbose" in sys.argv
    prompt = sys.argv[1]

    working_directory = os.getenv("WORKING_DIRECTORY")

    print(f"\n{'='*70}")
    print("BUG HUNTER AI - Starting Agent")
    print(f"{'='*70}")
    print(f"Working Directory: {working_directory}")
    print(f"User Prompt: {prompt}")
    if verbose:
        print(f"Verbose mode: ENABLED")
    print(f"{'='*70}\n")

    messages = [
        {"role": "system", "content": get_system_prompt(working_directory)},
        {
            "role": "user",
            "content": f"{prompt}\n\nIMPORTANT: Respond in English only.",
        },
    ]

    while True:
        response = get_api_response(
            client, messages, tools, int(os.getenv("MAX_RETRIES"))
        )
        if not response:
            return

        message = response.choices[0].message

        if message.tool_calls:
            handle_structured_tool_calls(
                message, messages, working_directory, verbose
            )
        elif message.content:
            if not parse_and_execute_text_tool_call(
                message.content, messages, working_directory, verbose
            ):
                break
        else:
            print(f"\n{'='*70}")
            print("FINAL RESPONSE: (empty)")
            print(f"{'='*70}\n")
            break

    if verbose and response.usage:
        print(f"\n{'='*70}")
        print("TOKEN USAGE")
        print(f"{'='*70}")
        print(f"   Prompt tokens:    {response.usage.prompt_tokens:,}")
        print(f"   Response tokens:   {response.usage.completion_tokens:,}")
        print(f"   Total tokens:      {response.usage.total_tokens:,}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    main()