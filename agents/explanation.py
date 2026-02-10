"""
Explanation Generation Agent: produces the final Explanation for the CSV,
referencing known bug patterns/docs from MCP.
"""

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def generate_explanation(
    code: str,
    bug_line: int,
    mcp_chunks: list[dict[str, Any]],
    detection_reasoning: str | None = None,
) -> str:
    """
    Generate a short explanation of the bug, grounded in MCP documentation.
    """
    from agent_core.llm_client import make_client
    from agents.mcp_lookup import format_chunks_for_prompt

    docs_text = format_chunks_for_prompt(mcp_chunks, max_chars=3500)
    
    docs_instruction = ""
    if docs_text:
        docs_instruction = "Reference the relevant documentation chunks provided (cite Chunk 1, Chunk 2, etc.)."
    else:
        docs_instruction = "No documentation was found in the search. Do NOT cite any 'Doc' or 'Chunk'. Explain the bug based on general C++ knowledge or the internal reasoning provided."

    system = f"""You are a C++/RDI bug explanation expert. Your task is to write a brief explanation of the bug that:
1. {docs_instruction}
2. Explains the error on the specific bug line.
3. Incorporates the internal reasoning provided by the detection expert.
4. Is 1-2 sentences only, suitable for a CSV column."""

    reasoning_part = f"\nInternal detection reasoning: {detection_reasoning}\n" if detection_reasoning else ""

    user = f"""Code snippet:
{code[:2500]}

Bug first manifests on line: {bug_line}
{reasoning_part}
{f"Documentation provided:\n{docs_text}" if docs_text else "No documentation available."}

Write the final Explanation:"""

    try:
        client = make_client()
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=150,
        )
        content = (response.choices[0].message.content or "").strip()
        return content.replace("\n", " ").strip() or "Bug on line {}.".format(bug_line)
    except Exception as e:
        return f"Bug on line {bug_line}. (Explanation unavailable: {e})"
