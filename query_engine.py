#!/usr/bin/env python3
"""AI Code Assistant - Using Ollama for code analysis"""
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder"

def query_code(question: str) -> dict:
    prompt = f"""You are a code assistant. Answer this question about code:
{question}

Provide a helpful, clear answer."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.status_code == 200:
            answer = response.json().get("response", "")
            return {"answer": answer[:500], "sources": []}
    except Exception as e:
        return {"answer": f"Ollama error: {e}", "sources": []}
    return {"answer": "Ollama not running", "sources": []}

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How does Python work?"
    result = query_code(question)
    print(f"💬 {result['answer'][:300]}")
