"""
MCP client for the existing ABH_Server (FastMCP SSE on port 8003).

Calls search_documents(query) to retrieve relevant document chunks for
documentation grounding in the bug detection pipeline.
"""

import asyncio
import os
from typing import Any


def search_documents(query: str, url: str | None = None, timeout: float = 30.0) -> list[dict[str, Any]]:
    """
    Search documents using the MCP server's vector retrieval (sync wrapper).

    Args:
        query: Search query string.
        url: MCP SSE URL (default from MCP_SERVER_URL or http://localhost:8003/sse).
        timeout: Request timeout in seconds.

    Returns:
        List of dicts with "text" and "score" keys (same as server's search_documents).
    """
    return asyncio.run(_search_documents_async(query, url=url, timeout=timeout))


async def _search_documents_async(
    query: str, url: str | None = None, timeout: float = 30.0
) -> list[dict[str, Any]]:
    try:
        from fastmcp import Client
        from fastmcp.client.transports import SSETransport
    except ImportError:
        raise ImportError(
            "FastMCP client requires: pip install fastmcp"
        ) from None

    base_url = url or os.getenv("MCP_SERVER_URL", "http://localhost:8003/sse")
    transport = SSETransport(url=base_url)
    client = Client(transport)

    async with client:
        result = await asyncio.wait_for(
            client.call_tool("search_documents", {"query": query}),
            timeout=timeout,
        )

    if getattr(result, "is_error", False):
        err_msg = (
            result.content[0].text
            if result.content
            else "search_documents failed"
        )
        return [{"text": "", "score": 0.0, "error": err_msg}]

    # FastMCP may return .data as list; or JSON in content blocks
    data = getattr(result, "data", None)
    if isinstance(data, list) and data:
        return data
    content = getattr(result, "content", []) or []
    for block in content:
        if hasattr(block, "text") and block.text:
            import json
            try:
                parsed = json.loads(block.text)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict) and "text" in parsed:
                    return [parsed]
            except json.JSONDecodeError:
                pass
    return []
