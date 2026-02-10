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

    system = f"""You are an RDI expert. Write a 1-sentence explanation of the bug.
1. {docs_instruction}
2. Incorporate the detection reasoning.
3. Be remarkably concise. STRICTLY 1 SENTENCE. Maximum 60 words ONLY.
4. Use format: BUG: <bug description> and do not cite chunk sources."""

    reasoning_part = f"\nReasoning: {detection_reasoning}\n" if detection_reasoning else ""

    user = f"""Code:
{code[:1000]}

Line: {bug_line}
{reasoning_part}
{f"Docs:\n{docs_text}" if docs_text else ""}

Write 1-sentence explanation:"""

    try:
        client = make_client()
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=80, # Reduced
        )
        content = (response.choices[0].message.content or "").strip()
        return content.replace("\n", " ").strip() or "Bug on line {}.".format(bug_line)
    except Exception as e:
        return f"Bug on line {bug_line}. (Explanation unavailable: {e})"
