"""Test OpenAI Realtime API connection"""
import asyncio
import os
from websockets import connect

async def test():
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1"
    }
    
    print("Testing connection to OpenAI Realtime API...")
    print(f"URL: {url}")
    
    ws = await asyncio.wait_for(connect(url, additional_headers=headers), timeout=10.0)
    print("Connected OK!")
    await ws.close()

if __name__ == "__main__":
    asyncio.run(test())
