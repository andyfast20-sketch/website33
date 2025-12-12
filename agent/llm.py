"""OpenAI streaming client - fast responses."""
from __future__ import annotations

import asyncio
import json
from typing import Callable

import aiohttp

from .config import settings


async def llm_stream(user_text: str, on_token: Callable[[str], None], *, stop_event: asyncio.Event) -> None:
    if settings.use_mock_llm:
        await _mock_stream(user_text, on_token, stop_event=stop_event)
        return

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a voice assistant. Be brief - respond in 1 short sentence."},
            {"role": "user", "content": user_text},
        ],
        "stream": True,
        "max_tokens": 30,
        "temperature": 0.7,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
                async for line in resp.content:
                    if stop_event.is_set():
                        break
                    line_text = line.decode("utf-8").strip()
                    if not line_text.startswith("data: "):
                        continue
                    json_str = line_text[6:]
                    if json_str == "[DONE]":
                        break
                    try:
                        data = json.loads(json_str)
                        content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            on_token(content)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"[LLM] Error: {e}")
        await _mock_stream(user_text, on_token, stop_event=stop_event)


async def _mock_stream(user_text: str, on_token: Callable[[str], None], *, stop_event: asyncio.Event) -> None:
    response = f"I heard: {user_text}. How can I help?"
    for word in response.split(" "):
        if stop_event.is_set():
            break
        on_token(word + " ")
        await asyncio.sleep(0.05)
