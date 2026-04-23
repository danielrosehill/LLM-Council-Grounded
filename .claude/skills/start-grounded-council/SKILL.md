---
name: start-grounded-council
description: Launch an LLM-Council-Grounded run — six personality-based council members deliberate with retrieved context (Pinecone + Tavily). Use when the user says "run the grounded council", "deliberate on this with research backing", "/start-grounded-council", or provides a question in the LLM-Council-Grounded repo. Handles backend + frontend startup, confirms grounding configuration, and surfaces the chairman synthesis.
---

# Start a Grounded Council

You are operating inside the `LLM-Council-Grounded` repo. This skill runs a deliberation with retrieved context from Pinecone and/or Tavily.

## Preconditions

1. Repo root must contain `backend/main.py`, `main.py`, and `start.sh`.
2. Check env: `OPENROUTER_API_KEY` is required. Grounding layers are optional but have their own keys:
   - `TAVILY_API_KEY` — for web/news grounding.
   - `PINECONE_API_KEY` + index config — for knowledge-base grounding.
   If a grounding key is missing, tell the user what that disables; do not invent values.
3. `uv sync` and `cd frontend && npm install && cd ..` if dependencies are not installed.

## Step 1 — Capture the question

Ask the user for the question they want the council to deliberate on. One question per run.

Help the user judge whether grounding is actually needed:

- Pure conceptual / philosophical → no grounding needed; the planning agent will confirm.
- Factual with time-sensitive elements → Tavily useful.
- Domain-specific (against a Pinecone KB the user has configured) → Pinecone useful.

## Step 2 — Start the app

Preferred:

```bash
./start.sh
```

Or manually (two terminals):

```bash
# Terminal 1
uv run python -m backend.main
# Terminal 2
cd frontend && npm run dev
```

Then direct the user to `http://localhost:5173`.

If the user wants a headless CLI run without the frontend, check whether `main.py` supports that directly — if yes, use it; if not, tell the user the current UX is the web UI.

## Step 3 — Surface the output

The web UI shows:

- Planning agent's grounding choice (which sources were queried and why).
- Six per-personality responses with retrieved context visible.
- Peer-review rankings.
- Chairman synthesis.

If the user wants the PDF / podcast digest, trigger those from the UI, then direct them to the output paths. The `typst-council-report` skill can render a PDF from a captured council result JSON.

## Step 4 — Iterate

Offer to:

- Re-ask with different grounding scope (e.g., "force Pinecone only").
- Edit personality prompts in `backend/` if a member is drifting off their assigned style.

## Failure modes

- Missing `OPENROUTER_API_KEY` → stop.
- Frontend port collision → offer to run on an alternate port.
- Pinecone index not found → confirm the index name in config; do not auto-create indexes.

## Out of scope

This skill does not ingest or manage the Pinecone knowledge base — that is a separate operation. Use Daniel's `pinecone` MCP tools or the repo's ingestion scripts.
