import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get last call
c.execute("SELECT call_uuid, created_at FROM calls ORDER BY created_at DESC LIMIT 1")
call = c.fetchone()

if call:
    uuid, created = call
    print(f"Call: {uuid}")
    print(f"Time: {created}\n")
    
    # Check call_logs for filler-related messages
    c.execute("""
        SELECT log_level, message, timestamp 
        FROM call_logs 
        WHERE call_uuid = ? AND (
            message LIKE '%filler%' OR 
            message LIKE '%Filler%' OR
            message LIKE '%FILLER%'
        )
        ORDER BY timestamp ASC
    """, (uuid,))
    
    logs = c.fetchall()
    
    if logs:
        print(f"=== FILLER LOGS ({len(logs)} entries) ===")
        for level, msg, ts in logs:
            print(f"[{ts}] {msg}")
    else:
        print("❌ NO FILLER LOGS FOUND")
        print("\nThis means the filler system never triggered.")
        print("Checking why...")
        
        # Check if response was triggered
        c.execute("""
            SELECT log_level, message, timestamp 
            FROM call_logs 
            WHERE call_uuid = ? AND (
                message LIKE '%response triggered%' OR
                message LIKE '%trigger%brain%' OR
                message LIKE '%speech_stopped%'
            )
            ORDER BY timestamp ASC
            LIMIT 10
        """, (uuid,))
        
        triggers = c.fetchall()
        if triggers:
            print("\n=== RESPONSE TRIGGER LOGS ===")
            for level, msg, ts in triggers[:5]:
                print(f"[{ts}] {msg[:150]}")

conn.close()
