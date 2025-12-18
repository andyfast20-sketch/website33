"""Test Deepgram async WebSocket connection"""
import asyncio
import os
from deepgram import DeepgramClient

async def test_connection():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPGRAM_API_KEY env var")

    client = DeepgramClient(api_key=api_key)
    
    print("Client attributes:", [attr for attr in dir(client.listen) if not attr.startswith('_')])
    
    # Try to access async methods
    print("\nTrying different connection methods...")
    
    # Check if there's an async version
    if hasattr(client.listen, 'asyncwebsocket'):
        print("✅ Found asyncwebsocket")
    elif hasattr(client.listen, 'websocket'):
        print("✅ Found websocket")  
    elif hasattr(client.listen, 'asynclive'):
        print("✅ Found asynclive")
    elif hasattr(client.listen, 'live'):
        print("✅ Found live")
    
    # Check v1
    print("\nV1 attributes:", [attr for attr in dir(client.listen.v1) if not attr.startswith('_')])

asyncio.run(test_connection())
