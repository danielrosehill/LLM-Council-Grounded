"""
Grounding layer for council deliberations.

Two sources:
  - Pinecone: knowledge-base retrieval (always used if configured)
  - Tavily: real-time web/news search (used when the planning agent decides the
    query needs current information)

A lightweight planning agent (single LLM call via OpenRouter) inspects the user
query and decides whether Tavily should be invoked and, if so, what search query
to use.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional

from .config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_NAMESPACE, GROUNDING_TOP_K,
    TAVILY_API_KEY, TAVILY_MAX_RESULTS,
    COUNCIL_MODEL,
)

# ---------------------------------------------------------------------------
# Pinecone
# ---------------------------------------------------------------------------

_pc = None
_index = None


def _get_pinecone_index():
    global _pc, _index
    if _index is None:
        from pinecone import Pinecone
        if not PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not set")
        if not PINECONE_INDEX_NAME:
            raise RuntimeError("PINECONE_INDEX_NAME is not set")
        _pc = Pinecone(api_key=PINECONE_API_KEY)
        _index = _pc.Index(PINECONE_INDEX_NAME)
    return _index


def is_pinecone_enabled() -> bool:
    return bool(PINECONE_API_KEY and PINECONE_INDEX_NAME)


def is_tavily_enabled() -> bool:
    return bool(TAVILY_API_KEY)


def is_grounding_enabled() -> bool:
    """At least one grounding source is configured."""
    return is_pinecone_enabled() or is_tavily_enabled()


async def retrieve_pinecone_context(query: str) -> List[Dict[str, Any]]:
    """Query Pinecone for relevant knowledge-base chunks."""
    if not is_pinecone_enabled():
        return []

    def _search():
        index = _get_pinecone_index()
        return index.search(
            namespace=PINECONE_NAMESPACE or "",
            query={"top_k": GROUNDING_TOP_K, "inputs": {"text": query}},
        )

    results = await asyncio.to_thread(_search)

    chunks = []
    for hit in results.get("result", {}).get("hits", []):
        fields = hit.get("fields", {})
        text = (
            fields.get("text")
            or fields.get("chunk_text")
            or fields.get("content")
            or ""
        )
        if not text:
            for v in fields.values():
                if isinstance(v, str) and len(v) > 20:
                    text = v
                    break
        if text:
            chunks.append({
                "text": text,
                "score": hit.get("_score", 0),
                "source": fields.get("source") or fields.get("title") or fields.get("url") or "",
            })
    return chunks


# ---------------------------------------------------------------------------
# Tavily
# ---------------------------------------------------------------------------

async def retrieve_tavily_context(
    search_query: str,
    topic: str = "general",
) -> List[Dict[str, Any]]:
    """Run a Tavily web search and return result chunks."""
    if not is_tavily_enabled():
        return []

    from tavily import TavilyClient

    def _search():
        client = TavilyClient(api_key=TAVILY_API_KEY)
        return client.search(
            query=search_query,
            max_results=TAVILY_MAX_RESULTS,
            topic=topic,
            include_answer=False,
        )

    results = await asyncio.to_thread(_search)

    chunks = []
    for result in results.get("results", []):
        text = result.get("content", "")
        if text:
            chunks.append({
                "text": text,
                "score": result.get("score", 0),
                "source": result.get("url", ""),
                "title": result.get("title", ""),
            })
    return chunks


# ---------------------------------------------------------------------------
# Planning agent
# ---------------------------------------------------------------------------

async def plan_grounding(user_query: str) -> Dict[str, Any]:
    """
    Lightweight planning agent that decides which grounding sources to use.

    Returns a dict like:
      {
        "use_pinecone": true,
        "use_tavily": true,
        "tavily_query": "latest AI regulation news 2026",
        "tavily_topic": "news",
        "reasoning": "The question asks about recent policy..."
      }
    """
    from .openrouter import query_model

    available_sources = []
    if is_pinecone_enabled():
        available_sources.append("pinecone (knowledge base / document store)")
    if is_tavily_enabled():
        available_sources.append("tavily (real-time web & news search)")

    if not available_sources:
        return {"use_pinecone": False, "use_tavily": False, "reasoning": "No sources configured"}

    sources_list = "\n".join(f"- {s}" for s in available_sources)

    planning_prompt = f"""You are a grounding planner for an LLM council deliberation system.
Your job is to decide which external information sources should be queried to help
the council answer the user's question with factual grounding.

Available sources:
{sources_list}

Guidelines:
- Use pinecone for questions that benefit from stored domain knowledge or documents.
- Use tavily when the question involves recent events, current affairs, breaking news,
  up-to-date statistics, or anything where timeliness matters.
- You can use both, one, or neither.
- If using tavily, craft a focused search query (different from the user's question
  if needed) and pick a topic: "general" or "news".

User question: {user_query}

Respond with ONLY valid JSON (no markdown, no explanation outside the JSON):
{{
  "use_pinecone": true/false,
  "use_tavily": true/false,
  "tavily_query": "search query if use_tavily is true, else empty string",
  "tavily_topic": "general" or "news",
  "reasoning": "one sentence explaining your decision"
}}"""

    messages = [{"role": "user", "content": planning_prompt}]
    response = await query_model(COUNCIL_MODEL, messages, timeout=30.0)

    if response is None:
        # Fallback: use whatever is available
        return {
            "use_pinecone": is_pinecone_enabled(),
            "use_tavily": False,
            "tavily_query": "",
            "tavily_topic": "general",
            "reasoning": "Planning agent failed; defaulting to knowledge base only",
        }

    content = response.get("content", "").strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        plan = json.loads(content)
    except json.JSONDecodeError:
        return {
            "use_pinecone": is_pinecone_enabled(),
            "use_tavily": False,
            "tavily_query": "",
            "tavily_topic": "general",
            "reasoning": "Could not parse planning response; defaulting to knowledge base only",
        }

    # Enforce availability constraints
    if not is_pinecone_enabled():
        plan["use_pinecone"] = False
    if not is_tavily_enabled():
        plan["use_tavily"] = False

    return plan


# ---------------------------------------------------------------------------
# Unified retrieval
# ---------------------------------------------------------------------------

async def retrieve_context(user_query: str) -> Dict[str, Any]:
    """
    Run the full grounding pipeline:
      1. Planning agent decides sources
      2. Retrieve from selected sources in parallel
      3. Return structured result

    Returns:
      {
        "plan": { ... planning agent output ... },
        "pinecone": [ ... chunks ... ],
        "tavily": [ ... chunks ... ],
      }
    """
    if not is_grounding_enabled():
        return {"plan": {}, "pinecone": [], "tavily": []}

    plan = await plan_grounding(user_query)

    tasks = {}
    if plan.get("use_pinecone"):
        tasks["pinecone"] = retrieve_pinecone_context(user_query)
    if plan.get("use_tavily") and plan.get("tavily_query"):
        tasks["tavily"] = retrieve_tavily_context(
            plan["tavily_query"],
            topic=plan.get("tavily_topic", "general"),
        )

    results = {"pinecone": [], "tavily": []}
    if tasks:
        gathered = await asyncio.gather(*tasks.values())
        for key, result in zip(tasks.keys(), gathered):
            results[key] = result

    return {"plan": plan, **results}


def format_context_for_prompt(grounding_result: Dict[str, Any]) -> str:
    """
    Format the combined grounding results into a prompt-injection string.
    Returns empty string if no context was retrieved.
    """
    pinecone_chunks = grounding_result.get("pinecone", [])
    tavily_chunks = grounding_result.get("tavily", [])

    if not pinecone_chunks and not tavily_chunks:
        return ""

    parts = []

    if pinecone_chunks:
        parts.append("KNOWLEDGE BASE CONTEXT:")
        for i, chunk in enumerate(pinecone_chunks, 1):
            source = chunk.get("source", "")
            source_line = f" [Source: {source}]" if source else ""
            parts.append(f"\n--- KB {i}{source_line} ---\n{chunk['text']}")

    if tavily_chunks:
        parts.append("\nWEB / NEWS CONTEXT (recent):")
        for i, chunk in enumerate(tavily_chunks, 1):
            title = chunk.get("title", "")
            source = chunk.get("source", "")
            header = ""
            if title:
                header += f" [{title}]"
            if source:
                header += f" ({source})"
            parts.append(f"\n--- Web {i}{header} ---\n{chunk['text']}")

    parts.append("\n--- End of grounding context ---")
    return "\n".join(parts)
