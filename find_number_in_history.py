import sqlite3

conn = sqlite3.connect('call_logs.db')
c = conn.cursor()

# Check recent calls to/from user 27 to find the number
print("=== RECENT CALLS FOR USER 27 ===")
c.execute('''
    SELECT id, user_id, to_number, from_number, created_at
    FROM calls
    WHERE user_id = 27
    ORDER BY created_at DESC
    LIMIT 10
''')
calls = c.fetchall()
if calls:
    for call in calls:
        print(f"  Call {call[0]}: To: {call[2]}, From: {call[3]}, Date: {call[4]}")
else:
    print("  No calls found for user 27")

# Check all distinct numbers from calls involving user 27
print("\n=== PHONE NUMBERS ASSOCIATED WITH USER 27 ===")
c.execute('''
    SELECT DISTINCT to_number FROM calls WHERE user_id = 27 AND to_number LIKE '%271'
    UNION
    SELECT DISTINCT from_number FROM calls WHERE user_id = 27 AND from_number LIKE '%271'
''')
numbers = c.fetchall()
if numbers:
    for num in numbers:
        print(f"  Found: {num[0]}")
else:
    print("  No numbers ending in 271 found in call history")

# Try to find any number ending in 271 in the calls table
print("\n=== ALL NUMBERS ENDING IN 271 IN CALL HISTORY ===")
c.execute('''
    SELECT DISTINCT to_number FROM calls WHERE to_number LIKE '%271'
    UNION
    SELECT DISTINCT from_number FROM calls WHERE from_number LIKE '%271'
''')
all_271_numbers = c.fetchall()
if all_271_numbers:
    for num in all_271_numbers:
        print(f"  {num[0]}")
else:
    print("  No numbers ending in 271 found")

conn.close()
