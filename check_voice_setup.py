import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Check tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

# Check global_settings for voice-related columns
if 'global_settings' in tables:
    c.execute('PRAGMA table_info(global_settings)')
    cols = c.fetchall()
    print("\nGlobal settings columns:")
    for col in cols:
        print(f"  {col[1]}")

# Check accounts for voice-related columns  
if 'accounts' in tables:
    c.execute('PRAGMA table_info(accounts)')
    cols = c.fetchall()
    print("\nAccounts columns (voice-related):")
    for col in cols:
        if any(x in col[1].lower() for x in ['voice', 'tts', 'speech', 'eleven', 'play', 'google', 'cartesia', 'lemon']):
            print(f"  {col[1]}")

conn.close()
