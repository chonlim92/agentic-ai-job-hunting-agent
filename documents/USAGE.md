# Usage Guide

**Author:** Chong Kiat Lim

## Prerequisites

1. **Python 3.11+** installed
2. Virtual environment activated with dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` file configured with your API keys (see [IMPLEMENTATION.md](IMPLEMENTATION.md#environment-variables))

## Quick Start

### GUI Mode (Recommended)

Launch the chatbot-style web interface:

```bash
python main.py gui
```

This opens a Gradio app in your browser at `http://localhost:7860`.

![Job Hunting Agent GUI](documents/images/example_gui.jpg)

**Steps:**
1. Select **ReAct** or **ReWOO** agent mode in the left sidebar.
2. Upload your CV file (`.pdf`, `.docx`, or `.doc`).
3. Paste one or more job posting URLs (one per line).
4. Type your question in the chat input (e.g., "Analyze my CV against these job postings").
5. Click **Send** or press Enter.
6. Ask follow-up questions — the agent retains memory within the session.
7. Click **New Session** to start fresh with a new conversation thread.

**History Tab:**
- Switch to the **History** tab to view all previous Q&A pairs.
- Click **Refresh** to update the display.
- Click **Export History** to download all conversations as a text file.

To share the GUI publicly (e.g., for demo):
```bash
python main.py gui --share
```

### CLI Mode — Interactive

Run without arguments for a guided experience:

```bash
python main.py
```

You will be prompted to:
1. Choose agent mode (ReAct or ReWOO)
2. Enable/disable LangSmith tracing (only if API key is in `.env`)
3. Enter your CV file path
4. Enter job posting URLs (one per line, empty line to finish)
5. Optionally save the result to a file

### CLI Mode — With Arguments

For scripted or automated usage:

```bash
python main.py --mode react --cv data/cv_sample.pdf --jobs https://www.linkedin.com/jobs/view/4402161329 https://www.linkedin.com/jobs/view/4409462037
```

**Arguments:**

| Flag | Required | Description |
|------|----------|-------------|
| `--mode` | Yes | Agent mode: `react` or `rewoo` |
| `--cv` | Yes | Path to CV file |
| `--jobs` | Yes | One or more job posting URLs (space-separated) |
| `--output` | No | Save result to this file path |
| `--langsmith` | No | Enable LangSmith tracing (requires API key in `.env`) |

**Example with output file:**

```bash
python main.py --mode rewoo --cv data/cv_sample.pdf --jobs https://www.linkedin.com/jobs/view/4402161329 --output analysis.txt
```

## Agent Modes

### ReAct (Reasoning + Acting)
- The agent reasons step-by-step, deciding which tool to call at each turn.
- Better for **exploratory tasks** where the agent needs to adapt based on intermediate results.
- Supports multi-turn conversations with memory.

### ReWOO (Reasoning Without Observation)
- The agent creates a full plan upfront, then executes all steps sequentially.
- More **efficient** (fewer LLM calls) for well-defined tasks.
- Better for batch processing multiple job links.

## Examples

### Analyze CV against multiple jobs (CLI):
```bash
python main.py --mode react \
  --cv data/cv_sample.pdf \
  --jobs https://www.linkedin.com/jobs/view/4402161329 \
        https://www.linkedin.com/jobs/view/4409462037 \
        https://www.linkedin.com/jobs/view/4343051642 \
  --output result.txt
```

### Launch GUI:
```bash
python main.py gui
```

### Follow-up questions in GUI:
After the initial analysis, you can ask follow-up questions like:
- "Which job is the best fit for me?"
- "What specific skills should I add to my CV?"
- "Can you rewrite my summary section for the first job?"

The agent remembers the previous context within the same session.

## Running Tests

```bash
pytest tests/ -v
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `APIConnectionError: Connection error` | Check your internet connection and ensure `OPENAI_API_KEY` is valid |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in your activated venv |
| `File not found` for CV | Use an absolute path or ensure the file is relative to where you run the command |
| LangSmith traces not showing | Ensure `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` are set in `.env` |
| `TypeError: Chatbot.__init__()` | Ensure Gradio 6.x is installed (`pip install --upgrade gradio`) |
