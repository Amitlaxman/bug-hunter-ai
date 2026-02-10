"""
MCP Documentation Lookup Agent: builds queries from code/context and calls
the MCP server's search_documents to retrieve relevant docs/bug patterns.
"""

import os
from typing import Any

from agents.mcp_client import search_documents


def generate_search_queries(
    code_snippet: str, hypothesis: str | None = None, verbose: bool = False
) -> list[str]:
    """
    Generate targeted search queries by combining LLM analysis with 
    regex-based API extraction for RDI-specific code.
    """
    from agent_core.llm_client import make_client
    import re

    queries = []

    # 1. Regex-based extraction of RDI methods (e.g., rdi.smartVec().writeData -> smartVec, writeData)
    # Look for patterns like .methodName()
    methods = re.findall(r"\.([a-zA-Z0-9_]+)\(", code_snippet)
    # Look for rdi.objectName
    objects = re.findall(r"rdi\.([a-zA-Z0-9_]+)", code_snippet)
    
    technical_terms = list(set(methods + objects))
    for term in technical_terms[:5]:
        queries.append(f"RDI API {term}")

    # 2. LLM-based query generation
    try:
        system = """You are a C++/RDI expert. Suggest 2 specific documentation search queries for the provided code.
Focus on the most suspicious API calls or sequence of operations.
Return only the queries, one per line, no numbering. Do not include quotes."""
        
        user = f"Code:\n{code_snippet[:1000]}\n"
        if hypothesis:
            user += f"Hypothesis: {hypothesis}\n"

        client = make_client()
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=60,
        )
        llm_content = (response.choices[0].message.content or "").strip()
        llm_queries = [q.strip("- ").strip('"').strip() for q in llm_content.splitlines() if q.strip()]
        queries.extend(llm_queries)
    except Exception:
        pass

    # 3. Fallback: First line of code
    first_line = code_snippet.strip().split("\n")[0][:80].strip()
    if first_line:
        queries.append(f"RDI {first_line}")

    # Deduplicate and limit
    final_queries = []
    seen = set()
    for q in queries:
        q_clean = q.lower()
        if q_clean not in seen:
            seen.add(q_clean)
            final_queries.append(q)
            
    if verbose:
        print(f"[Lookup] Final search queries: {final_queries}")
    
    return final_queries[:6]


def lookup_docs(
    code_snippet: str,
    hypothesis: str | None = None,
    top_k: int = 10,
    timeout: float = 30.0,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """
    Retrieve relevant documentation and bug patterns from the MCP server.
    """
    queries = generate_search_queries(code_snippet, hypothesis, verbose=verbose)

    all_chunks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for q in queries:
        try:
            results = search_documents(q, timeout=timeout)
            for r in results:
                text = (r.get("text") or "").strip()
                if text and text not in seen and not r.get("error"):
                    seen.add(text)
                    all_chunks.append(r)
        except Exception as e:
            if verbose:
                print(f"[Lookup] Error searching for '{q}': {e}")
            continue
        if len(all_chunks) >= top_k:
            break
            
    return all_chunks[:top_k]


def format_chunks_for_prompt(chunks: list[dict[str, Any]], max_chars: int = 4000) -> str:
    """Format retrieved chunks as a single string for LLM prompts."""
    if not chunks:
        return ""
        
    parts = []
    total = 0
    for i, c in enumerate(chunks, 1):
        text = (c.get("text") or "").strip()
        score = c.get("score")
        # Truncate text if it's huge
        if len(text) > 2000:
            text = text[:2000] + "... (truncated)"
            
        block = (
            f"--- Documentation Chunk {i} ---\n{text}"
        )
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
