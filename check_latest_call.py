import sqlite3
from datetime import datetime

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get most recent call
cursor.execute('SELECT call_uuid, caller_number, start_time FROM calls ORDER BY start_time DESC LIMIT 1')
call = cursor.fetchone()
if not call:
    print("No calls found")
    exit()

call_uuid, caller, start_time = call
print(f"\n=== Most Recent Call ===")
print(f"UUID: {call_uuid}")
print(f"Caller: {caller}")
print(f"Time: {start_time}")

# Get transcript
cursor.execute('SELECT speaker, text, timestamp FROM transcript WHERE call_uuid = ? ORDER BY timestamp', (call_uuid,))
transcript = cursor.fetchall()
print(f"\n=== Transcript ({len(transcript)} parts) ===")
for speaker, text, ts in transcript:
    print(f"{speaker}: {text[:100]}..." if len(text) > 100 else f"{speaker}: {text}")

# Get latency events
cursor.execute('SELECT turn_index, event_name, ms_from_turn_start FROM call_latency_events WHERE call_uuid = ? ORDER BY turn_index, ms_from_turn_start', (call_uuid,))
events = cursor.fetchall()
if events:
    print(f"\n=== Latency Events ===")
    current_turn = None
    for turn, event, ms in events:
        if turn != current_turn:
            print(f"\nTurn {turn}:")
            current_turn = turn
        print(f"  +{ms:.0f}ms: {event}")

# Get brain usage
cursor.execute('SELECT brain_provider, openrouter_turns FROM call_brain_usage WHERE call_uuid = ?', (call_uuid,))
brain = cursor.fetchone()
if brain:
    print(f"\n=== Brain Usage ===")
    print(f"Provider: {brain[0]}")
    print(f"OpenRouter turns: {brain[1]}")

conn.close()
