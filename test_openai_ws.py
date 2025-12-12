"""Test OpenAI Realtime API connection"""
import asyncio
from websockets import connect

async def test():
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
    headers = {
        "Authorization": "Bearer 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",
        "OpenAI-Beta": "realtime=v1"
    }
    
    print("Testing connection to OpenAI Realtime API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    ws = await asyncio.wait_for(connect(url, additional_headers=headers), timeout=10.0)
    print("Connected OK!")
    await ws.close()

if __name__ == "__main__":
    asyncio.run(test())
