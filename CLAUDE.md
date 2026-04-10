# CLAUDE.md -- LLM Council Template

## What This Is

A personality-based LLM council deliberation system. Instead of querying different LLMs (like the original karpathy/llm-council), this uses a single model with six system-prompt-defined personalities that deliberate in three stages.

## Architecture

- `backend/config.py` -- Model config + personality definitions (system prompts)
- `backend/council.py` -- 3-stage orchestration (collect, rank, synthesize)
- `backend/openrouter.py` -- OpenRouter API client with personality-parallel querying
- `backend/digest.py` -- PDF (Typst) and podcast (Edge TTS) generation
- `backend/storage.py` -- JSON file storage for conversations
- `backend/main.py` -- FastAPI endpoints
- `frontend/` -- React + Vite UI with stage tabs and digest panel

## Key Design Decisions

- Single model, multiple personalities via system prompts (not multi-provider)
- Personalities: Logical Thinker, Creative Solver, Pessimist, Optimist, Connector, Unconventional
- Stage 2 uses anonymous labels (Response A, B, C) to prevent bias
- Digest outputs: Typst PDF report + Edge TTS podcast audio
- Backend port 8001, frontend port 5173

## Running

```bash
./start.sh
# or: uv run python -m backend.main & cd frontend && npm run dev
```

Requires `.env` with `OPENROUTER_API_KEY`.
