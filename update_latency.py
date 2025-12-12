"""
Update response_latency for all accounts to 200ms for faster responses
"""
import sqlite3

def update_response_latency():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    print("Updating response latency for all accounts to 200ms (faster)...")
    
    try:
        # Update all accounts to use 200ms response time
        cursor.execute('UPDATE account_settings SET response_latency = 200 WHERE response_latency = 500 OR response_latency IS NULL')
        updated = cursor.rowcount
        conn.commit()
        print(f"✅ Updated {updated} account(s) to 200ms response latency")
        print("   This will make AI responses much faster (about 1 second total response time)")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_response_latency()
