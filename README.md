# LLM Council -- Grounded

A grounded variant of the personality-based LLM council deliberation system. Based on [karpathy/llm-council](https://github.com/karpathy/llm-council), with two layers of differentiation from the original formulation.

## Differentiation from Baseline

### vs. karpathy/llm-council (original)

The original llm-council queries **multiple different LLM providers** (GPT-4, Claude, Gemini, etc.) and compares their outputs. This template instead uses a **single model with six personality-based system prompts**, so the deliberation is between different *thinking styles* rather than different models. This isolates the effect of perspective from the effect of model capability.

### vs. the ungrounded personality council

The base personality council template deliberates purely from the LLM's training data. This **grounded** variant adds a **context retrieval layer** that runs before the council sees the question:

| Feature | Ungrounded | Grounded (this repo) |
|---------|-----------|----------------------|
| Knowledge source | LLM training data only | Training data + retrieved context |
| Planning agent | None | Analyzes query to decide which sources to use |
| Pinecone integration | None | Vector search over a knowledge base |
| Tavily integration | None | Real-time web and news search |
| Context injection | None | Retrieved chunks prepended to all Stage 1 prompts |

The planning agent is a lightweight LLM call that inspects the user's question and decides:
- Whether to query **Pinecone** (domain knowledge / document store)
- Whether to query **Tavily** (real-time web/news) and, if so, what search query and topic to use
- Or whether the question is purely conceptual and needs no external grounding

This means the council members deliberate with factual grounding from authoritative sources rather than relying solely on parametric knowledge.

## How It Works

Six council members are defined by system prompts:

| Member | Thinking Style |
|--------|---------------|
| Logical Thinker | Analytical, structured, evidence-based reasoning |
| Creative Problem Solver | Lateral thinking, unexpected analogies, novel angles |
| Pessimist | Risk identification, failure modes, worst-case scenarios |
| Optimist | Opportunity focus, best-case scenarios, momentum building |
| Connecting The Dots Specialist | Pattern recognition, systems thinking, second-order effects |
| Unconventional Solutions Ideator | Contrarian thinking, first-principles, radical simplification |

The deliberation follows four phases:

1. **Grounding** -- Planning agent decides sources; Pinecone and/or Tavily are queried in parallel
2. **Stage 1: Individual Perspectives** -- Each personality responds to the query with retrieved context injected
3. **Stage 2: Peer Review** -- Each personality evaluates and ranks the anonymized responses
4. **Stage 3: Chairman Synthesis** -- A chairman role synthesizes all perspectives into a final answer

## Digest Outputs

After deliberation, you can generate two digest formats:

- **PDF Report** -- A formatted Typst document with all stages, rankings, and the final synthesis
- **Personal Podcast** -- An LLM-written podcast script converted to audio via Microsoft Edge TTS

## Setup

### 1. Install Dependencies

Requires [uv](https://docs.astral.sh/uv/) for Python and Node.js for the frontend.

```bash
uv sync
cd frontend && npm install && cd ..
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Optional: grounding via Pinecone (knowledge base)
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=my-index
PINECONE_NAMESPACE=
GROUNDING_TOP_K=5

# Optional: grounding via Tavily (web/news search)
TAVILY_API_KEY=tvly-...
TAVILY_MAX_RESULTS=5

# Optional: model selection
COUNCIL_MODEL=anthropic/claude-sonnet-4.5
CHAIRMAN_MODEL=anthropic/claude-sonnet-4.5
```

The system works without any grounding keys -- it gracefully degrades to ungrounded deliberation. Configure one or both grounding sources as needed.

### 3. Optional: Install Typst

For PDF report generation:
```bash
cargo install typst-cli
```

## Running

```bash
./start.sh
```

Or manually:

```bash
# Terminal 1 - Backend
uv run python -m backend.main

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Open http://localhost:5173 in your browser.

## Tech Stack

- **Backend:** FastAPI, async httpx, OpenRouter API
- **Grounding:** Pinecone (vector search), Tavily (web/news), planning agent (LLM)
- **Frontend:** React + Vite, react-markdown
- **PDF Generation:** Typst
- **Audio Generation:** Microsoft Edge TTS (edge-tts)
- **Storage:** JSON files in `data/conversations/`

## Attribution

Based on [karpathy/llm-council](https://github.com/karpathy/llm-council) by Andrej Karpathy.
