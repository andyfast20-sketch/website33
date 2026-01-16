import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get last call UUID
c.execute("SELECT call_uuid, created_at FROM calls ORDER BY created_at DESC LIMIT 1")
call = c.fetchone()

if call:
    uuid, created = call
    print(f"=== CALL ANALYSIS ===")
    print(f"UUID: {uuid}")
    print(f"Time: {created}")
    
    # Get latency events for this call
    c.execute("""
        SELECT turn_index, event_name, ms_from_turn_start, created_at 
        FROM call_latency_events 
        WHERE call_uuid = ? 
        ORDER BY created_at ASC
    """, (uuid,))
    
    events = c.fetchall()
    
    if events:
        print(f"\n=== LATENCY TRACKING ({len(events)} events) ===")
        current_turn = None
        turn_data = {}
        
        for turn_idx, event_type, ms_from_start, ts in events:
            if current_turn != turn_idx:
                if current_turn is not None and turn_data:
                    # Calculate latencies for previous turn
                    if 'caller_stopped' in turn_data and 'first_audio' in turn_data:
                        total = turn_data['first_audio'] - turn_data['caller_stopped']
                        print(f"\n  Turn {current_turn} TOTAL LATENCY: {total:.0f}ms")
                        if 'brain_triggered' in turn_data:
                            brain_time = turn_data['first_audio'] - turn_data['brain_triggered']
                            print(f"    Brain→Audio: {brain_time:.0f}ms")
                
                current_turn = turn_idx
                turn_data = {}
                print(f"\n--- Turn {turn_idx} ---")
            
            turn_data[event_type] = ms_from_start
            print(f"  {event_type}: +{ms_from_start:.0f}ms")
        
        # Process last turn
        if current_turn is not None and turn_data:
            if 'caller_stopped' in turn_data and 'first_audio' in turn_data:
                total = turn_data['first_audio'] - turn_data['caller_stopped']
                print(f"\n  Turn {current_turn} TOTAL LATENCY: {total:.0f}ms")
                if 'brain_triggered' in turn_data:
                    brain_time = turn_data['first_audio'] - turn_data['brain_triggered']
                    print(f"    Brain→Audio: {brain_time:.0f}ms")
    else:
        print("\nNo latency events tracked for this call")
    
    # Check call_logs table for any logged info
    try:
        c.execute("SELECT log_level, message, timestamp FROM call_logs WHERE call_uuid = ? ORDER BY timestamp DESC LIMIT 20", (uuid,))
        logs = c.fetchall()
        
        if logs:
            print(f"\n=== RECENT LOGS ===")
            for level, msg, ts in logs[:10]:
                if 'latency' in msg.lower() or 'slow' in msg.lower() or 'filler' in msg.lower():
                    print(f"[{level}] {msg[:120]}")
    except:
        pass

conn.close()
