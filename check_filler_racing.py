import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get last call UUID
c.execute("SELECT call_uuid FROM calls ORDER BY created_at DESC LIMIT 1")
uuid = c.fetchone()[0]

print(f"Call UUID: {uuid}\n")

# Check call_logs for filler and racing messages
c.execute("""
    SELECT message, timestamp 
    FROM call_logs 
    WHERE call_uuid = ? 
    AND (
        message LIKE '%filler%' 
        OR message LIKE '%racing%'
        OR message LIKE '%openrouter%'
        OR message LIKE '%brain%'
        OR message LIKE '%model%'
    )
    ORDER BY timestamp ASC
""", (uuid,))

logs = c.fetchall()

if logs:
    print(f"=== FILLER & RACING LOGS ({len(logs)} messages) ===\n")
    for msg, ts in logs:
        print(f"[{ts}] {msg}")
else:
    print("No filler/racing logs found")

# Check brain usage
c.execute("""
    SELECT brain_provider, model_used, racing_enabled, turn_number, response_time_ms
    FROM call_brain_usage 
    WHERE call_uuid = ?
    ORDER BY turn_number ASC
""", (uuid,))

brain_usage = c.fetchall()

if brain_usage:
    print(f"\n\n=== BRAIN USAGE ({len(brain_usage)} turns) ===\n")
    for provider, model, racing, turn, response_ms in brain_usage:
        racing_status = "✅ RACING" if racing else "❌ NO RACING"
        print(f"Turn {turn}: {provider} | {model} | {racing_status} | {response_ms}ms")

conn.close()
