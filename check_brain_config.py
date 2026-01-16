import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get last call UUID
c.execute("SELECT call_uuid FROM calls ORDER BY created_at DESC LIMIT 1")
uuid = c.fetchone()[0]

print(f"Call UUID: {uuid}\n")

# Check brain usage
c.execute("""
    SELECT brain_provider, model_used, racing_enabled, turn_number, response_time_ms
    FROM call_brain_usage 
    WHERE call_uuid = ?
    ORDER BY turn_number ASC
""", (uuid,))

brain_usage = c.fetchall()

if brain_usage:
    print(f"=== BRAIN USAGE ({len(brain_usage)} turns) ===\n")
    for provider, model, racing, turn, response_ms in brain_usage:
        racing_status = "✅ RACING ON" if racing else "❌ RACING OFF"
        print(f"Turn {turn}: {provider} | {model or 'N/A'} | {racing_status} | {response_ms or 'N/A'}ms")
else:
    print("No brain usage data found\n")

# Check global settings for racing and filler config
c.execute("""
    SELECT racing_enabled, ai_brain_provider, 
           small_filler_duration_ms, medium_filler_duration_ms, large_filler_duration_ms
    FROM global_settings 
    WHERE id = 1
""")

settings = c.fetchone()
if settings:
    racing, brain, small, medium, large = settings
    print(f"\n=== GLOBAL SETTINGS ===\n")
    print(f"Brain Provider: {brain}")
    print(f"Racing Enabled: {'✅ YES' if racing else '❌ NO'}")
    print(f"Filler Sizes: small={small}ms, medium={medium}ms, large={large}ms")

# Check if there are any filler phrases configured
c.execute("SELECT COUNT(*) FROM global_filler_phrases")
filler_count = c.fetchone()[0]
print(f"\nConfigured Fillers: {filler_count} phrases")

conn.close()
