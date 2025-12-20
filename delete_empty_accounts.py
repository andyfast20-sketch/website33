import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Find accounts with no phone numbers
cursor.execute('''
    SELECT a.user_id, u.name, a.phone_number
    FROM account_settings a 
    JOIN users u ON a.user_id = u.id 
    WHERE a.phone_number IS NULL OR a.phone_number = ''
''')

accounts_to_delete = cursor.fetchall()

print("\n=== ACCOUNTS TO DELETE ===")
for user_id, name, phone in accounts_to_delete:
    print(f"User {user_id} ({name}): phone={phone}")

if accounts_to_delete:
    confirm = input(f"\nDelete {len(accounts_to_delete)} accounts? (yes/no): ")
    if confirm.lower() == 'yes':
        for user_id, name, phone in accounts_to_delete:
            # Delete from account_settings first (foreign key)
            cursor.execute('DELETE FROM account_settings WHERE user_id = ?', (user_id,))
            # Delete from users
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            print(f"✅ Deleted user {user_id} ({name})")
        
        conn.commit()
        print(f"\n✅ Successfully deleted {len(accounts_to_delete)} accounts")
    else:
        print("❌ Cancelled")
else:
    print("\nNo accounts to delete")

conn.close()
