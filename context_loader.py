#!/usr/bin/env python3
"""
AI Code Assistant - Real implementation with LangChain
Index and understand your codebase
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from langchain_community.document_loaders import TextLoader, DirectoryLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

load_dotenv()

# Supported code extensions
CODE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.cpp': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.md': 'Markdown',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.sh': 'Shell',
    '.sql': 'SQL',
}

class CodebaseIndexer:
    """Index codebase for AI understanding"""
    
    def __init__(self, persist_dir: str = "./code_index"):
        self.persist_dir = persist_dir
        self.embeddings = None
        self.vectorstore = None
        
        if LANGCHAIN_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    
    def load_codebase(self, path: str) -> List[Dict]:
        """Load all code files from directory"""
        path_obj = Path(path)
        files = []
        
        if not path_obj.exists():
            return []
        
        for ext in CODE_EXTENSIONS.keys():
            for file_path in path_obj.rglob(f"*{ext}"):
                # Skip common ignored directories
                if any(ignored in str(file_path) for ignored in ['node_modules', '.git', '__pycache__', 'venv', '.venv', 'build', 'dist']):
                    continue
                
                try:
                    relative = file_path.relative_to(path_obj)
                    language = CODE_EXTENSIONS.get(file_path.suffix, 'Unknown')
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    files.append({
                        'path': str(relative),
                        'language': language,
                        'content': content,
                        'size': len(content),
                        'lines': len(content.splitlines())
                    })
                except Exception as e:
                    continue
        
        return files
    
    def index_codebase(self, path: str) -> Dict:
        """Index codebase into vector store"""
        if not LANGCHAIN_AVAILABLE:
            return {"status": "needs_langchain", "files": 0}
        
        if not self.embeddings:
            return {"status": "needs_api_key", "files": 0}
        
        files = self.load_codebase(path)
        if not files:
            return {"status": "no_files", "files": 0}
        
        print(f"📂 Loading {len(files)} code files...")
        
        # Create documents
        documents = []
        for file in files:
            from langchain.schema import Document
            doc = Document(
                page_content=f"File: {file['path']}\nLanguage: {file['language']}\n\n{file['content'][:5000]}",
                metadata={"source": file['path'], "language": file['language']}
            )
            documents.append(doc)
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = splitter.split_documents(documents)
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )
        
        self.vectorstore.persist()
        
        return {
            "status": "success",
            "files": len(files),
            "chunks": len(chunks),
            "languages": list(set(f['language'] for f in files))
        }
    
    def get_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Get relevant code context for a query"""
        if not self.vectorstore:
            return []
        
        docs = self.vectorstore.similarity_search(query, k=top_k)
        return [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} for doc in docs]

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Codebase Indexer")
    parser.add_argument("--path", "-p", default=".", help="Path to codebase")
    parser.add_argument("--query", "-q", help="Query to search")
    args = parser.parse_args()
    
    indexer = CodebaseIndexer()
    
    if args.path:
        result = indexer.index_codebase(args.path)
        print(json.dumps(result, indent=2))
    
    if args.query:
        results = indexer.get_context(args.query)
        print(f"\n🔍 Found {len(results)} relevant files:")
        for r in results:
            print(f"  📄 {r['source']}")

if __name__ == "__main__":
    main()
