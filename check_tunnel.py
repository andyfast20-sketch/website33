import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Get last call
cursor.execute('SELECT id, phone_number, created_at FROM call_logs ORDER BY id DESC LIMIT 1')
row = cursor.fetchone()

if row:
    print(f'Last call ID: {row[0]}')
    print(f'From: {row[1]}')
    print(f'Time: {row[2]}')
    
    # Check webhook URL
    cursor.execute('SELECT webhook_url FROM webhook_logs WHERE call_id = ? LIMIT 1', (row[0],))
    webhook = cursor.fetchone()
    
    if webhook and webhook[0]:
        url = webhook[0]
        print(f'\nWebhook URL: {url}')
        
        if 'ngrok' in url:
            print('\n✅ TUNNEL TYPE: NGROK')
        elif 'trycloudflare' in url:
            print('\n✅ TUNNEL TYPE: CLOUDFLARE')
        else:
            print('\n⚠️ TUNNEL TYPE: UNKNOWN')
    else:
        print('\n⚠️ No webhook URL found')
else:
    print('No calls found')

conn.close()
