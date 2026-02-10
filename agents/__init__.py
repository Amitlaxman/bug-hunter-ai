"""
Modular agents for C++ (RDI) bug detection.

- Code Parsing Agent: structures code (line-numbered) for downstream agents.
- Bug Detection Agent: identifies bug presence and first manifest line.
- MCP Doc Lookup Agent: retrieves relevant docs via MCP server.
- Explanation Generation Agent: produces explanation grounded in MCP docs.
"""

from agents.parsing import parse_code, format_parsed_for_prompt
from agents.mcp_client import search_documents
from agents.mcp_lookup import lookup_docs, format_chunks_for_prompt
from agents.detection import detect_bug
from agents.explanation import generate_explanation

__all__ = [
    "parse_code",
    "format_parsed_for_prompt",
    "search_documents",
    "lookup_docs",
    "format_chunks_for_prompt",
    "detect_bug",
    "generate_explanation",
]
