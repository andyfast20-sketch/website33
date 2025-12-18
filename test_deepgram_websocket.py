"""Test Deepgram WebSocket connection with their SDK"""
import os
from deepgram import DeepgramClient

API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing DEEPGRAM_API_KEY env var")

print(f"Testing Deepgram WebSocket connection...")

try:
    client = DeepgramClient(api_key=API_KEY)
    print("✅ Client initialized")
    
    # Try to connect
    print("Attempting to connect to Deepgram live transcription...")
    dg_connection_context = client.listen.v1.connect(
        model="nova-2",
        language="en",
        smart_format=True,
        encoding="linear16",
        sample_rate=16000,
        interim_results=False,
        utterance_end_ms=1000,
        vad_events=True,
    )
    
    print("Connection context created")
    
    # Enter context manager
    dg_connection = dg_connection_context.__enter__()
    print("✅ Successfully entered context manager - WebSocket connected!")
    
    # Close it
    dg_connection_context.__exit__(None, None, None)
    print("✅ Connection closed cleanly")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
