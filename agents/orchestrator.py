"""
Orchestrator: runs the full pipeline (parse -> MCP lookup -> detect -> explain)
and outputs CSV with columns ID, Bug Line, Explanation.
"""

import csv
import io
import sys
from pathlib import Path
from typing import Any

# Project root for imports when run as script
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from agents.detection import detect_bug
from agents.explanation import generate_explanation
from agents.mcp_lookup import lookup_docs


def run_pipeline_row(
    sample_id: str,
    code: str,
    context: str | None = None,
    use_mcp: bool = True,
    verbose: bool = False,
) -> tuple[str, int, str]:
    """
    Run the pipeline for one code snippet.
    Collaboration: Lookup -> Detect (with Reasoning) -> Explain (using Docs + Reasoning).
    """
    if verbose:
        print(f"\n[Orchestrator] Processing Sample {sample_id}...")

    # 1. MCP Lookup (Agentic Querying)
    mcp_chunks = lookup_docs(code, hypothesis=context, timeout=25.0, verbose=verbose) if use_mcp else []
    if verbose:
        print(f"[Orchestrator] Retrieved {len(mcp_chunks)} doc chunks.")

    # 2. Bug Detection (returns reasoning)
    bug_present, bug_line, reasoning = detect_bug(code, mcp_chunks=mcp_chunks, verbose=verbose)
    if verbose:
        status = f"YES on line {bug_line}" if bug_present else "NO"
        # Clean reasoning for clean terminal output
        clean_reasoning = reasoning.replace("\r", " ").replace("\n", " ").strip()
        print(f"[Orchestrator] Bug Detected: {status}")
        print(f"[Orchestrator] Detection Reasoning: {clean_reasoning}")

    if not bug_present or bug_line <= 0:
        explanation = "No bug detected."
    else:
        # 3. Explanation Generation (grounded in MCP + reasoning)
        explanation = generate_explanation(code, bug_line, mcp_chunks, detection_reasoning=reasoning)
        if verbose:
            clean_explanation = explanation.replace("\r", " ").replace("\n", " ").strip()
            print(f"[Orchestrator] Explanation generated: {clean_explanation[:100]}...")

    return sample_id, bug_line, explanation


def run_pipeline_csv(
    input_path: Path | None = None,
    output_path: Path | None = None,
    use_mcp: bool = True,
    limit: int | None = None,
    verbose: bool = False,
) -> None:
    """
    Run pipeline on samples.csv (or given path) and write CSV with ID, Bug Line, Explanation.

    Args:
        input_path: Input CSV. Only columns ID, Context, Code (buggy) are read.
        output_path: Output CSV path; if None, print to stdout.
        use_mcp: Whether to call MCP server for documentation lookup.
        limit: If set, process only the first N rows (for testing).
    """
    # Input: only ID, Context, Code. We do not read Explanation or Correct Code.
    ID_COLUMN = "ID"
    CONTEXT_COLUMN = "Context"
    CODE_COLUMN = "Code"

    input_path = input_path or Path("samples.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    def _norm(s: str) -> str:
        return s.strip().replace("\ufeff", "")

    rows_out: list[tuple[str, int, str]] = []
    with open(input_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Normalize header names (BOM, spaces)
        fieldnames = reader.fieldnames or []
        fieldnames = [_norm(h) for h in fieldnames]
        reader.fieldnames = fieldnames
        id_idx = fieldnames.index(ID_COLUMN) if ID_COLUMN in fieldnames else 0
        context_idx = fieldnames.index(CONTEXT_COLUMN) if CONTEXT_COLUMN in fieldnames else 2
        code_idx = fieldnames.index(CODE_COLUMN) if CODE_COLUMN in fieldnames else 3
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            row = {_norm(k): (v or "") for k, v in row.items()}
            sample_id = row.get(ID_COLUMN) or (row.get(fieldnames[id_idx]) if id_idx < len(fieldnames) else "") or str(i + 1)
            context = row.get(CONTEXT_COLUMN) or (row.get(fieldnames[context_idx]) if context_idx < len(fieldnames) else "") or ""
            code = row.get(CODE_COLUMN) or (row.get(fieldnames[code_idx]) if code_idx < len(fieldnames) else "") or ""
            code = (code or "").strip()
            if not code:
                rows_out.append((sample_id, 0, "No code provided."))
                continue
            id_val, bug_line, explanation = run_pipeline_row(
                sample_id, code, context=context or None, use_mcp=use_mcp, verbose=verbose
            )
            rows_out.append((id_val, bug_line, explanation))

    out_buffer = io.StringIO()
    writer = csv.writer(out_buffer, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["ID", "Bug Line", "Explanation"])
    for r in rows_out:
        writer.writerow([r[0], r[1], r[2]])
    result = out_buffer.getvalue()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            f.write(result)
    else:
        sys.stdout.write(result)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="C++ Bug Detection Pipeline: output CSV with ID, Bug Line, Explanation."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="samples.csv",
        help="Input CSV path (default: samples.csv)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output CSV path (default: stdout)",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Disable MCP documentation lookup",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=None,
        help="Process only first N rows",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print raw model response when no bug is detected (for debugging)",
    )
    args = parser.parse_args()
    run_pipeline_csv(
        input_path=Path(args.input),
        output_path=Path(args.output) if args.output else None,
        use_mcp=not args.no_mcp,
        limit=args.limit,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
