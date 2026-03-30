#!/usr/bin/env python3
"""Query Engine - Ask questions about your code"""
import sys

def query(codebase, question):
    """Ask a question about your codebase"""
    print(f"❓ Question: {question}")
    print("""
⚠️  This is a template.

To implement:
1. Use LangChain to load code as documents
2. Create a vector store index
3. Use RAG to answer questions

See: langchain.readthedocs.io
    """)
    return "[AI Answer]"

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How does this work?"
    query(".", q)
