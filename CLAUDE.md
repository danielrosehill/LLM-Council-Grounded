# CLAUDE.md -- LLM Council (Grounded)

## What This Is

A personality-based LLM council deliberation system with grounded context retrieval. Instead of querying different LLMs (like the original karpathy/llm-council), this uses a single model with six system-prompt-defined personalities that deliberate in three stages -- preceded by a grounding step that retrieves factual context from Pinecone (knowledge base) and/or Tavily (real-time web/news).

## Architecture

- `backend/config.py` -- Model config + personality definitions + grounding config
- `backend/grounding.py` -- Planning agent + Pinecone/Tavily retrieval layer
- `backend/council.py` -- 3-stage orchestration (collect, rank, synthesize)
- `backend/openrouter.py` -- OpenRouter API client with personality-parallel querying
- `backend/digest.py` -- PDF (Typst) and podcast (Edge TTS) generation
- `backend/storage.py` -- JSON file storage for conversations
- `backend/main.py` -- FastAPI endpoints
- `frontend/` -- React + Vite UI with grounding panel, stage tabs, and digest panel

## Grounding Pipeline

The grounding layer runs before Stage 1:

1. **Planning agent** -- a lightweight LLM call that analyzes the user query and decides which sources to use (Pinecone, Tavily, both, or neither). For Tavily it also crafts a focused search query and picks a topic (general/news).
2. **Parallel retrieval** -- selected sources are queried concurrently.
3. **Context injection** -- retrieved chunks are formatted and prepended to the user query for all Stage 1 personality prompts.

Sources:
- **Pinecone**: domain knowledge / document store (always used if configured)
- **Tavily**: real-time web and news search (used when planning agent determines timeliness matters)

## Key Design Decisions

- Single model, multiple personalities via system prompts (not multi-provider)
- Personalities: Logical Thinker, Creative Solver, Pessimist, Optimist, Connector, Unconventional
- Stage 2 uses anonymous labels (Response A, B, C) to prevent bias
- Grounding is optional -- system works without Pinecone/Tavily keys configured
- Planning agent prevents unnecessary web searches for static/conceptual questions
- Digest outputs: Typst PDF report + Edge TTS podcast audio
- Backend port 8001, frontend port 5173

## Running

```bash
./start.sh
# or: uv run python -m backend.main & cd frontend && npm run dev
```

## Environment Variables

Required:
- `OPENROUTER_API_KEY` -- OpenRouter API key

Optional (grounding):
- `PINECONE_API_KEY` -- Pinecone API key
- `PINECONE_INDEX_NAME` -- Pinecone index name (must be an integrated index with inference)
- `PINECONE_NAMESPACE` -- Pinecone namespace (default: empty)
- `GROUNDING_TOP_K` -- Number of Pinecone results (default: 5)
- `TAVILY_API_KEY` -- Tavily API key for web/news search
- `TAVILY_MAX_RESULTS` -- Number of Tavily results (default: 5)
