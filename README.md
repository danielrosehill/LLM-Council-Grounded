# LLM Council Template

A template for running multi-perspective LLM deliberations using personality-based system prompting. Based on [karpathy/llm-council](https://github.com/karpathy/llm-council), modified to use a single LLM with different "thinking personalities" rather than multiple model providers.

## How It Works

Instead of querying different LLM providers, this template defines six council members differentiated by system prompts:

| Member | Thinking Style |
|--------|---------------|
| Logical Thinker | Analytical, structured, evidence-based reasoning |
| Creative Problem Solver | Lateral thinking, unexpected analogies, novel angles |
| Pessimist | Risk identification, failure modes, worst-case scenarios |
| Optimist | Opportunity focus, best-case scenarios, momentum building |
| Connecting The Dots Specialist | Pattern recognition, systems thinking, second-order effects |
| Unconventional Solutions Ideator | Contrarian thinking, first-principles, radical simplification |

The deliberation follows three stages:

1. **Stage 1: Individual Perspectives** -- Each personality responds to the query independently
2. **Stage 2: Peer Review** -- Each personality evaluates and ranks the anonymized responses
3. **Stage 3: Chairman Synthesis** -- A chairman role synthesizes all perspectives into a final answer

## Digest Outputs

After deliberation, you can generate two digest formats:

- **PDF Report** -- A formatted Typst document with all stages, rankings, and the final synthesis
- **Personal Podcast** -- An LLM-written podcast script converted to audio via Microsoft Edge TTS, delivered as a personal briefing addressed to you

## Setup

### 1. Install Dependencies

Requires [uv](https://docs.astral.sh/uv/) for Python and Node.js for the frontend.

```bash
uv sync
cd frontend && npm install && cd ..
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Get your API key at [openrouter.ai](https://openrouter.ai/).

### 3. Configure Model (Optional)

Set the base model and chairman model via environment variables in `.env`:

```bash
COUNCIL_MODEL=anthropic/claude-sonnet-4.5
CHAIRMAN_MODEL=anthropic/claude-sonnet-4.5
```

Or edit `backend/config.py` to customize the council personalities.

### 4. Optional: Install Typst and Edge TTS

For PDF report generation:
```bash
# Install Typst (see https://github.com/typst/typst)
cargo install typst-cli
# or via package manager
```

For podcast audio generation:
```bash
pip install edge-tts
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
- **Frontend:** React + Vite, react-markdown
- **PDF Generation:** Typst
- **Audio Generation:** Microsoft Edge TTS (edge-tts)
- **Storage:** JSON files in `data/conversations/`

## Attribution

Based on [karpathy/llm-council](https://github.com/karpathy/llm-council) by Andrej Karpathy.
