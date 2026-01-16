"""
Add Ted - Virtual Performance Manager
Ted monitors call quality, learns from mistakes, and auto-adjusts settings.
He doesn't want to lose his job, so he constantly improves.
"""
import sqlite3

DB_PATH = "call_logs.db"

def add_ted_manager():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Ted's performance tracking table
    c.execute("""
        CREATE TABLE IF NOT EXISTS ted_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            call_uuid TEXT,
            metric_type TEXT,
            metric_value REAL,
            issue_detected TEXT,
            action_taken TEXT
        )
    """)
    
    # Ted's learning memory - what went wrong and how he fixed it
    c.execute("""
        CREATE TABLE IF NOT EXISTS ted_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            problem_pattern TEXT,
            solution_applied TEXT,
            success_rate REAL DEFAULT 0.0,
            times_encountered INTEGER DEFAULT 1,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ted's current settings/adjustments
    c.execute("""
        CREATE TABLE IF NOT EXISTS ted_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            performance_score REAL DEFAULT 100.0,
            job_security_level REAL DEFAULT 100.0,
            negative_feedback_count INTEGER DEFAULT 0,
            auto_adjust_enabled INTEGER DEFAULT 1,
            filler_timing_ms REAL DEFAULT 500.0,
            min_user_turn_override REAL DEFAULT NULL,
            barge_in_override REAL DEFAULT NULL,
            last_adjustment DATETIME DEFAULT CURRENT_TIMESTAMP,
            ted_mood TEXT DEFAULT 'confident'
        )
    """)
    
    # Insert initial Ted settings if not exists
    c.execute("""
        INSERT OR IGNORE INTO ted_settings (id, performance_score, job_security_level, ted_mood)
        VALUES (1, 100.0, 100.0, 'confident')
    """)
    
    conn.commit()
    conn.close()
    print("✅ Ted is now employed! He's ready to monitor calls and keep his job.")
    print("   Performance Score: 100/100")
    print("   Job Security: 100%")
    print("   Mood: Confident and motivated")

if __name__ == "__main__":
    add_ted_manager()
