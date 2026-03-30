#!/usr/bin/env python3
"""Codebase Indexer - Index your code for AI understanding"""
import os
from pathlib import Path

def load_codebase(path: str):
    """Load and index codebase"""
    print(f"📂 Loading: {path}")
    files = []
    for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs']:
        files.extend(Path(path).rglob(f'*{ext}'))
    print(f"Found {len(files)} code files")
    return files

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    load_codebase(path)
