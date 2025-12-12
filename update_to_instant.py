"""
Update response_latency for all accounts to 100ms for instant responses
"""
import sqlite3

def update_response_latency():
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()
    
    print("Updating response latency for all accounts to 100ms (instant)...")
    
    try:
        # Update all accounts to use 100ms response time
        cursor.execute('UPDATE account_settings SET response_latency = 100')
        updated = cursor.rowcount
        conn.commit()
        print(f"✅ Updated {updated} account(s) to 100ms response latency")
        print("   This will make AI responses instant (sub-1 second total)")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_response_latency()
