"""Test Deepgram SDK imports for version 5.3.0"""
import sys

# Test basic import
try:
    from deepgram import DeepgramClient
    print("✅ DeepgramClient imported")
except ImportError as e:
    print(f"❌ Failed to import DeepgramClient: {e}")
    sys.exit(1)

# Check client structure
client = DeepgramClient(api_key="test")
print(f"\nClient attributes: {[attr for attr in dir(client) if not attr.startswith('_')]}")
print(f"\nClient.listen attributes: {[attr for attr in dir(client.listen) if not attr.startswith('_')]}")

# Try to find LiveOptions
try:
    from deepgram.clients.listen import LiveOptions
    print("✅ LiveOptions found at deepgram.clients.listen")
except ImportError:
    try:
        from deepgram import LiveOptions
        print("✅ LiveOptions found at deepgram")
    except ImportError:
        print("❌ LiveOptions not found, checking alternatives...")
        import deepgram.clients.listen as listen_module
        print(f"   listen module contents: {[attr for attr in dir(listen_module) if not attr.startswith('_')]}")

# Try to find LiveTranscriptionEvents
try:
    from deepgram.clients.listen import LiveTranscriptionEvents
    print("✅ LiveTranscriptionEvents found at deepgram.clients.listen")
except ImportError:
    print("❌ LiveTranscriptionEvents not found")
