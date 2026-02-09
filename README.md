# Context Engine

AI-powered context aggregation and agent platform for scaling consultancy work through AI agents rather than headcount.

## What This Does

1. **Captures** your patterns across Slack, GitHub, Gmail, Notion, and Cursor
2. **Learns** your communication style, code patterns, and decision-making
3. **Drafts** responses, updates, and code reviews in your voice
4. **Scales** by handling routine work with human-in-the-loop approval

## Quick Start

```bash
# Clone and setup
cd /Users/daleyarborough/Code/context-engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the API
uvicorn src.api.main:app --reload

# Start the context watcher (separate terminal)
python scripts/watch_context.py
```

## Project Structure

```
context-engine/
├── spec/           # Product specifications
├── src/
│   ├── api/        # FastAPI routes
│   ├── ingestors/  # Platform connectors
│   ├── agents/     # AI agents
│   ├── storage/    # Database & vector store
│   ├── ai/         # LLM integration
│   └── core/       # Shared utilities
├── tests/
├── scripts/        # CLI tools
├── docker/
└── k8s/
```

## Key Concepts

- **Ingestors**: Pull data from platforms (Slack, GitHub, etc.)
- **Embeddings**: Convert text to vectors for semantic search
- **RAG Pipeline**: Retrieve relevant context for AI prompts
- **Agents**: AI assistants that draft content in your style
- **Approval Flow**: Human-in-the-loop before sending anything

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Type check
mypy src
```

## License

Private - All rights reserved.
