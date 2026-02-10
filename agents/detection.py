"""
Bug Detection Agent: decides if there is a bug and the exact line number
where the bug first manifests. Uses LLM with optional MCP retrieval context.
"""

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def detect_bug(
    code: str,
    mcp_chunks: list[dict[str, Any]] | None = None,
    verbose: bool = False,
) -> tuple[bool, int, str]:
    """
    Detect whether the code contains a bug and the first line where it manifests.
    Returns: (bug_present, bug_line, reasoning).
    """
    from agent_core.llm_client import make_client
    from agents.parsing import format_parsed_for_prompt, parse_code
    from agents.mcp_lookup import format_chunks_for_prompt

    parsed = parse_code(code)
    code_with_lines = format_parsed_for_prompt(parsed)
    doc_section = ""
    if mcp_chunks:
        doc_section = "\n\nRelevant RDI API Documentation & Bug Patterns:\n" + format_chunks_for_prompt(mcp_chunks, max_chars=3000)

    system = """You are a C++/RDI (SmartRDI API) bug detection expert. 
Your job is to identify the first line (1-based) where a bug manifests.
Bugs include: wrong API usage, invalid constants, incorrect method order, or syntax errors.

You MUST reply in exactly this format:
REASONING: <1-sentence description of the bug>
BUG: YES
LINE: <line_number>

If you are absolutely certain there is no bug:
REASONING: Code is correct.
BUG: NO
LINE: 0"""

    user = f"""Review this C++ snippet for RDI API bugs.
{doc_section}

Code to analyze:
{code_with_lines}

Identify the bug and the line number."""

    try:
        client = make_client()
        model_name = os.getenv("MODEL", "gpt-4o-mini")
        if verbose:
            print(f"[Detection] Using model: {model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=250,
        )
        content = (response.choices[0].message.content or "").strip()
        if verbose:
            print(f"[Detection] Raw response: {content}")
    except Exception as e:
        import sys
        sys.stderr.write(f"[detect_bug] API error: {e}\n")
        return False, 0, f"API Error: {e}"

    if "```" in content:
        content = re.sub(r"```[\w]*\n?", "", content).strip()
    
    # Flexible extraction
    reasoning = "Unknown reasoning."
    r_match = re.search(r"REASONING:\s*(.*)", content, re.IGNORECASE)
    if r_match:
        reasoning = r_match.group(1).strip()
    elif ":" in content and "BUG" not in content.split(":")[0]:
        # Try to guess reasoning if it's the first line before BUG:
        reasoning = content.splitlines()[0].strip()

    content_upper = content.upper()
    
    line = 0
    l_match = re.search(r"LINE:\s*(\d+)", content_upper)
    if l_match:
        line = int(l_match.group(1))
    
    bug_present = "BUG: YES" in content_upper or (line > 0 and "BUG" in content_upper)
    if "BUG: NO" in content_upper:
        bug_present = False
        line = 0

    return bug_present, line, reasoning
