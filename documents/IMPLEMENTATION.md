# Implementation Guide

**Author:** Chong Kiat Lim

## Architecture Overview

The Job Hunting Agent is a modular Python application that leverages LangChain, LangGraph, and OpenAI to analyze CVs against job postings. It supports two agent architectures (ReAct and ReWOO) and two interfaces (CLI and GUI).

## Project Structure

```
agentic-ai-job-hunting-agent/
├── main.py                  # Entry point (CLI / GUI dispatcher)
├── app/
│   ├── __init__.py
│   ├── tools.py             # Shared tools (CV reader, job scraper)
│   ├── react_agent.py       # ReAct agent (LangGraph + ToolNode)
│   ├── rewoo_agent.py       # ReWOO agent (Planner → Executor → Solver)
│   ├── cli.py               # Command-line interface
│   └── gui.py               # Gradio chatbot web interface
├── tests/
│   ├── __init__.py
│   ├── test_tools.py        # Unit tests for tools
│   ├── test_react_agent.py  # Unit tests for ReAct agent
│   └── test_rewoo_agent.py  # Unit tests for ReWOO agent
├── data/
│   └── cv_sample.pdf        # Sample CV for testing
├── documents/images/
│   └── example_gui.jpg      # GUI screenshot
├── .env                     # API keys (not committed)
├── requirements.txt         # Python dependencies
├── JobHuntingAgent_ReAct.ipynb   # ReAct notebook (reference)
└── JobHuntingAgent_ReWoo.ipynb   # ReWOO notebook (reference)
```

## Component Details

### 1. Shared Tools (`app/tools.py`)

Two LangChain `@tool`-decorated functions shared by both agents:

- **`extract_cv_text(file_path)`** — Reads CV content from `.pdf`, `.docx`, or `.doc` files using `pdfplumber` and `python-docx`. For `.doc` files, it uses LibreOffice headless conversion.
- **`job_posting_scraper(job_link)`** — Uses OpenAI's `gpt-4o-search-preview` model with web search to visit and extract structured details from a job posting URL.

### 2. ReAct Agent (`app/react_agent.py`)

Implements the **Reasoning + Acting** pattern:

![ReAct Agent Graph](images/graph_react.png)

- **Graph**: `START → assistant → tools_condition → tools → assistant → END`
- The LLM decides which tool to call at each step, observes the result, and reasons about the next action.
- Uses `MessagesState` for conversational context.
- Includes `InMemorySaver` for thread-based memory persistence.

### 3. ReWOO Agent (`app/rewoo_agent.py`)

Implements the **Reasoning Without Observation** pattern:

![ReWOO Agent Graph](images/graph_rewoo.png)

- **Graph**: `START → planner → executor → router(executor|solver) → END`
- **Planner**: Generates a full plan upfront with `#E1`, `#E2`, etc. evidence variables.
- **Executor**: Executes each step sequentially, calling the appropriate tool.
- **Solver**: Synthesizes all gathered evidence into a final answer.
- Uses regex parsing (`Plan:\s*(.+?)\s*(#E\d+)\s*=\s*(\w+)\[(.+?)\]`) to extract structured steps from the planner output.

### 4. CLI (`app/cli.py`)

Two modes:
- **Interactive**: Prompts the user for agent mode, LangSmith tracing (if API key available), CV path, and job links step by step.
- **Argument-based**: Accepts `--mode`, `--cv`, `--jobs`, `--output`, and `--langsmith` flags for scripted usage.

### 5. GUI (`app/gui.py`)

Built with **Gradio** as a chatbot-style interface:

![Job Hunting Agent GUI](documents/images/example_gui.jpg)

**Chat Tab:**
- Multi-turn conversational interface with message history
- Agent mode selection (ReAct / ReWOO)
- File upload for CV
- Multi-line text input for job posting URLs
- LangSmith tracing toggle (only shown if API key is configured in `.env`)
- Follow-up questions with memory persistence within a session
- "New Session" button to start fresh with a new thread ID

**History Tab:**
- Displays all previous Q&A pairs from the current app session
- Refresh and export functionality
- Downloadable history as a text file

### 6. Entry Point (`main.py`)

Dispatches to the correct interface:
- `python main.py` → Interactive CLI
- `python main.py --mode react --cv ... --jobs ...` → Argument-based CLI
- `python main.py gui` → Gradio chatbot UI
- `python main.py gui --share` → Gradio with public sharing link

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `langchain`, `langchain-openai` | LLM integration and tool framework |
| `langgraph` | Agent graph orchestration |
| `langsmith` | Tracing and observability |
| `openai` | Direct OpenAI API (web search tool) |
| `gradio` | Chatbot web UI |
| `pdfplumber` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `python-dotenv` | Environment variable management |
| `pytest` | Unit testing |

## Environment Variables

Required in `.env`:

```
OPENAI_API_KEY=sk-...
```

Optional (enables LangSmith tracing toggle in GUI/CLI):

```
LANGCHAIN_API_KEY=lsv2_...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=Job Hunting Agent
```

> **Note:** If `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY` is not set, tracing is automatically disabled and the toggle is hidden from the GUI.
