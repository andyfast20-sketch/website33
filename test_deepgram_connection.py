"""Test correct Deepgram connection usage"""
import asyncio
import os
from deepgram import DeepgramClient
from deepgram.core.events import EventType

async def test_economy_mode():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPGRAM_API_KEY env var")

    client = DeepgramClient(api_key=api_key)
    
    print("Testing Deepgram connection...")
    
    # Try using connect() without context manager
    try:
        connection = client.listen.v1.connect(
            model="nova-2",
            encoding="linear16",
            sample_rate=16000,
        )
        print(f"Connection type: {type(connection)}")
        print(f"Connection attributes: {[attr for attr in dir(connection) if not attr.startswith('_')]}")
        
        # Check if it has __enter__ and __exit__ (context manager)
        if hasattr(connection, '__enter__'):
            print("✅ This is a context manager - needs 'with' statement")
        
        # Try to use it
        connection.on(EventType.OPEN, lambda: print("Opened!"))
        connection.start_listening()
        print("✅ Started listening without context manager")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_economy_mode())
