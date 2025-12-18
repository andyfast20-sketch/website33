"""Find which parameter causes the HTTP 400"""
import os
from deepgram import DeepgramClient

API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing DEEPGRAM_API_KEY env var")
client = DeepgramClient(api_key=API_KEY)

base_params = {
    "model": "nova-2",
    "encoding": "linear16",
    "sample_rate": 16000,
}

test_params = [
    ("language", "en"),
    ("smart_format", True),
    ("interim_results", False),
    ("utterance_end_ms", 1000),
    ("vad_events", True),
]

print("Testing each parameter individually...\n")

for param_name, param_value in test_params:
    try:
        params = base_params.copy()
        params[param_name] = param_value
        
        print(f"Testing with {param_name}={param_value}... ", end="")
        dg_connection_context = client.listen.v1.connect(**params)
        dg_connection = dg_connection_context.__enter__()
        dg_connection_context.__exit__(None, None, None)
        print("✅ OK")
    except Exception as e:
        print(f"❌ FAILED: {e}")

print("\nTesting ALL parameters together...")
try:
    all_params = base_params.copy()
    for param_name, param_value in test_params:
        all_params[param_name] = param_value
    
    dg_connection_context = client.listen.v1.connect(**all_params)
    dg_connection = dg_connection_context.__enter__()
    dg_connection_context.__exit__(None, None, None)
    print("✅ ALL PARAMETERS WORK!")
except Exception as e:
    print(f"❌ ALL TOGETHER FAILED: {e}")
