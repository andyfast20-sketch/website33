"""DeepSeek streaming client with interrupt support."""
from __future__ import annotations

import asyncio
from typing import Callable

import aiohttp

from .config import settings


async def llm_stream(user_text: str, on_token: Callable[[str], None], *, stop_event: asyncio.Event) -> None:
    """Stream DeepSeek (or mock) responses token-by-token."""
    if settings.use_mock_llm or settings.deepseek_api_key is None:
        await _mock_stream(user_text, on_token, stop_event=stop_event)
        return

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": "You are a helpful voice assistant."},
            {"role": "user", "content": user_text},
        ],
        "stream": True,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers) as resp:
            async for line in resp.content:
                if stop_event.is_set():
                    break
                if not line:
                    continue
                token = line.decode(errors="ignore")
                if token.startswith("data: "):
                    token = token.replace("data: ", "", 1).strip()
                if token:
                    on_token(token)


async def _mock_stream(user_text: str, on_token: Callable[[str], None], *, stop_event: asyncio.Event) -> None:
    """Simple mock streaming generator for offline environments."""
    response = f"You said: {user_text}. How can I help next?"
    for token in response.split(" "):
        if stop_event.is_set():
            break
        on_token(token + " ")
        await asyncio.sleep(0.1)
