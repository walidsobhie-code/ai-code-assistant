#!/usr/bin/env python3
"""
AI Code Assistant - Context Loader
Index your codebase for intelligent queries
"""
import os
import json
import argparse
from typing import List, Dict, Set
from pathlib import Path

# Try imports
try:
    from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader, PythonLoader
    from langchain.vectorstores import Chroma
    from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# Supported languages and their extensions
LANGUAGE_MAP = {
    '.py': ('python', PythonLoader if LANGCHAIN_AVAILABLE else None),
    '.js': ('javascript', None),
    '.ts': ('typescript', None),
    '.jsx': ('javascript', None),
    '.tsx': ('typescript', None),
    '.java': ('java', None),
    '.go': ('go', None),
    '.rs': ('rust', None),
    '.cpp': ('cpp', None),
    '.c': ('c', None),
    '.h': ('c', None),
    '.cs': ('csharp', None),
    '.rb': ('ruby', None),
    '.php': ('php', None),
    '.swift': ('swift', None),
    '.kt': ('kotlin', None),
    '.scala': ('scala', None),
    '.r': ('r', None),
    '.sql': ('sql', None),
    '.sh': ('shell', None),
    '.bash': ('shell', None),
    '.md': ('markdown', None),
    '.json': ('json', None),
    '.yaml': ('yaml', None),
    '.yml': ('yaml', None),
    '.toml': ('toml', None),
}

# Directories to ignore
IGNORE_DIRS = {
    'node_modules', '__pycache__', '.git', '.venv', 'venv',
    'env', '.env', 'dist', 'build', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'target', 'coverage',
    '.tox', '.nox', 'vendor', 'Packages'
}

# Files to ignore
IGNORE_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.so',
    '*.dll', '*.dylib', '.gitignore', 'LICENSE', 'README*'
}


class CodeIndexer:
    """Index code for semantic search"""

    def __init__(self, root_path: str, embedding_model: str = "openai"):
        self.root_path = Path(root_path)
        self.embedding_model = embedding_model
        self.vectorstore = None
        self.indexed_files = []
        self.code_chunks = []

    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        # Check directories
        for part in path.parts:
            if part in IGNORE_DIRS:
                return True

        # Check file patterns
        for pattern in IGNORE_FILES:
            if pattern.startswith('*'):
                if path.name.endswith(pattern[1:]):
                    return True
            elif path.name == pattern:
                return True

        return False

    def scan_codebase(self) -> List[str]:
        """Scan and collect code files"""
        code_files = []

        for ext in LANGUAGE_MAP.keys():
            code_files.extend(self.root_path.rglob(f'*{ext}'))

        # Filter ignored files
        code_files = [f for f in code_files if not self.should_ignore(f)]

        return code_files

    def load_file(self, file_path: Path) -> Dict:
        """Load a code file"""
        ext = file_path.suffix

        if not LANGCHAIN_AVAILABLE:
            # Simple fallback
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return {
                    "path": str(file_path),
                    "content": content,
                    "language": LANGUAGE_MAP.get(ext, ('text', None))[0],
                    "lines": len(content.splitlines())
                }
            except Exception as e:
                return None

        # Use langchain loaders
        try:
            if ext == '.py':
                from langchain.document_loaders import PythonLoader
                loader = PythonLoader(str(file_path))
            else:
                loader = TextLoader(str(file_path), encoding='utf-8')

            docs = loader.load()
            return {
                "path": str(file_path),
                "content": docs[0].page_content,
                "language": LANGUAGE_MAP.get(ext, ('text', None))[0],
                "lines": len(docs[0].page_content.splitlines())
            }
        except Exception as e:
            print(f"⚠️  Failed to load {file_path}: {e}")
            return None

    def chunk_code(self, code_files: List[Dict]) -> List[Dict]:
        """Split code into chunks"""
        chunks = []

        if not LANGCHAIN_AVAILABLE:
            # Simple chunking
            for file in code_files:
                content = file["content"]
                # Split by paragraphs roughly
                for i in range(0, len(content), 500):
                    chunk = content[i:i+500]
                    if chunk.strip():
                        chunks.append({
                            "content": chunk,
                            "file": file["path"],
                            "language": file["language"]
                        })
            return chunks

        # Use langchain text splitters
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=500,
            chunk_overlap=50
        )

        for file in code_files:
            try:
                docs = splitter.create_documents(
                    [file["content"]],
                    metadatas=[{"file": file["path"], "language": file["language"]}]
                )
                for d in docs:
                    chunks.append({
                        "content": d.page_content,
                        "file": d.metadata.get("file", file["path"]),
                        "language": file["language"]
                    })
            except Exception as e:
                print(f"⚠️  Failed to chunk {file['path']}: {e}")

        return chunks

    def create_index(self, persist_dir: str = "./code_index"):
        """Create vector index from code"""
        print(f"🔍 Scanning: {self.root_path}")

        # Scan codebase
        code_files = self.scan_codebase()
        print(f"   Found {len(code_files)} code files")

        # Load files
        loaded_files = []
        for f in code_files:
            loaded = self.load_file(f)
            if loaded:
                loaded_files.append(loaded)

        print(f"   Loaded {len(loaded_files)} files")

        # Chunk code
        chunks = self.chunk_code(loaded_files)
        print(f"   Created {len(chunks)} chunks")

        # Create embeddings and vector store
        if LANGCHAIN_AVAILABLE:
            try:
                if self.embedding_model == "openai":
                    embeddings = OpenAIEmbeddings()
                else:
                    embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )

                texts = [c["content"] for c in chunks]
                metadatas = [{"file": c["file"], "language": c["language"]} for c in chunks]

                self.vectorstore = Chroma.from_texts(
                    texts=texts,
                    embedding=embeddings,
                    metadatas=metadatas,
                    persist_directory=persist_dir
                )

                print(f"✅ Index created at: {persist_dir}")
            except Exception as e:
                print(f"⚠️  Failed to create vector index: {e}")
                print("   Using basic search mode")
        else:
            print("⚠️  LangChain not available. Using basic search.")
            self.code_chunks = chunks

        self.indexed_files = [f["path"] for f in loaded_files]
        return {
            "files_indexed": len(self.indexed_files),
            "chunks_created": len(chunks),
            "persist_dir": persist_dir
        }

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search code index"""
        if self.vectorstore is None:
            # Basic keyword search
            return self._basic_search(query, top_k)

        try:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            return [
                {
                    "content": d.page_content,
                    "file": d.metadata.get("file", "unknown"),
                    "language": d.metadata.get("language", "text")
                }
                for d in docs
            ]
        except Exception as e:
            print(f"⚠️  Search error: {e}")
            return []

    def _basic_search(self, query: str, top_k: int) -> List[Dict]:
        """Basic keyword search fallback"""
        query_terms = query.lower().split()
        results = []

        for chunk in self.code_chunks:
            content_lower = chunk["content"].lower()
            score = sum(1 for term in query_terms if term in content_lower)
            if score > 0:
                results.append({
                    **chunk,
                    "score": score
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def main():
    parser = argparse.ArgumentParser(
        description='AI Code Assistant - Index your codebase',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--path', '-p', default='.', help='Codebase path')
    parser.add_argument('--output', '-o', default='./code_index', help='Index output directory')
    parser.add_argument('--embedding', '-e', default='openai', help='Embedding model')
    parser.add_argument('--list-files', '-l', action='store_true', help='List indexed files')

    args = parser.parse_args()

    print("🧠 AI Code Assistant - Context Loader")
    print("=" * 40)

    if not LANGCHAIN_AVAILABLE:
        print("⚠️  LangChain not installed. Running in basic mode.")
        print("   Install: pip install langchain openai")
        print()

    indexer = CodeIndexer(args.path, args.embedding)
    result = indexer.create_index(args.output)

    print(f"\n✅ Indexing complete!")
    print(f"   Files: {result['files_indexed']}")
    print(f"   Chunks: {result['chunks_created']}")

    if args.list_files:
        print(f"\n📁 Indexed files:")
        for f in indexer.indexed_files[:20]:
            print(f"   {f}")
        if len(indexer.indexed_files) > 20:
            print(f"   ... and {len(indexer.indexed_files) - 20} more")


if __name__ == '__main__':
    main()