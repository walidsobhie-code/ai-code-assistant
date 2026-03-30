#!/usr/bin/env python3
"""
AI Code Assistant - Query engine with LangChain
Ask questions about your codebase
"""
import os
import json
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

try:
    from langchain_openai import ChatOpenAI
    from langchain.chains import RetrievalQA
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

load_dotenv()

class CodeAssistant:
    """AI Code Assistant using RAG"""
    
    def __init__(self, index_dir: str = "./code_index"):
        self.index_dir = index_dir
        self.llm = None
        self.chain = None
        self._setup()
    
    def _setup(self):
        if not LANGCHAIN_AVAILABLE:
            return
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY not set")
            return
        
        if not os.path.exists(self.index_dir):
            print(f"⚠️ No index found at {self.index_dir}. Run context_loader.py first.")
            return
        
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=api_key)
            vectorstore = Chroma(
                persist_directory=self.index_dir,
                embedding_function=embeddings
            )
            
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.7, openai_api_key=api_key)
            
            self.chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True
            )
            print("✅ Code Assistant ready!")
        
        except Exception as e:
            print(f"❌ Setup error: {e}")
    
    def query(self, question: str) -> Dict:
        """Ask a question about the codebase"""
        if not self.chain:
            return {
                "answer": "Codebase not indexed. Run: python context_loader.py --path ./your_project",
                "sources": []
            }
        
        try:
            result = self.chain({"query": question})
            sources = [doc.metadata.get("source", "unknown") for doc in result.get("source_documents", [])]
            
            return {
                "answer": result["result"],
                "sources": list(set(sources))
            }
        
        except Exception as e:
            return {"answer": f"Error: {e}", "sources": []}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Query your codebase")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    args = parser.parse_args()
    
    assistant = CodeAssistant()
    
    if args.interactive:
        print("💬 Code Assistant - Ask questions about your codebase")
        print("Type 'exit' to quit\n")
        while True:
            q = input("You: ")
            if q.lower() == 'exit':
                break
            result = assistant.query(q)
            print(f"\nAI: {result['answer']}\n")
            if result.get('sources'):
                print(f"📄 Sources: {', '.join(result['sources'][:5])}\n")
    
    elif args.question:
        result = assistant.query(args.question)
        print(f"\n💬 Answer:\n{result['answer']}\n")
        if result.get('sources'):
            print(f"📄 Sources: {', '.join(result['sources'][:5])}")
    
    else:
        print("""
💬 AI Code Assistant

Usage:
  python query_engine.py "How does auth work?"
  python query_engine.py -i  # Interactive mode

First, index your codebase:
  python context_loader.py --path ./your_project
        """)

if __name__ == "__main__":
    main()
