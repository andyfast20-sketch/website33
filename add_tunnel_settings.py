import sqlite3

def add_tunnel_settings():
    """Add tunnel provider settings to global_settings table"""
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(global_settings)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'tunnel_provider' not in columns:
        cursor.execute('ALTER TABLE global_settings ADD COLUMN tunnel_provider TEXT DEFAULT "ngrok"')
        print("✅ Added tunnel_provider column (default: ngrok)")
    
    if 'cloudflare_domain' not in columns:
        cursor.execute('ALTER TABLE global_settings ADD COLUMN cloudflare_domain TEXT DEFAULT NULL')
        print("✅ Added cloudflare_domain column")
    
    if 'cloudflare_tunnel_token' not in columns:
        cursor.execute('ALTER TABLE global_settings ADD COLUMN cloudflare_tunnel_token TEXT DEFAULT NULL')
        print("✅ Added cloudflare_tunnel_token column")

    if 'public_url' not in columns:
        cursor.execute('ALTER TABLE global_settings ADD COLUMN public_url TEXT DEFAULT NULL')
        print("✅ Added public_url column")
    
    conn.commit()
    conn.close()
    print("✅ Tunnel settings migration complete.")

if __name__ == '__main__':
    add_tunnel_settings()
