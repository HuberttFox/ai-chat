# AI Chat
> [中文版](./README.zh.md)

A Streamlit-based AI chat application powered by DeepSeek API, featuring multi-session management, streaming output, and persistent chat history.

## Features

- 💬 **Multi-session management** — Create, load, and delete chat sessions
- ⚡ **Streaming output** — Real-time typewriter effect for AI responses
- 📝 **Custom system prompts**
- 💾 **Local JSON persistence** — Conversations auto-saved to `sessions/`
- 🧹 **Path sanitization** — Session names are sanitized to prevent path traversal
- 🛡️ **Graceful error handling** — API errors shown in UI instead of crashing

## Quick Start

### Prerequisites

- Python >= 3.13
- A DeepSeek API Key

### Installation

```bash
git clone <repo-url>
cd <repo-name>

# Virtual environment recommended
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Configuration

```bash
cp .env.example .env
# Edit .env and add your API Key:
# DEEPSEEK_API_KEY=sk-your-key-here
```

### Run

```bash
streamlit run main.py
```

Open `http://localhost:8501` in your browser.

## Project Structure

```
.
├── main.py              # Application entry point
├── pyproject.toml       # Project config & dependencies
├── .env.example         # Environment variable template
├── .gitignore
└── sessions/            # Chat history data (gitignored)
```

## Notes

- The `sessions/` directory is gitignored — local conversations won't be committed
- API Key is read from environment variable — never hardcode it or commit `.env`
