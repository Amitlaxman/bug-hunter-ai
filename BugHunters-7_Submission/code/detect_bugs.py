"""
Entrypoint for the C++ bug detection pipeline.

Reads samples from CSV (default: samples.csv), runs modular agents with MCP
documentation lookup, and outputs CSV with columns: ID, Bug Line, Explanation.

Usage:
  python detect_bugs.py [input.csv] [-o output.csv] [--no-mcp] [-n 5]
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.orchestrator import main

if __name__ == "__main__":
    main()
