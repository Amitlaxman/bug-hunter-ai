"""
Code Parsing Agent: normalizes and structures code snippets for downstream agents.

Output: list of {line_number, line_content} for exact bug-line reporting.
"""

from typing import TypedDict


class LineInfo(TypedDict):
    line_number: int
    line_content: str


def parse_code(code: str) -> list[LineInfo]:
    """
    Parse raw code string into line-numbered structure.

    Args:
        code: Raw code snippet (e.g. from samples.csv Code column).

    Returns:
        List of {"line_number": int, "line_content": str}, 1-based line numbers.
    """
    if not code or not code.strip():
        return []
    lines = code.splitlines()
    return [
        {"line_number": i + 1, "line_content": line}
        for i, line in enumerate(lines)
    ]


def format_parsed_for_prompt(parsed: list[LineInfo]) -> str:
    """Format parsed lines as a single string for LLM prompts."""
    return "\n".join(
        f"{p['line_number']:4d} | {p['line_content']}"
        for p in parsed
    )
