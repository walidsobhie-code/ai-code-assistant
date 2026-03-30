#!/usr/bin/env python3
"""
AI Code Assistant - Gradio Web Interface
Query your codebase with natural language
"""
import os
import gradio as gr
from query_engine import QueryEngine

# Global engine
engine = None
is_indexed = False


def index_codebase(path):
    """Index a codebase"""
    global engine, is_indexed

    if not path:
        return "⚠️  Please provide a path to your codebase"

    if not os.path.exists(path):
        return f"⚠️  Path does not exist: {path}"

    try:
        engine = QueryEngine()
        result = engine.index(path)
        is_indexed = True
        return f"✅ Indexed {result.get('files', 0)} files with {result.get('documents', 0)} documents"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def ask_question(question):
    """Ask a question about the codebase"""
    global engine, is_indexed

    if not is_indexed:
        return "⚠️  Please index your codebase first using the Index tab"

    if not question:
        return ""

    try:
        answer = engine.query(question)
        return answer
    except Exception as e:
        return f"❌ Error: {str(e)}"


def analyze_file(file_path):
    """Analyze a single file"""
    global engine

    if not engine:
        return "⚠️  Initialize the engine first"

    if not file_path or not os.path.exists(file_path):
        return "⚠️  File not found"

    try:
        result = engine.analyzer.analyze_file(file_path)

        output = f"### 📊 Analysis: {result.get('file', 'Unknown')}\n\n"
        output += f"**Language:** {result.get('language', 'Unknown')}\n\n"
        output += f"**Lines:** {result.get('lines', 0)}\n\n"
        output += f"**Size:** {result.get('size', 0)} bytes\n\n"

        if result.get('functions'):
            output += "**Functions:**\n"
            for fn in result['functions'][:10]:
                output += f"- `{fn}`\n"

        if result.get('classes'):
            output += "\n**Classes:**\n"
            for cls in result['classes'][:10]:
                output += f"- `{cls}`\n"

        return output

    except Exception as e:
        return f"❌ Error: {str(e)}"


# Build Gradio Interface
with gr.Blocks(title="AI Code Assistant", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🤖 AI Code Assistant")
    gr.Markdown("Ask questions about your codebase in natural language")

    with gr.Tab("💬 Ask"):
        gr.Markdown("### Query your codebase")

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(height=400)
                msg = gr.Textbox(
                    placeholder="e.g., How does authentication work? Where is the main function?",
                    show_label=False
                )
                with gr.Row():
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")

            with gr.Column(scale=1):
                gr.Markdown("### Tips")
                gr.Markdown("""
                - Ask about specific features
                - Find where functions are defined
                - Get help understanding code
                - Ask for code improvements
                """)

        def respond(message, history):
            response = ask_question(message)
            history.append((message, response))
            return "", history

        submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        clear_btn.click(lambda: (None, []), outputs=[msg, chatbot])

    with gr.Tab("📂 Index"):
        gr.Markdown("### Index your codebase")

        with gr.Row():
            with gr.Column():
                codebase_path = gr.Textbox(
                    label="Codebase Path",
                    placeholder="./my_project"
                )
                index_btn = gr.Button("🔍 Index Codebase", variant="primary")

            with gr.Column():
                status_output = gr.Textbox(label="Status", lines=5)

        index_btn.click(
            index_codebase,
            inputs=[codebase_path],
            outputs=status_output
        )

    with gr.Tab("📊 Analyze"):
        gr.Markdown("### Analyze a single file")

        with gr.Row():
            with gr.Column():
                file_path = gr.Textbox(
                    label="File Path",
                    placeholder="./src/main.py"
                )
                analyze_btn = gr.Button("Analyze", variant="primary")

            with gr.Column():
                analysis_output = gr.Markdown()

        analyze_btn.click(
            analyze_file,
            inputs=[file_path],
            outputs=analysis_output
        )

    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## AI Code Assistant

        An AI-powered coding assistant that understands YOUR codebase:
        - 🧠 Learns your entire codebase
        - 💡 Suggests improvements
        - 🧪 Generates tests
        - 📖 Documents code
        - 🔍 Finds bugs
        - 💬 Chat in natural language

        ### Supported Languages
        Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, C#, Ruby, PHP, Swift, Kotlin, and more!
        """)

# Launch
if __name__ == "__main__":
    print("🚀 Starting AI Code Assistant Web UI...")
    print("   Open http://localhost:7861 in your browser")
    app.launch(server_name="0.0.0.0", server_port=7861)