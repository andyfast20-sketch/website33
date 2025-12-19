import sqlite3

# Add quality analysis columns to calls table
conn = sqlite3.connect('call_logs.db')
cursor = conn.cursor()

try:
    # Add new columns for quality analysis
    cursor.execute('ALTER TABLE calls ADD COLUMN quality_score INTEGER DEFAULT NULL')
    print("✅ Added quality_score column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  quality_score column already exists")
    else:
        raise

try:
    cursor.execute('ALTER TABLE calls ADD COLUMN quality_analysis TEXT DEFAULT NULL')
    print("✅ Added quality_analysis column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  quality_analysis column already exists")
    else:
        raise

try:
    cursor.execute('ALTER TABLE calls ADD COLUMN instruction_adherence TEXT DEFAULT NULL')
    print("✅ Added instruction_adherence column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  instruction_adherence column already exists")
    else:
        raise

try:
    cursor.execute('ALTER TABLE calls ADD COLUMN performance_issues TEXT DEFAULT NULL')
    print("✅ Added performance_issues column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  performance_issues column already exists")
    else:
        raise

conn.commit()
conn.close()

print("\n✅ Database schema updated successfully!")
print("New columns added:")
print("  - quality_score: INTEGER (0-100)")
print("  - quality_analysis: TEXT (DeepSeek analysis)")
print("  - instruction_adherence: TEXT (How well instructions were followed)")
print("  - performance_issues: TEXT (Any performance problems detected)")
