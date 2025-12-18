import sqlite3
from datetime import datetime

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Check if sessions table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
if not cursor.fetchone():
    print("❌ Sessions table does not exist!")
else:
    print("✅ Sessions table exists")
    
    # Check recent sessions
    cursor.execute('''
        SELECT s.user_id, u.name, s.session_token, s.expires_at, s.created_at
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at DESC
        LIMIT 5
    ''')
    
    sessions = cursor.fetchall()
    print(f"\n📋 Recent sessions ({len(sessions)} total):")
    for session in sessions:
        user_id, name, token, expires_at, created_at = session
        expired = datetime.fromisoformat(expires_at) < datetime.now()
        status = "❌ EXPIRED" if expired else "✅ ACTIVE"
        print(f"  User: {name} (ID: {user_id}) - {status}")
        print(f"    Token: {token[:20]}...")
        print(f"    Expires: {expires_at}")
        print()

conn.close()
