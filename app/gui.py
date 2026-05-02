import os
import uuid
import tempfile
import gradio as gr
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

from app.react_agent import build_react_agent
from app.rewoo_agent import build_rewoo_agent, ReWOO


# Module-level agent instances (persist across calls for memory)
_react_agent = None
_rewoo_agent = None
_history_log = []  # List of (question, answer) tuples


def _langsmith_available() -> bool:
    """Check if LangSmith API key is configured in environment."""
    return bool(os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY"))


def _set_langsmith_tracing(enabled: bool):
    """Enable or disable LangSmith tracing via environment variables."""
    if enabled and _langsmith_available():
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


# Default: LangSmith tracing disabled
_set_langsmith_tracing(False)


def _get_react_agent():
    global _react_agent
    if _react_agent is None:
        _react_agent = build_react_agent()
    return _react_agent


def _get_rewoo_agent():
    global _rewoo_agent
    if _rewoo_agent is None:
        _rewoo_agent = build_rewoo_agent()
    return _rewoo_agent


def _run_react_chat(message: str, thread_id: str) -> str:
    agent = _get_react_agent()
    config = {"configurable": {"thread_id": thread_id}}
    messages = [HumanMessage(content=message)]
    result = agent.invoke(MessagesState(messages=messages), config=config)
    return result["messages"][-1].content


def _run_rewoo_chat(message: str, thread_id: str) -> str:
    agent = _get_rewoo_agent()
    config = {"configurable": {"thread_id": thread_id}}
    request = ReWOO(
        task=message,
        plan_string="",
        steps=[],
        results={},
        result=""
    )
    result = agent.invoke(request, config=config)
    return result['result']


def chat_respond(user_message, chat_history, agent_mode, cv_file, job_links_text, thread_id, langsmith_enabled):
    """Process a user message and return updated chat history."""
    _set_langsmith_tracing(langsmith_enabled)

    if not user_message.strip():
        return chat_history, ""

    # Build context from CV and job links if provided
    context_parts = []
    if cv_file is not None:
        cv_path = cv_file.name if hasattr(cv_file, 'name') else cv_file
        context_parts.append(f'My CV is located at: "{cv_path}"')

    if job_links_text and job_links_text.strip():
        links = [l.strip() for l in job_links_text.strip().split("\n") if l.strip()]
        if links:
            context_parts.append(
                "Job postings to evaluate:\n" + "\n".join(links)
            )

    # Prepend context to the first message or if user references CV/jobs
    if context_parts:
        full_message = "\n".join(context_parts) + "\n\n" + user_message
    else:
        full_message = user_message

    # Add user message to chat display
    chat_history = chat_history or []
    chat_history.append({"role": "user", "content": user_message})

    try:
        if agent_mode == "ReAct":
            response = _run_react_chat(full_message, thread_id)
        else:
            response = _run_rewoo_chat(full_message, thread_id)
    except Exception as e:
        response = f"Error: {e}"

    chat_history.append({"role": "assistant", "content": response})

    # Log to history
    _history_log.append({"question": user_message, "answer": response})

    return chat_history, ""


def get_history_display():
    """Format the history log for display."""
    if not _history_log:
        return "No previous conversations yet."

    lines = []
    for i, entry in enumerate(_history_log, 1):
        lines.append(f"### Conversation {i}")
        lines.append(f"**You:** {entry['question']}")
        lines.append(f"**Agent:** {entry['answer']}")
        lines.append("---")

    return "\n\n".join(lines)


def export_history():
    """Export all history to a downloadable file."""
    if not _history_log:
        return None

    output_path = os.path.join(tempfile.gettempdir(), "job_hunting_history.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, entry in enumerate(_history_log, 1):
            f.write(f"=== Conversation {i} ===\n")
            f.write(f"Q: {entry['question']}\n")
            f.write(f"A: {entry['answer']}\n\n")

    return output_path


def new_session():
    """Start a new chat session with a fresh thread ID."""
    return [], str(uuid.uuid4())


def launch_gui(share: bool = False):
    """Launch the Gradio web interface with chatbot-style interaction."""
    with gr.Blocks(title="Job Hunting Agent") as app:
        gr.Markdown("# 💼 Job Hunting Agent")
        gr.Markdown("Chat with an AI agent to analyze your CV against job postings. Ask follow-up questions anytime.")

        # Hidden state for thread ID (enables memory across messages)
        thread_id = gr.State(str(uuid.uuid4()))

        with gr.Tabs():
            # === Chat Tab ===
            with gr.Tab("💬 Chat"):
                with gr.Row():
                    with gr.Column(scale=1):
                        agent_mode = gr.Radio(
                            choices=["ReAct", "ReWOO"],
                            value="ReAct",
                            label="Agent Mode"
                        )
                        cv_upload = gr.File(
                            label="Upload CV (.pdf, .docx, .doc)",
                            file_types=[".pdf", ".docx", ".doc"]
                        )
                        job_links = gr.Textbox(
                            label="Job Posting URLs (one per line)",
                            placeholder="https://www.linkedin.com/jobs/view/123456\nhttps://www.linkedin.com/jobs/view/789012",
                            lines=4
                        )
                        if _langsmith_available():
                            langsmith_toggle = gr.Checkbox(
                                label="Enable LangSmith Tracing",
                                value=False
                            )
                        else:
                            langsmith_toggle = gr.State(False)
                        new_session_btn = gr.Button("🔄 New Session", variant="secondary")

                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label="Conversation",
                            height=500
                        )
                        with gr.Row():
                            msg_input = gr.Textbox(
                                label="Your message",
                                placeholder="e.g. Analyze my CV against these job postings...",
                                lines=2,
                                scale=5
                            )
                            send_btn = gr.Button("Send ➤", variant="primary", scale=1)

                # Chat submission
                send_btn.click(
                    fn=chat_respond,
                    inputs=[msg_input, chatbot, agent_mode, cv_upload, job_links, thread_id, langsmith_toggle],
                    outputs=[chatbot, msg_input]
                )
                msg_input.submit(
                    fn=chat_respond,
                    inputs=[msg_input, chatbot, agent_mode, cv_upload, job_links, thread_id, langsmith_toggle],
                    outputs=[chatbot, msg_input]
                )
                new_session_btn.click(
                    fn=new_session,
                    outputs=[chatbot, thread_id]
                )

            # === History Tab ===
            with gr.Tab("📋 History"):
                gr.Markdown("### Previous Conversations")
                history_display = gr.Markdown("No previous conversations yet.")
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                    export_btn = gr.Button("📥 Export History", variant="secondary")
                export_file = gr.File(label="Download History")

                refresh_btn.click(fn=get_history_display, outputs=[history_display])
                export_btn.click(fn=export_history, outputs=[export_file])

    app.launch(share=share, theme=gr.themes.Soft())


if __name__ == "__main__":
    launch_gui()
