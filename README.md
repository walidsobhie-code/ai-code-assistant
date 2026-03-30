# AI Code Assistant 🤖💻

AI-powered coding assistant that understands YOUR codebase. Get answers, generate tests, refactor code.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

## Why This?

Every developer needs an AI that knows their specific codebase, not just general coding.

## ✨ Features

- 🧠 **Code Understanding** - Learns your entire codebase
- 💡 **Suggest Improvements** - Code review and optimization
- 🧪 **Generate Tests** - Auto-create unit tests
- 📖 **Document Code** - Auto-generate docs
- 🔍 **Find Bugs** - Identify issues
- 💬 **Chat** - Ask questions in natural language
- 🌐 **Web UI** - Beautiful Gradio interface
- 🐳 **Docker Ready** - Deploy anywhere

## 🚀 Quick Start

```bash
pip install -r requirements.txt

# Index your codebase
python context_loader.py --path ./your_project

# Ask questions
python query_engine.py "How does authentication work?"

# Or use Web UI
python gradio_app.py
# Open http://localhost:7861
```

## 🐳 Docker

```bash
docker build -t ai-code-assistant .
docker run -p 7861:7861 -e OPENAI_API_KEY=your-key ai-code-assistant
```

## 📝 License

MIT License

## ⭐ Star if helpful!