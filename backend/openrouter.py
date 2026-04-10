"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "anthropic/claude-sonnet-4.5")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_personalities_parallel(
    model: str,
    personalities: List[Dict[str, str]],
    user_messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query the same model with different personality system prompts in parallel.

    Args:
        model: OpenRouter model identifier
        personalities: List of personality dicts with 'id', 'name', 'system_prompt'
        user_messages: List of user message dicts to send to each personality

    Returns:
        Dict mapping personality id to response dict (or None if failed)
    """
    import asyncio

    async def query_with_personality(personality):
        messages = [
            {"role": "system", "content": personality["system_prompt"]},
            *user_messages
        ]
        return await query_model(model, messages)

    tasks = [query_with_personality(p) for p in personalities]
    responses = await asyncio.gather(*tasks)

    return {p["id"]: response for p, response in zip(personalities, responses)}
