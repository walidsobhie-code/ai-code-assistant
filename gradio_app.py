import gradio as gr
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder"

def query_code(question: str) -> str:
    prompt = f"""You are a code assistant. Answer this question about code:

Question: {question}

Provide a helpful answer."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "No answer")
    except Exception as e:
        return f"Error: {e}"
    return "Ollama not running"

def ask(q, history):
    answer = query_code(q)
    history.append((q, answer))
    return "", history

with gr.Blocks(title="💻 AI Code Assistant") as demo:
    gr.Markdown("# 💻 AI Code Assistant\n### Ask about YOUR code")
    chatbot = gr.Chatbot(height=500)
    question = gr.Textbox(label="Ask", placeholder="How does auth work?")
    ask_btn = gr.Button("💬 Ask", variant="primary")
    question.submit(lambda q, h: ask(q, h), [question, chatbot], [question, chatbot])
    ask_btn.click(lambda q, h: ask(q, h), [question, chatbot], [question, chatbot])

demo.launch(server_name="0.0.0.0", server_port=7863)
