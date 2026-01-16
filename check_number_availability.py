import sqlite3

conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

print("=== Number Availability Table ===\n")

# Check table structure
cursor.execute("PRAGMA table_info(number_availability)")
columns = cursor.fetchall()
print("Columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Find number ending in 271
print("\n=== Searching for number ending in 271 ===")
cursor.execute("SELECT * FROM number_availability WHERE number LIKE '%271'")
number = cursor.fetchone()
if number:
    print(f"Found: {number}")
else:
    print("Not found in number_availability table")

# Show all numbers
print("\n=== All numbers in availability table ===")
cursor.execute("SELECT * FROM number_availability")
all_numbers = cursor.fetchall()
for n in all_numbers:
    print(f"  {n}")

# Check calls table for numbers ending in 271
print("\n=== Checking calls table for 271 numbers ===")
cursor.execute("SELECT DISTINCT caller, called FROM calls WHERE caller LIKE '%271' OR called LIKE '%271' LIMIT 10")
calls = cursor.fetchall()
for c in calls:
    print(f"  Caller: {c[0]}, Called: {c[1]}")

conn.close()
