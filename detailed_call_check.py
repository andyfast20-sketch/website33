import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Get last call UUID
c.execute("SELECT call_uuid FROM calls ORDER BY created_at DESC LIMIT 1")
uuid = c.fetchone()[0]

print(f"Call UUID: {uuid}\n")

# Check brain usage turns
c.execute("""
    SELECT openai_turns, deepseek_turns, groq_turns, grok_turns, openrouter_turns
    FROM call_brain_usage 
    WHERE call_uuid = ?
""", (uuid,))

usage = c.fetchone()
if usage:
    openai, deepseek, groq, grok, openrouter = usage
    print(f"=== BRAIN USAGE ===")
    print(f"OpenAI: {openai or 0} turns")
    print(f"DeepSeek: {deepseek or 0} turns")
    print(f"Groq: {groq or 0} turns")
    print(f"Grok: {grok or 0} turns")
    print(f"OpenRouter: {openrouter or 0} turns")
    
    if openrouter and openrouter > 0:
        print(f"\n✅ OpenRouter was used ({openrouter} turns)")
    else:
        print(f"\n❌ OpenRouter NOT used")

# Check global settings for racing and brain provider
c.execute("""
    SELECT racing_enabled, ai_brain_provider
    FROM global_settings 
    WHERE id = 1
""")

settings = c.fetchone()
if settings:
    racing, brain = settings
    print(f"\n=== GLOBAL SETTINGS ===")
    print(f"Brain Provider: {brain}")
    print(f"Racing Enabled: {'✅ YES' if racing else '❌ NO'}")

# Check latency events to see if fillers were attempted
c.execute("""
    SELECT turn_index, event_name, ms_from_turn_start
    FROM call_latency_events 
    WHERE call_uuid = ?
    ORDER BY turn_index, ms_from_turn_start ASC
""", (uuid,))

events = c.fetchall()
print(f"\n=== LATENCY EVENTS PER TURN ===")
current_turn = None
for turn, event, ms in events:
    if turn != current_turn:
        current_turn = turn
        print(f"\nTurn {turn}:")
    print(f"  {event}: +{ms:.0f}ms")

conn.close()
