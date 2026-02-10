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

    system = """You are a C++/RDI (SmartRDI API) expert. 
Your task is to identify the first line (1-based) where a bug manifests.

RDI bugs often involve multi-line sequences:
1. Missing prerequisite calls (e.g., calling burst() before begin()).
2. Invalid order of operations (e.g., RDI_END() before RDI_BEGIN()).
3. State conflicts across lines (e.g., setting a range on line 5 that makes line 10 invalid).
4. Missing cleanup or synchronization.

Analyze the ENTIRE sequence or block.
Identify the first line that is WRONG or represents the start of the ERROR.

Reply exactly in this format:
REASONING: <1-sentence description of the logic error>
BUG: YES
LINE: <line_number>

If no bug: BUG: NO, LINE: 0"""

    user = f"""Analyze this RDI code snippet for sequential and logic bugs.
{doc_section}

Code with Line Numbers:
{code_with_lines}

Identify the bug and the first line where the sequence fails."""

    try:
        client = make_client()
        model_name = os.getenv("MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=100, # Reduced
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
