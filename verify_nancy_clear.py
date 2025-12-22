import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

# Clear Nancy's suspension fields
cursor.execute('''UPDATE account_settings 
                  SET is_suspended = 0, 
                      suspension_reason = NULL, 
                      suspended_at = NULL, 
                      last_flag_details = NULL 
                  WHERE user_id = 6''')
conn.commit()

print("✅ Nancy's suspension fields cleared")
print("\nCurrent Nancy account status:")

# Verify
cursor.execute('''SELECT is_suspended, suspension_reason, suspended_at, 
                         suspension_count, last_flag_details 
                  FROM account_settings 
                  WHERE user_id = 6''')
row = cursor.fetchone()

print(f"  is_suspended: {row[0]} (0 = active)")
print(f"  suspension_reason: {row[1]}")
print(f"  suspended_at: {row[2]}")
print(f"  suspension_count: {row[3]} (preserved for history)")
print(f"  last_flag_details: {row[4]}")

conn.close()

print("\n✅ Nancy's account is now fully restored and active!")
print("   The suspension_count is preserved for tracking purposes only.")
