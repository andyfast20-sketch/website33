"""Test Deepgram WebSocket with minimal parameters"""
import os
from deepgram import DeepgramClient

API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing DEEPGRAM_API_KEY env var")

print(f"Testing with MINIMAL parameters...")

try:
    client = DeepgramClient(api_key=API_KEY)
    
    # Try with minimal parameters
    print("Attempting minimal connection...")
    dg_connection_context = client.listen.v1.connect(
        model="nova-2",
        encoding="linear16",
        sample_rate=16000,
    )
    
    dg_connection = dg_connection_context.__enter__()
    print("✅ SUCCESS with minimal parameters!")
    dg_connection_context.__exit__(None, None, None)
    
except Exception as e:
    print(f"❌ Minimal failed: {e}")
    
    # Try with different encoding
    try:
        print("\nTrying with 'mulaw' encoding...")
        dg_connection_context = client.listen.v1.connect(
            model="nova-2",
            encoding="mulaw",
            sample_rate=8000,
        )
        dg_connection = dg_connection_context.__enter__()
        print("✅ SUCCESS with mulaw!")
        dg_connection_context.__exit__(None, None, None)
    except Exception as e2:
        print(f"❌ Mulaw failed: {e2}")
        
        # Try without encoding specified
        try:
            print("\nTrying without encoding parameter...")
            dg_connection_context = client.listen.v1.connect(
                model="nova-2",
            )
            dg_connection = dg_connection_context.__enter__()
            print("✅ SUCCESS without encoding!")
            dg_connection_context.__exit__(None, None, None)
        except Exception as e3:
            print(f"❌ No encoding failed: {e3}")
