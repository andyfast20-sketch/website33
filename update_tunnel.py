import sqlite3

# Try to find the right database
dbs = ['phone_agent.db', 'voice_agent.db', 'agent_data.db', 'agents.db']

for db_name in dbs:
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='global_settings'")
        if cursor.fetchone():
            print(f"Found global_settings in {db_name}")
            
            # Update tunnel provider
            cursor.execute("UPDATE global_settings SET tunnel_provider = ?, public_url = ? WHERE id = 1", 
                         ('cloudflare', 'https://nick-hollywood-slight-affects.trycloudflare.com'))
            conn.commit()
            
            # Verify
            cursor.execute("SELECT tunnel_provider, public_url FROM global_settings WHERE id = 1")
            row = cursor.fetchone()
            print(f"Updated: Provider={row[0]}, URL={row[1]}")
            conn.close()
            break
        conn.close()
    except Exception as e:
        print(f"Error with {db_name}: {e}")
