#!/usr/bin/env python3
"""
AI Code Assistant - Understand and query your codebase
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Optional
from pathlib import Path

# Try imports
try:
    from langchain.text_splitter import Language
    from langchain.document_loaders import TextLoader, DirectoryLoader
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import tree_sitter
    from tree_sitter import Language as TSLanguage
    from tree_sitter import Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


# Supported languages
SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.sql': 'sql',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.json': 'json',
    '.xml': 'xml',
    '.html': 'html',
    '.css': 'css',
    '.md': 'markdown',
    '.txt': 'text'
}


class CodeIndexer:
    """Index codebase for semantic search"""

    def __init__(self, embedding_model: str = "openai"):
        self.embedding_model = embedding_model
        self.vectorstore = None
        self.embeddings = None
        self.indexed_files = []

    def index_directory(self, path: str, extensions: List[str] = None) -> Dict:
        """Index all code files in a directory"""
        print(f"📂 Indexing: {path}")

        if extensions is None:
            extensions = list(SUPPORTED_EXTENSIONS.keys())

        # Collect all files
        files = []
        for root, _, filenames in os.walk(path):
            # Skip common non-code directories
            skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv',
                        'dist', 'build', '.idea', '.vscode', 'target', 'coverage'}
            if any(skip in root for skip in skip_dirs):
                continue

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    files.append(os.path.join(root, filename))

        print(f"   Found {len(files)} files")

        if not files:
            return {"status": "error", "message": "No files found"}

        # Load and chunk files
        documents = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Get relative path for metadata
                rel_path = os.path.relpath(file_path, path)

                documents.append({
                    "content": content,
                    "metadata": {
                        "file": rel_path,
                        "extension": os.path.splitext(file_path)[1],
                        "size": len(content)
                    }
                })
                self.indexed_files.append(rel_path)

            except Exception as e:
                print(f"   ⚠️  Skipped {file_path}: {e}")

        print(f"   Loaded {len(documents)} documents")

        # Create vector store
        if LANGCHAIN_AVAILABLE:
            try:
                if embedding_model == "openai":
                    self.embeddings = OpenAIEmbeddings()
                else:
                    # Use default
                    self.embeddings = OpenAIEmbeddings()

                # Chunk by language
                texts = [d["content"] for d in documents]
                metadatas = [d["metadata"] for d in documents]

                # Use RecursiveCharacterTextSplitter
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )

                chunks = splitter.create_documents(texts, metadatas=metadatas)

                self.vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    persist_directory="./code_index"
                )

                print(f"   Indexed {len(chunks)} chunks")

            except Exception as e:
                print(f"   ⚠️  Failed to create vector index: {e}")
                self.vectorstore = None

        return {
            "status": "success",
            "files": len(self.indexed_files),
            "documents": len(documents)
        }

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search the indexed codebase"""
        if self.vectorstore is None:
            # Fallback to simple search
            return self._simple_search(query, top_k)

        try:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            return [
                {
                    "file": d.metadata.get("file", "unknown"),
                    "content": d.page_content,
                    "score": 1.0  # LangChain doesn't provide scores directly
                }
                for d in docs
            ]
        except Exception as e:
            print(f"⚠️  Search error: {e}")
            return []

    def _simple_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple keyword-based search"""
        query_terms = query.lower().split()
        results = []

        # This would search through indexed documents
        # For now return empty as we don't have documents in memory
        return []


class CodeAnalyzer:
    """Analyze code structure"""

    def __init__(self):
        self.parser = None
        if TREE_SITTER_AVAILABLE:
            try:
                self.parser = Parser()
            except Exception as e:
                print(f"⚠️  Failed to initialize parser: {e}")

    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a single code file"""
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            ext = os.path.splitext(file_path)[1].lower()
            language = SUPPORTED_EXTENSIONS.get(ext, 'text')

            analysis = {
                "file": file_path,
                "language": language,
                "lines": len(content.split('\n')),
                "size": len(content),
                "functions": self._find_functions(content, language) if TREE_SITTER_AVAILABLE else [],
                "classes": self._find_classes(content, language) if TREE_SITTER_AVAILABLE else []
            }

            return analysis

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _find_functions(self, content: str, language: str) -> List[str]:
        """Find function definitions"""
        functions = []

        # Simple regex-based detection
        import re

        if language == 'python':
            pattern = r'def\s+(\w+)\s*\('
            functions = re.findall(pattern, content)
        elif language in ('javascript', 'typescript'):
            pattern = r'function\s+(\w+)\s*\(|(\w+)\s*=\s*\('
            functions = [f[0] or f[1] for f in re.findall(pattern, content)]

        return functions[:10]  # Limit to 10

    def _find_classes(self, content: str, language: str) -> List[str]:
        """Find class definitions"""
        classes = []

        import re

        if language == 'python':
            pattern = r'class\s+(\w+)'
            classes = re.findall(pattern, content)
        elif language in ('javascript', 'typescript'):
            pattern = r'class\s+(\w+)'
            classes = re.findall(pattern, content)

        return classes[:10]


class QueryEngine:
    """Query the indexed codebase"""

    def __init__(self, index_path: str = None):
        self.indexer = CodeIndexer()
        self.analyzer = CodeAnalyzer()
        self.is_indexed = False

    def index(self, path: str) -> Dict:
        """Index a codebase"""
        result = self.indexer.index_directory(path)
        if result.get("status") == "success":
            self.is_indexed = True
        return result

    def query(self, question: str, context: List[Dict] = None) -> str:
        """Answer a question about the codebase"""
        if not self.is_indexed:
            return "⚠️  No codebase indexed. Run with --path to index first."

        # Search for relevant code
        results = self.indexer.search(question, top_k=5)

        if not results:
            return "No relevant code found. Try a different query."

        # Build context
        if context is None:
            context = results

        if not LANGCHAIN_AVAILABLE:
            return self._demo_answer(question, context)

        # Use LLM to answer
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.chains import RetrievalQA

            # Simplified: just return the context for now
            answer = f"Found {len(context)} relevant code snippets:\n\n"
            for i, r in enumerate(context[:3]):
                answer += f"{i+1}. {r.get('file', 'unknown')}\n"
                answer += f"   {r.get('content', '')[:200]}...\n\n"

            return answer

        except Exception as e:
            return f"Error generating answer: {e}"

    def _demo_answer(self, question: str, context: List[Dict]) -> str:
        """Demo answer when LLM not available"""
        answer = f"[Demo Mode]\n\nQuestion: {question}\n\n"
        answer += f"Found {len(context)} relevant code snippets:\n\n"

        for i, r in enumerate(context[:3]):
            answer += f"{i+1}. {r.get('file', 'unknown')}:\n"
            answer += f"```\n{r.get('content', '')[:300]}...\n```\n\n"

        answer += "Install langchain & openai for AI-powered answers."

        return answer


def main():
    parser = argparse.ArgumentParser(
        description='AI Code Assistant - Query your codebase',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--path', '-p', help='Path to codebase to index')
    parser.add_argument('--query', '-q', help='Query about the code')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--analyze', '-a', help='Analyze a single file')
    parser.add_argument('--list', '-l', action='store_true', help='List indexed files')

    args = parser.parse_args()

    print("🤖 AI Code Assistant")
    print("=" * 40)

    if not LANGCHAIN_AVAILABLE:
        print("⚠️  LangChain not installed. Running in limited mode.")
        print("   Install: pip install langchain openai")
        print()

    engine = QueryEngine()

    if args.analyze:
        result = engine.analyzer.analyze_file(args.analyze)
        print(json.dumps(result, indent=2))

    elif args.path:
        result = engine.index(args.path)
        print(f"✅ {result}")

        if args.query:
            answer = engine.query(args.query)
            print(f"\n{answer}")

    elif args.interactive:
        print("Interactive mode. Type 'quit' to exit.")
        print("Commands: index <path>, query <question>, list, exit")
        print()

        while True:
            cmd = input("> ")
            if cmd.lower() in ('quit', 'exit', 'q'):
                break

            if cmd.startswith('index '):
                path = cmd[6:].strip()
                result = engine.index(path)
                print(f"✅ {result}")

            elif cmd.startswith('query '):
                question = cmd[6:].strip()
                answer = engine.query(question)
                print(f"\n{answer}\n")

            elif cmd == 'list':
                print(f"Indexed {len(engine.indexer.indexed_files)} files")
                for f in engine.indexer.indexed_files[:10]:
                    print(f"  - {f}")
                if len(engine.indexer.indexed_files) > 10:
                    print(f"  ... and {len(engine.indexer.indexed_files) - 10} more")

            else:
                print("Unknown command. Use: index <path>, query <question>, list")

    elif args.query:
        if not engine.is_indexed:
            print("⚠️  No codebase indexed. Use --path first.")
        else:
            answer = engine.query(args.query)
            print(answer)

    else:
        print("Usage:")
        print("  %(prog)s --path ./my_project --query 'How does auth work?'")
        print("  %(prog)s --path ./my_project --interactive")
        print("  %(prog)s --analyze main.py")


if __name__ == '__main__':
    main()