import sqlite3

DB_PATH = "voice_agent.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create global_settings if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS global_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        global_instructions TEXT DEFAULT '',
        speechmatics_api_key TEXT DEFAULT NULL,
        openai_api_key TEXT DEFAULT NULL,
        deepseek_api_key TEXT DEFAULT NULL,
        vonage_api_key TEXT DEFAULT NULL,
        vonage_api_secret TEXT DEFAULT NULL,
        vonage_application_id TEXT DEFAULT NULL,
        vonage_private_key_pem TEXT DEFAULT NULL,
        ai_brain_provider TEXT DEFAULT 'openai',
        filler_words TEXT DEFAULT '',
        filler_words_small TEXT DEFAULT '',
        filler_words_medium TEXT DEFAULT '',
        filler_words_large TEXT DEFAULT '',
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_by TEXT DEFAULT 'admin',
        ignore_backchannels_always INTEGER DEFAULT 1,
        backchannel_max_words INTEGER DEFAULT 3,
        min_user_turn_seconds REAL DEFAULT 0.45,
        barge_in_min_speech_seconds REAL DEFAULT 0.55
    )
''')

# Add racing columns to global_settings
try:
    cursor.execute("ALTER TABLE global_settings ADD COLUMN racing_enabled INTEGER DEFAULT 0")
    print("✅ Added racing_enabled column")
except sqlite3.OperationalError as e:
    print(f"⚠️ racing_enabled column may already exist: {e}")

try:
    cursor.execute("ALTER TABLE global_settings ADD COLUMN openrouter_model_2 TEXT DEFAULT NULL")
    print("✅ Added openrouter_model_2 column")
except sqlite3.OperationalError as e:
    print(f"⚠️ openrouter_model_2 column may already exist: {e}")

try:
    cursor.execute("ALTER TABLE global_settings ADD COLUMN openrouter_model_3 TEXT DEFAULT NULL")
    print("✅ Added openrouter_model_3 column")
except sqlite3.OperationalError as e:
    print(f"⚠️ openrouter_model_3 column may already exist: {e}")

conn.commit()
conn.close()

print("\n✅ Racing columns migration complete!")
print("Now you can:")
print("  1. Enable/disable racing mode")
print("  2. Select up to 3 OpenRouter models to race")
print("  3. First model to respond wins, others are cancelled")
