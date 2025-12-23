import sqlite3

def setup_database():
    """Set up the SQLite database with the correct schema."""
    conn = sqlite3.connect('call_logs.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
    ''')

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create calls table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_uuid TEXT UNIQUE,
            caller_number TEXT,
            called_number TEXT,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER,
            transcript TEXT,
            summary TEXT,
            status TEXT DEFAULT 'active',
            user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            average_response_time REAL,
            transfer_initiated INTEGER DEFAULT 0,
            transfer_duration INTEGER DEFAULT 0,
            transfer_credits_charged REAL DEFAULT 0,
            booking_credits_charged REAL DEFAULT 0,
            task_credits_charged REAL DEFAULT 0,
            advanced_voice_credits_charged REAL DEFAULT 0,
            sales_detector_credits_charged REAL DEFAULT 0,
            sales_confidence INTEGER DEFAULT NULL,
            sales_reasoning TEXT DEFAULT NULL,
            sales_ended_by_detector INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER DEFAULT 30,
            title TEXT,
            description TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            status TEXT DEFAULT 'scheduled',
            created_by TEXT DEFAULT 'user',
            call_uuid TEXT,
            user_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            source TEXT DEFAULT 'manual',
            call_uuid TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create account_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            minutes_remaining INTEGER DEFAULT 60,
            total_minutes_purchased INTEGER DEFAULT 60,
            voice TEXT DEFAULT 'shimmer',
            use_elevenlabs INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            elevenlabs_voice_id TEXT DEFAULT 'EXAVITQu4vr4xnSDxMaL',
            phone_number TEXT,
            response_latency INTEGER DEFAULT 300,
            voice_provider TEXT DEFAULT 'openai',
            cartesia_voice_id TEXT DEFAULT 'a0e99841-438c-4a64-b679-ae501e7d6091',
            google_voice TEXT DEFAULT 'en-GB-Neural2-A',
            playht_voice_id TEXT DEFAULT 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json',
            agent_name TEXT DEFAULT 'Judie',
            business_info TEXT DEFAULT '',
            agent_personality TEXT DEFAULT 'Friendly and professional. Keep responses brief and conversational.',
            agent_instructions TEXT DEFAULT 'Answer questions about the business. Take messages if needed.',
            calendar_booking_enabled INTEGER DEFAULT 1,
            tasks_enabled INTEGER DEFAULT 1,
            advanced_voice_enabled INTEGER DEFAULT 0,
            sales_detector_enabled INTEGER DEFAULT 0,
            call_greeting TEXT DEFAULT '',
            transfer_number TEXT DEFAULT '',
            transfer_people TEXT DEFAULT '[]',
            first_login_completed INTEGER DEFAULT 0,
            trial_days_remaining INTEGER DEFAULT 3,
            trial_start_date TEXT DEFAULT NULL,
            trial_total_days INTEGER DEFAULT 3,
            is_suspended INTEGER DEFAULT 0,
            suspension_reason TEXT DEFAULT NULL,
            suspended_at TEXT DEFAULT NULL,
            suspension_count INTEGER DEFAULT 0,
            last_flag_details TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create lemonsqueezy_processed_orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lemonsqueezy_processed_orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            event_name TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create stripe_processed_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stripe_processed_events (
            event_id TEXT PRIMARY KEY,
            session_id TEXT,
            user_id INTEGER,
            event_type TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create global_settings table
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
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT DEFAULT 'admin',
            ignore_backchannels_always INTEGER DEFAULT 1,
            backchannel_max_words INTEGER DEFAULT 3,
            min_user_turn_seconds REAL DEFAULT 0.45,
            barge_in_min_speech_seconds REAL DEFAULT 0.55
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO global_settings (id, global_instructions) VALUES (1, "")')

    # Create super_admin_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS super_admin_sessions (
            token_sha256 TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            last_used_at TEXT NOT NULL,
            ip TEXT DEFAULT '',
            user_agent TEXT DEFAULT ''
        )
    ''')

    # Create super_admin_config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS super_admin_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == '__main__':
    setup_database()
