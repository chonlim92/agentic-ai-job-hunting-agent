# Job Hunting Agent

**Author:** Chong Kiat Lim

An AI-powered career assistant that analyzes your CV against job postings and provides tailored recommendations. Built with LangChain, LangGraph, and OpenAI.

## Features

- **Two agent architectures**: ReAct (iterative reasoning) and ReWOO (plan-then-execute)
- **Chatbot-style GUI**: Multi-turn conversation with memory, follow-up questions, and session management
- **CV parsing**: Supports `.pdf`, `.docx`, and `.doc` formats
- **Job scraping**: Extracts structured details from job posting URLs via OpenAI web search
- **Dual interface**: CLI (interactive + scripted) and Gradio web UI
- **Conversation history**: View and export previous conversations
- **LangSmith tracing**: Optional observability — auto-detected from `.env`, toggle on/off in GUI and CLI

## Screenshot

![Job Hunting Agent GUI](documents/images/example_gui.jpg)

## Quick Start

### 1. Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file:

```
OPENAI_API_KEY=sk-...

# Optional: LangSmith tracing (if not provided, tracing is disabled automatically)
LANGCHAIN_API_KEY=lsv2_...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=Job Hunting Agent
```

### 3. Run

**Web UI:**
```bash
python main.py gui
```

**CLI (interactive):**
```bash
python main.py
```

**CLI (scripted):**
```bash
python main.py --mode react --cv data/cv_sample.pdf --jobs https://linkedin.com/jobs/view/123 https://linkedin.com/jobs/view/456 --langsmith
```

## Project Structure

```
├── main.py                # Entry point
├── app/
│   ├── tools.py           # CV reader & job scraper tools
│   ├── react_agent.py     # ReAct agent
│   ├── rewoo_agent.py     # ReWOO agent
│   ├── cli.py             # Command-line interface
│   └── gui.py             # Gradio chatbot web interface
├── tests/                 # Unit tests (pytest)
├── data/                  # Sample CV files
├── documents/images/      # Screenshots
├── .env                   # API keys (not committed)
└── requirements.txt
```

## Documentation

- [IMPLEMENTATION.md](documents/IMPLEMENTATION.md) — Architecture and component details
- [USAGE.md](documents/USAGE.md) — Full usage guide with examples and troubleshooting

## Tech Stack

LangChain · LangGraph · LangSmith · OpenAI GPT · Gradio · pdfplumber · python-docx · pytest
