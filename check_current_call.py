import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get the most recent call
c.execute("SELECT call_uuid, created_at, status FROM calls ORDER BY created_at DESC LIMIT 1")
call = c.fetchone()

if call:
    uuid, created, status = call
    print(f"=== MOST RECENT CALL ===")
    print(f"UUID: {uuid}")
    print(f"Time: {created}")
    print(f"Status: {status}\n")
    
    # Check latency events for this call
    c.execute("""
        SELECT turn_index, event_name, ms_from_turn_start 
        FROM call_latency_events 
        WHERE call_uuid = ? 
        ORDER BY created_at DESC
        LIMIT 15
    """, (uuid,))
    
    events = c.fetchall()
    if events:
        print(f"=== RECENT LATENCY EVENTS ===")
        for turn, event, ms in events:
            print(f"  Turn {turn}: {event} at +{ms:.0f}ms")
    
    # Check brain usage
    c.execute("""
        SELECT turn_number, provider, tokens_used, response_time_ms 
        FROM call_brain_usage 
        WHERE call_uuid = ? 
        ORDER BY turn_number DESC
        LIMIT 5
    """, (uuid,))
    
    brain = c.fetchall()
    if brain:
        print(f"\n=== BRAIN USAGE (last 5 turns) ===")
        for turn, provider, tokens, response_time in brain:
            print(f"  Turn {turn}: {provider} - {response_time}ms ({tokens} tokens)")

conn.close()
