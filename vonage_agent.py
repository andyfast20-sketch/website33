"""
Vonage Voice Agent - Production Ready
=====================================
Connects phone calls to OpenAI Realtime API for voice conversations.

Usage:
1. Install dependencies: pip install fastapi uvicorn websockets numpy scipy
2. Set environment variables or update config below
3. Run: python vonage_agent.py
4. Use ngrok: ngrok http 8000
5. Set Vonage webhooks to your ngrok URL
"""

import asyncio
import base64
import json
import logging
import os
import subprocess
import secrets
import hashlib
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import sqlite3
import io

import numpy as np
from scipy import signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Header
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn
import openai
import httpx
from elevenlabs import ElevenLabs, VoiceSettings
from google.cloud import texttospeech
from pyht import Client as PlayHTClient
from cartesia import Cartesia
import base64

# ============================================================================
# CONFIGURATION - Update these or set as environment variables
# ============================================================================

CONFIG = {
    # OpenAI - hardcoded to avoid environment variable conflicts
    "OPENAI_API_KEY": "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",
    
    # DeepSeek API Key (optional - for cheaper summaries)
    "DEEPSEEK_API_KEY": "sk-5892b01daa764aa9869c77a6b23ce271",
    
    # ElevenLabs API Key and Voice ID
    "ELEVENLABS_API_KEY": "sk_ed0fdc5eb5acd0a634bca953582f7cf9aa750424809900a4",
    "ELEVENLABS_VOICE_ID": "EXAVITQu4vr4xnSDxMaL",  # Bella - UK female
    "USE_ELEVENLABS": True,  # Initialize ElevenLabs client (per-user setting controls actual usage)
    
    # Google Cloud TTS
    "GOOGLE_CREDENTIALS_PATH": "google-credentials.json",
    "USE_GOOGLE_TTS": True,
    
    # PlayHT TTS
    "PLAYHT_USER_ID": "le8RMVjnrhd1q1aWgXZMNZ2Mnx73",
    "PLAYHT_API_KEY": "ak-097229e3e3f3463c8fbd2a877f1ac785",
    "USE_PLAYHT": True,  # Re-enabled with updated API
    
    # Cartesia AI (real-time streaming, 100+ voices, low latency)
    "CARTESIA_API_KEY": "sk_car_5S1GHCuxH1zeN2UEY3Mz9u",
    "USE_CARTESIA": True,  # ✅ ENABLED - Fastest option with 100+ voices
    
    # Summary model - which AI to use for call summaries
    # "openai": gpt-4o-mini ($0.15/$0.60 per 1M tokens)
    # "deepseek": deepseek-chat ($0.014/$0.028 per 1M tokens) - 15x cheaper!
    "SUMMARY_PROVIDER": "deepseek",
    "SUMMARY_MODEL": "gpt-4o-mini",
    
    # Vonage (optional - only needed for outbound calls)
    "VONAGE_APPLICATION_ID": os.getenv("VONAGE_APPLICATION_ID", ""),
    "VONAGE_PRIVATE_KEY_PATH": os.getenv("VONAGE_PRIVATE_KEY_PATH", "private.key"),
    "VONAGE_API_KEY": os.getenv("VONAGE_API_KEY", "b5d8ed31"),
    "VONAGE_API_SECRET": os.getenv("VONAGE_API_SECRET", "1D@X(NoflDKvv9Uy14"),
    
    # Server
    "HOST": "0.0.0.0",
    "PORT": 5004,
    
    # Your public URL (ngrok URL) - UPDATE THIS after starting ngrok
    "PUBLIC_URL": os.getenv("PUBLIC_URL", "https://unfasciate-unsurlily-suzanna.ngrok-free.dev"),
    
    # Agent personality
    "AGENT_NAME": "Judie",
    "BUSINESS_INFO": "",
    "AGENT_PERSONALITY": "Friendly and professional. Keep responses brief and conversational.",
    "AGENT_INSTRUCTIONS": "Answer questions about the business. Take messages if needed.",
    
    # Welcome message (spoken when call connects)
    "WELCOME_MESSAGE": "Hello! This is Judie. How can I help you today?",
}

# Audio settings
VONAGE_SAMPLE_RATE = 16000  # Vonage uses 16kHz Linear PCM
OPENAI_SAMPLE_RATE = 24000  # OpenAI Realtime API uses 24kHz

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VonageAgent")

# ============================================================================
# ELEVENLABS CLIENT
# ============================================================================

eleven_client = None
if CONFIG.get("USE_ELEVENLABS"):
    eleven_client = ElevenLabs(api_key=CONFIG["ELEVENLABS_API_KEY"])
    logger.info("ElevenLabs client initialized")

# Initialize Google TTS client  
google_tts_client = None
if CONFIG.get("USE_GOOGLE_TTS"):
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CONFIG["GOOGLE_CREDENTIALS_PATH"]
        google_tts_client = texttospeech.TextToSpeechClient()
        logger.info("Google Cloud TTS client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Google TTS: {e}")

# Initialize Cartesia client (real-time voice streaming)
cartesia_client = None
if CONFIG.get("USE_CARTESIA") and CONFIG.get("CARTESIA_API_KEY"):
    try:
        cartesia_client = Cartesia(api_key=CONFIG["CARTESIA_API_KEY"])
        logger.info("Cartesia AI client initialized - Real-time voice streaming enabled")
    except Exception as e:
        logger.warning(f"Failed to initialize Cartesia: {e}")

# Initialize PlayHT client
playht_client = None
playht_api_key = None
playht_user_id = None
if CONFIG.get("USE_PLAYHT"):
    try:
        playht_user_id = CONFIG["PLAYHT_USER_ID"]
        playht_api_key = CONFIG["PLAYHT_API_KEY"]
        # Don't initialize client here - will use REST API directly
        logger.info("PlayHT TTS configured with API key")
    except Exception as e:
        logger.warning(f"Failed to configure PlayHT: {e}")

# ============================================================================
# DATABASE SETUP
# ============================================================================

def get_db_connection():
    """Get a database connection with proper settings for concurrency"""
    conn = sqlite3.connect('call_logs.db', timeout=30, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
    conn.execute('PRAGMA busy_timeout=30000')  # 30 second timeout
    return conn

def init_database():
    """Initialize SQLite database for call logs"""
    conn = get_db_connection()
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
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Add user_id column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE calls ADD COLUMN user_id INTEGER')
    except:
        pass  # Column already exists
    
    # Add status column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE calls ADD COLUMN status TEXT DEFAULT "active"')
    except:
        pass  # Column already exists
    
    # Add average_response_time column if doesn't exist
    try:
        cursor.execute('ALTER TABLE calls ADD COLUMN average_response_time REAL')
    except:
        pass  # Column already exists
    
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
    
    # Add user_id to appointments if doesn't exist
    try:
        cursor.execute('ALTER TABLE appointments ADD COLUMN user_id INTEGER')
    except:
        pass
    
    # Create account_settings table for minutes tracking (per user)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            minutes_remaining INTEGER DEFAULT 60,
            total_minutes_purchased INTEGER DEFAULT 60,
            voice TEXT DEFAULT 'shimmer',
            use_elevenlabs INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Add voice column if doesn't exist
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN voice TEXT DEFAULT "shimmer"')
    except:
        pass
    
    # Add use_elevenlabs column if doesn't exist
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN use_elevenlabs INTEGER DEFAULT 0')
    except:
        pass
    
    # Add phone_number column if doesn't exist
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN phone_number TEXT')
    except:
        pass
    
    # Add response_latency column if doesn't exist (in milliseconds)
    # AI-optimized default: 300ms balances speed and natural conversation
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN response_latency INTEGER DEFAULT 300')
    except:
        pass
    
    # Add voice_provider column (openai, elevenlabs, cartesia, google)
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN voice_provider TEXT DEFAULT "openai"')
    except:
        pass
    
    # Add cartesia_voice_id column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN cartesia_voice_id TEXT DEFAULT "a0e99841-438c-4a64-b679-ae501e7d6091"')
    except:
        pass
    
    # Add google_voice column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN google_voice TEXT DEFAULT "en-GB-Neural2-A"')
    except:
        pass
    
    # Add agent_name column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN agent_name TEXT DEFAULT "Judie"')
    except:
        pass
    
    # Add business_info column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN business_info TEXT DEFAULT ""')
    except:
        pass
    
    # Add agent_personality column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN agent_personality TEXT DEFAULT "Friendly and professional. Keep responses brief and conversational."')
    except:
        pass
    
    # Add agent_instructions column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN agent_instructions TEXT DEFAULT "Answer questions about the business. Take messages if needed."')
    except:
        pass
    
    # Add calendar_booking_enabled column
    try:
        cursor.execute('ALTER TABLE account_settings ADD COLUMN calendar_booking_enabled INTEGER DEFAULT 1')
    except:
        pass
    
    # Create global_settings table for admin-controlled settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            global_instructions TEXT DEFAULT '',
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT DEFAULT 'admin'
        )
    ''')
    
    # Initialize global_settings with default empty instructions
    cursor.execute('INSERT OR IGNORE INTO global_settings (id, global_instructions) VALUES (1, "")')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# ============================================================================
# AUTHENTICATION HELPER
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """
    Validates session token and returns user_id.
    Returns None if invalid or expired.
    """
    if not authorization or not authorization.startswith('Bearer '):
        return None
    
    session_token = authorization[7:]  # Remove 'Bearer ' prefix
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.user_id, s.expires_at 
        FROM sessions s
        WHERE s.session_token = ?
    ''', (session_token,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    user_id, expires_at = result
    
    # Check if session is expired
    if datetime.fromisoformat(expires_at) < datetime.now():
        return None
    
    return user_id

# ============================================================================
# MINUTES TRACKING
# ============================================================================

class MinutesTracker:
    """Handles account minutes tracking per user"""
    
    @staticmethod
    def get_minutes_remaining(user_id: int) -> int:
        """Get remaining minutes for user"""
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT minutes_remaining FROM account_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    @staticmethod
    def has_minutes(user_id: int) -> bool:
        """Check if user has minutes available"""
        return MinutesTracker.get_minutes_remaining(user_id) > 0
    
    @staticmethod
    def add_minutes(user_id: int, amount: int) -> int:
        """Add minutes to user account (e.g., when purchasing)"""
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE account_settings 
            SET minutes_remaining = minutes_remaining + ?,
                total_minutes_purchased = total_minutes_purchased + ?,
                last_updated = ?
            WHERE user_id = ?
        ''', (amount, amount, datetime.now().isoformat(), user_id))
        conn.commit()
        
        cursor.execute('SELECT minutes_remaining FROM account_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    @staticmethod
    def deduct_minutes(user_id: int, call_duration_seconds: int):
        """Deduct minutes after a call completes"""
        minutes_used = max(1, int(call_duration_seconds / 60))  # Round up to nearest minute
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE account_settings 
            SET minutes_remaining = MAX(0, minutes_remaining - ?),
                last_updated = ?
            WHERE user_id = ?
        ''', (minutes_used, datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        logger.info(f"Deducted {minutes_used} minute(s) from user {user_id} account")

# ============================================================================
# CALL LOGGING
# ============================================================================

class CallLogger:
    """Handles call logging and summarization"""
    
    @staticmethod
    def log_call_start(call_uuid: str, caller: str, called: str, user_id: Optional[int] = None):
        """Log when a call starts"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO calls (call_uuid, caller_number, called_number, start_time, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (call_uuid, caller, called, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def log_call_end(call_uuid: str, transcript: str = "", avg_response_time: Optional[float] = None):
        """Log when a call ends"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get start time and user_id to calculate duration and deduct minutes
        cursor.execute('SELECT start_time, user_id FROM calls WHERE call_uuid = ?', (call_uuid,))
        result = cursor.fetchone()
        
        if result:
            start_time = datetime.fromisoformat(result[0])
            user_id = result[1]
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            cursor.execute('''
                UPDATE calls 
                SET end_time = ?, duration = ?, transcript = ?, average_response_time = ?
                WHERE call_uuid = ?
            ''', (end_time.isoformat(), duration, transcript, avg_response_time, call_uuid))
            
            conn.commit()
            
            # Deduct minutes from user's account based on call duration
            if user_id:
                MinutesTracker.deduct_minutes(user_id, duration)
        
        conn.close()
    
    @staticmethod
    async def generate_summary(call_uuid: str):
        """Generate AI summary of the call using OpenAI"""
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT transcript, caller_number FROM calls WHERE call_uuid = ?', (call_uuid,))
        result = cursor.fetchone()
        
        if result and result[0]:
            transcript = result[0]
            caller_number = result[1] or "Unknown"
            
            try:
                # Use AI to summarize the conversation
                import openai as openai_module
                
                summary_provider = CONFIG.get("SUMMARY_PROVIDER", "openai")
                
                if summary_provider == "deepseek" and CONFIG.get("DEEPSEEK_API_KEY"):
                    # Use DeepSeek - 15x cheaper!
                    client = openai_module.OpenAI(
                        api_key=CONFIG['DEEPSEEK_API_KEY'],
                        base_url="https://api.deepseek.com"
                    )
                    model = "deepseek-chat"
                else:
                    # Use OpenAI
                    client = openai_module.OpenAI(
                        api_key=CONFIG['OPENAI_API_KEY']
                    )
                    model = CONFIG.get("SUMMARY_MODEL", "gpt-4o-mini")
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes phone conversations. Provide a brief, clear summary of what the caller wanted and what was discussed."},
                        {"role": "user", "content": f"Summarize this phone conversation:\n\n{transcript}"}
                    ],
                    max_tokens=150
                )
                
                summary = response.choices[0].message.content.strip()
                logger.info(f"[{call_uuid}] Summary generated using {summary_provider}/{model}")
                
                # Save summary to database
                cursor.execute('UPDATE calls SET summary = ? WHERE call_uuid = ?', (summary, call_uuid))
                conn.commit()
                
                logger.info(f"[{call_uuid}] Generated summary: {summary}")
                
            except Exception as e:
                logger.error(f"[{call_uuid}] Failed to generate summary: {e}")
                import traceback
                logger.error(f"[{call_uuid}] Traceback: {traceback.format_exc()}")
                # Set a fallback summary so it doesn't stay as "Processing..."
                summary = f"Call about: (summary generation failed)"
                cursor.execute('UPDATE calls SET summary = ? WHERE call_uuid = ?', (summary, call_uuid))
                conn.commit()
        else:
            logger.warning(f"[{call_uuid}] No transcript found for summary generation")
        
        conn.close()
    
    @staticmethod
    def get_recent_calls(limit: int = 20, user_id: Optional[int] = None) -> List[Dict]:
        """Get recent call logs for a specific user"""
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT c.call_uuid, c.caller_number, c.called_number, c.start_time, 
                       c.end_time, c.duration, c.transcript, c.summary, c.status,
                       (SELECT COUNT(*) FROM appointments WHERE call_uuid = c.call_uuid AND user_id = ?) as has_appointment
                FROM calls c
                WHERE c.user_id = ?
                ORDER BY c.start_time DESC
                LIMIT ?
            ''', (user_id, user_id, limit))
        else:
            cursor.execute('''
                SELECT c.call_uuid, c.caller_number, c.called_number, c.start_time, 
                       c.end_time, c.duration, c.transcript, c.summary, c.status,
                       (SELECT COUNT(*) FROM appointments WHERE call_uuid = c.call_uuid) as has_appointment
                FROM calls c
                ORDER BY c.start_time DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        calls = []
        for row in rows:
            calls.append({
                "call_uuid": row[0],
                "caller_number": row[1],
                "called_number": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "duration": row[5],
                "transcript": row[6],
                "summary": row[7] or "Processing...",
                "status": row[8] or "active",
                "has_appointment": row[9] > 0
            })
        
        return calls

# ============================================================================
# CALL SESSION HANDLER
# ============================================================================

class CallSession:
    """Handles a single phone call, bridging Vonage WebSocket to OpenAI Realtime API"""
    
    def __init__(self, call_uuid: str, caller: str = "", called: str = ""):
        self.call_uuid = call_uuid
        self.caller = caller
        self.caller_number = caller  # Store for appointment booking
        self.called = called
        self.openai_ws = None
        self.vonage_ws: Optional[WebSocket] = None
        self.is_active = True
        self._openai_task = None
        self.transcript_parts = []  # Store conversation transcript
        self._last_speech_time = None  # Track last time caller spoke
        self._timeout_task = None  # Task for timeout checking
        self._agent_speaking = False  # Track if agent is currently speaking
        
        # Response time tracking
        self._speech_stopped_time = None  # Timestamp when user stops speaking
        self._response_times = []  # List of response latencies in milliseconds
        self.user_id = None  # Will be set from caller lookup
        
        # ElevenLabs streaming optimization
        self._elevenlabs_text_buffer = ""  # Buffer for accumulating text
        self._elevenlabs_sent = False  # Track if we've already sent audio for this response
        
    async def connect_to_openai(self):
        """Establish connection to OpenAI Realtime API"""
        # Retry up to 3 times
        for attempt in range(3):
            try:
                # Import here to handle missing dependency gracefully
                from websockets import connect
                
                url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
                api_key = CONFIG['OPENAI_API_KEY']
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "OpenAI-Beta": "realtime=v1"
                }
                
                logger.info(f"[{self.call_uuid}] Connecting to OpenAI Realtime API (attempt {attempt + 1})...")
                logger.info(f"[{self.call_uuid}] API Key starts with: {api_key[:20]}... ends with: ...{api_key[-10:]}")
                self.openai_ws = await asyncio.wait_for(
                    connect(url, additional_headers=headers),
                    timeout=10.0
                )
                
                # Configure the session with current instructions
                # Build comprehensive instructions from all config fields
                instructions_parts = [f"You are {CONFIG['AGENT_NAME']}, a phone assistant."]
                
                # Add global instructions first (applies to all accounts)
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT global_instructions FROM global_settings WHERE id = 1')
                    result = cursor.fetchone()
                    conn.close()
                    if result and result[0]:
                        instructions_parts.append(f"\n🌐 GLOBAL INSTRUCTIONS (MANDATORY FOR ALL AGENTS):\n{result[0]}")
                        logger.info(f"[{self.call_uuid}] Applied global instructions")
                except Exception as e:
                    logger.warning(f"[{self.call_uuid}] Could not load global instructions: {e}")
                
                if CONFIG.get("BUSINESS_INFO"):
                    instructions_parts.append(f"\nBUSINESS INFORMATION:\n{CONFIG['BUSINESS_INFO']}")
                
                if CONFIG.get("AGENT_PERSONALITY"):
                    instructions_parts.append(f"\nPERSONALITY & TONE:\n{CONFIG['AGENT_PERSONALITY']}")
                
                if CONFIG.get("AGENT_INSTRUCTIONS"):
                    instructions_parts.append(f"\nADDITIONAL INSTRUCTIONS:\n{CONFIG['AGENT_INSTRUCTIONS']}")
                
                # Natural, friendly responses - not too short, not too long
                instructions_parts.append("\nRESPONSE STYLE:")
                instructions_parts.append("- Be warm, friendly, and professional")
                instructions_parts.append("- Keep responses natural and conversational (3-5 sentences)")
                instructions_parts.append("- Be helpful and polite - never abrupt or curt")
                instructions_parts.append("- Provide clear, complete answers without rambling")
                instructions_parts.append("- NEVER include meta-commentary like 'Assistant:', 'mode:', or stage directions")
                instructions_parts.append("- Speak ONLY as the receptionist - no prefixes, labels, or formatting")
                instructions_parts.append("\nYou can book appointments using the book_appointment function when a caller requests one.")
                instructions_parts.append("\nIf a time slot is already booked, the system will return alternative available times - offer these alternatives to the caller.")
                
                current_instructions = "\n".join(instructions_parts)
                logger.info(f"[{self.call_uuid}] Using instructions: {current_instructions[:100]}...")
                
                # Get user's voice preference and response latency from account_settings
                # When ElevenLabs is enabled, use 'shimmer' as safe fallback for OpenAI session
                # (ElevenLabs will replace the audio anyway)
                response_latency = 300  # AI-optimized default (balances speed and natural pauses)
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT response_latency FROM account_settings WHERE user_id = ?', (getattr(self, 'user_id', None),))
                    row = cursor.fetchone()
                    conn.close()
                    if row and row[0] is not None:
                        response_latency = row[0]
                        logger.info(f"[{self.call_uuid}] Using custom response latency: {response_latency}ms (user-configured)")
                except Exception as e:
                    logger.warning(f"[{self.call_uuid}] Could not load response latency, using AI-optimized default 300ms: {e}")
                
                if getattr(self, 'use_elevenlabs', False):
                    selected_voice = 'shimmer'
                    logger.info(f"[{self.call_uuid}] ⚡ ElevenLabs ENABLED (eleven_turbo_v2_5) - Balanced Speed")
                    logger.info(f"[{self.call_uuid}] ⚖️ BALANCED MODE: silence={response_latency}ms, prefix=300ms, tokens=300, temp=0.8")
                else:
                    selected_voice = getattr(self, 'user_voice', 'shimmer')
                    logger.info(f"[{self.call_uuid}] Using OpenAI voice: {selected_voice}")
                    logger.info(f"[{self.call_uuid}] ⚖️ BALANCED MODE: silence={response_latency}ms, prefix=300ms, tokens=300, temp=0.8")
                
                # Get voice provider to determine if we need OpenAI audio
                voice_provider = getattr(self, 'voice_provider', 'openai')
                
                # Configure modalities based on voice provider
                # If using Cartesia, ElevenLabs, Google, or PlayHT, we only need text from OpenAI (no audio)
                if voice_provider in ['cartesia', 'elevenlabs', 'google', 'playht']:
                    modalities = ["text"]  # Text only - external TTS will handle audio
                    logger.info(f"[{self.call_uuid}] Using {voice_provider} for TTS - OpenAI text-only mode")
                    # For external TTS: higher threshold to prevent false triggers/hallucinations
                    turn_detection_config = {
                        "type": "server_vad",
                        "threshold": 0.7,  # Higher threshold to prevent picking up noise/echo
                        "prefix_padding_ms": 300,  # Standard padding
                        "silence_duration_ms": max(response_latency, 500),  # Minimum 500ms for faster responses
                        "create_response": True
                    }
                    logger.info(f"[{self.call_uuid}] {voice_provider.upper()} TTS VAD: threshold=0.7, silence={max(response_latency, 500)}ms")
                else:
                    modalities = ["text", "audio"]  # OpenAI handles both text and audio
                    # For OpenAI voice: need lower threshold for better conversational flow
                    turn_detection_config = {
                        "type": "server_vad",
                        "threshold": 0.5,  # Lower threshold for more responsive conversation
                        "prefix_padding_ms": 200,  # Less padding for faster response
                        "silence_duration_ms": response_latency,  # Use configured latency
                        "create_response": True
                    }
                    logger.info(f"[{self.call_uuid}] OpenAI voice VAD: threshold=0.5, silence={response_latency}ms")
                
                await self.openai_ws.send(json.dumps({
                    "type": "session.update",
                    "session": {
                        "modalities": modalities,
                        "instructions": current_instructions,
                        "voice": selected_voice,
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                            "model": "whisper-1"
                        },
                        "turn_detection": turn_detection_config,
                        "max_response_output_tokens": 300,  # Balanced length
                        "temperature": 0.8,  # Faster generation
                        "tools": [
                            {
                                "type": "function",
                                "name": "book_appointment",
                                "description": "Book an appointment for the caller. Use this when someone wants to schedule a meeting or appointment.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "date": {
                                            "type": "string",
                                            "description": "The date of the appointment in YYYY-MM-DD format"
                                        },
                                        "time": {
                                            "type": "string",
                                            "description": "The time of the appointment in HH:MM format (24-hour)"
                                        },
                                        "customer_name": {
                                            "type": "string",
                                            "description": "The caller's name"
                                        },
                                        "customer_phone": {
                                            "type": "string",
                                            "description": "The caller's phone number"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Notes about the appointment"
                                        }
                                    },
                                    "required": ["date", "time", "customer_name"]
                                }
                            }
                        ],
                        "tool_choice": "auto"
                    }
                }))
                
                logger.info(f"[{self.call_uuid}] Connected to OpenAI successfully")
                return True
                
            except asyncio.TimeoutError:
                logger.warning(f"[{self.call_uuid}] Connection timeout, retrying...")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"[{self.call_uuid}] Failed to connect to OpenAI (attempt {attempt + 1}): {e}")
                await asyncio.sleep(0.5)
        
        return False
    
    async def send_audio_to_openai(self, audio_data: bytes):
        """Send audio from Vonage to OpenAI (with resampling)"""
        if not self.openai_ws or not self.is_active:
            return
            
        try:
            # Convert bytes to numpy array (16-bit PCM from Vonage)
            audio_16k = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # Resample from 16kHz (Vonage) to 24kHz (OpenAI)
            num_samples = int(len(audio_16k) * OPENAI_SAMPLE_RATE / VONAGE_SAMPLE_RATE)
            audio_24k = signal.resample(audio_16k, num_samples)
            
            # Convert back to int16
            audio_int16 = (audio_24k * 32767).astype(np.int16)
            
            # Send to OpenAI
            await self.openai_ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(audio_int16.tobytes()).decode()
            }))
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error sending audio to OpenAI: {e}")
    
    async def receive_from_openai(self):
        """Receive responses from OpenAI and forward to Vonage"""
        try:
            async for message in self.openai_ws:
                if not self.is_active:
                    break
                    
                event = json.loads(message)
                event_type = event.get("type", "")
                
                # Debug: log all events when using text-only mode
                voice_provider = getattr(self, 'voice_provider', 'openai')
                if voice_provider in ['cartesia', 'elevenlabs', 'google'] and event_type.startswith('response'):
                    logger.info(f"[{self.call_uuid}] 🔍 Event: {event_type} | Data: {event}")
                
                if event_type == "session.created":
                    logger.info(f"[{self.call_uuid}] OpenAI session created")
                    
                elif event_type == "session.updated":
                    logger.info(f"[{self.call_uuid}] OpenAI session configured")
                    # Start timeout monitoring
                    self._last_speech_time = asyncio.get_event_loop().time()
                    self._timeout_task = asyncio.create_task(self._monitor_timeout())
                    
                elif event_type == "input_audio_buffer.speech_started":
                    logger.debug(f"[{self.call_uuid}] Caller speaking...")
                    self._last_speech_time = asyncio.get_event_loop().time()
                    # If agent is speaking, cancel current response to allow interruption
                    if self._agent_speaking:
                        logger.info(f"[{self.call_uuid}] Caller interrupted - canceling response")
                        await self.openai_ws.send(json.dumps({"type": "response.cancel"}))
                        self._agent_speaking = False
                    
                elif event_type == "input_audio_buffer.speech_stopped":
                    logger.debug(f"[{self.call_uuid}] Caller stopped speaking")
                    self._last_speech_time = asyncio.get_event_loop().time()
                    # Mark time when user stops speaking for latency tracking
                    self._speech_stopped_time = asyncio.get_event_loop().time()
                    
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    logger.info(f"[{self.call_uuid}] 📞 Caller: {transcript}")
                    self.transcript_parts.append(f"Caller: {transcript}")
                    self._last_speech_time = asyncio.get_event_loop().time()
                
                elif event_type == "response.audio.delta":
                    # Agent is speaking
                    self._agent_speaking = True
                    
                    # Track response latency if we have a speech_stopped timestamp
                    if self._speech_stopped_time is not None:
                        response_latency_ms = (asyncio.get_event_loop().time() - self._speech_stopped_time) * 1000
                        self._response_times.append(response_latency_ms)
                        logger.debug(f"[{self.call_uuid}] Response latency: {response_latency_ms:.0f}ms")
                        self._speech_stopped_time = None  # Reset for next turn
                    
                    # Get user's voice provider preference
                    voice_provider = getattr(self, 'voice_provider', 'openai')
                    
                    # Only use OpenAI audio if provider is 'openai'
                    audio_b64 = event.get("delta", "")
                    if audio_b64 and self.vonage_ws:
                        # Store for potential fallback
                        if not hasattr(self, '_openai_audio_chunks'):
                            self._openai_audio_chunks = []
                        self._openai_audio_chunks.append(audio_b64)
                        
                        # Only send OpenAI audio immediately if that's the selected provider
                        if voice_provider == 'openai':
                            await self._send_audio_to_vonage(audio_b64)
                        
                elif event_type == "response.audio_transcript.delta":
                    # Real-time transcript - start ElevenLabs when we have a complete sentence
                    delta_text = event.get("delta", "")
                    if delta_text and getattr(self, 'use_elevenlabs', False) and eleven_client:
                        self._elevenlabs_text_buffer += delta_text
                        
                        # Only start generating when we have a complete sentence (40+ chars AND ends with punctuation)
                        buffer_ends_with_punctuation = self._elevenlabs_text_buffer.strip().endswith(('.', '!', '?'))
                        buffer_long_enough = len(self._elevenlabs_text_buffer) >= 40
                        
                        if not self._elevenlabs_sent and buffer_ends_with_punctuation and buffer_long_enough:
                            # Generate as soon as we have one complete sentence
                            asyncio.create_task(self._send_elevenlabs_audio(self._elevenlabs_text_buffer))
                            self._elevenlabs_sent = True
                            logger.info(f"[{self.call_uuid}] ⚡ FAST MODE: Started ElevenLabs with complete sentence ({len(self._elevenlabs_text_buffer)} chars)")
                    
                elif event_type == "response.text.delta":
                    # Text response when in text-only mode (Cartesia/ElevenLabs)
                    text = event.get("delta", "")
                    if not hasattr(self, '_text_response_buffer'):
                        self._text_response_buffer = ""
                    self._text_response_buffer += text
                    
                elif event_type == "response.text.done":
                    # Complete text response - generate audio with Cartesia/ElevenLabs
                    transcript = event.get("text", "")
                    if not transcript and hasattr(self, '_text_response_buffer'):
                        transcript = self._text_response_buffer
                    
                    logger.info(f"[{self.call_uuid}] 🤖 {CONFIG['AGENT_NAME']}: {transcript}")
                    self.transcript_parts.append(f"{CONFIG['AGENT_NAME']}: {transcript}")
                    self._agent_speaking = False
                    
                    # Get user's voice provider preference
                    voice_provider = getattr(self, 'voice_provider', 'openai')
                    
                    # Generate audio with the selected voice provider
                    if voice_provider == 'cartesia' and cartesia_client and transcript:
                        await self._send_cartesia_audio(transcript)
                    elif voice_provider == 'elevenlabs' and eleven_client and transcript:
                        await self._send_elevenlabs_audio(transcript)
                    elif voice_provider == 'google' and google_tts_client and transcript:
                        await self._send_google_tts_audio(transcript)
                    elif voice_provider == 'playht' and playht_api_key and transcript:
                        await self._send_playht_audio(transcript)
                    
                    # Reset buffer
                    self._text_response_buffer = ""
                    
                elif event_type == "response.audio_transcript.done":
                    # Audio response when in audio mode (OpenAI voice)
                    transcript = event.get("transcript", "")
                    logger.info(f"[{self.call_uuid}] 🤖 {CONFIG['AGENT_NAME']}: {transcript}")
                    self.transcript_parts.append(f"{CONFIG['AGENT_NAME']}: {transcript}")
                    self._agent_speaking = False  # Agent finished speaking
                    
                    # Get user's voice provider preference
                    voice_provider = getattr(self, 'voice_provider', 'openai')
                    
                    # Route to the correct voice provider based on user preference
                    if voice_provider == 'cartesia' and cartesia_client and transcript:
                        success = await self._send_cartesia_audio(transcript)
                        if not success and hasattr(self, '_openai_audio_chunks'):
                            logger.warning(f"[{self.call_uuid}] Cartesia failed, falling back to OpenAI audio")
                            for audio_chunk in self._openai_audio_chunks:
                                await self._send_audio_to_vonage(audio_chunk)
                        self._openai_audio_chunks = []
                    elif voice_provider == 'elevenlabs' and eleven_client and transcript:
                        # Only generate if we haven't already started (early generation)
                        if not self._elevenlabs_sent:
                            logger.info(f"[{self.call_uuid}] Using ElevenLabs for complete response: {transcript[:50]}...")
                            success = await self._send_elevenlabs_audio(transcript)
                            if not success and hasattr(self, '_openai_audio_chunks'):
                                logger.warning(f"[{self.call_uuid}] ElevenLabs failed, falling back to OpenAI audio")
                                for audio_chunk in self._openai_audio_chunks:
                                    await self._send_audio_to_vonage(audio_chunk)
                        else:
                            logger.info(f"[{self.call_uuid}] ⚡ ElevenLabs already sent early - skipping duplicate")
                        
                        # Reset for next response
                        self._elevenlabs_text_buffer = ""
                        self._elevenlabs_sent = False
                        self._openai_audio_chunks = []
                    elif voice_provider == 'google' and google_tts_client and transcript:
                        success = await self._send_google_tts_audio(transcript)
                        if not success and hasattr(self, '_openai_audio_chunks'):
                            logger.warning(f"[{self.call_uuid}] Google TTS failed, falling back to OpenAI audio")
                            for audio_chunk in self._openai_audio_chunks:
                                await self._send_audio_to_vonage(audio_chunk)
                        self._openai_audio_chunks = []
                    elif voice_provider == 'playht' and playht_api_key and transcript:
                        success = await self._send_playht_audio(transcript)
                        if not success and hasattr(self, '_openai_audio_chunks'):
                            logger.warning(f"[{self.call_uuid}] PlayHT failed, falling back to OpenAI audio")
                            for audio_chunk in self._openai_audio_chunks:
                                await self._send_audio_to_vonage(audio_chunk)
                        self._openai_audio_chunks = []
                    else:
                        # Use OpenAI audio (already sent in real-time)
                        logger.info(f"[{self.call_uuid}] Using OpenAI audio (already streamed)")
                        self._openai_audio_chunks = []
                    
                elif event_type == "response.done":
                    logger.debug(f"[{self.call_uuid}] Response complete")
                
                elif event_type == "response.function_call_arguments.done":
                    # Function call from AI
                    call_id = event.get("call_id")
                    function_name = event.get("name")
                    arguments = json.loads(event.get("arguments", "{}"))
                    
                    logger.info(f"[{self.call_uuid}] Function call: {function_name} with args: {arguments}")
                    
                    if function_name == "book_appointment":
                        await self._handle_book_appointment(call_id, arguments)
                    
                elif event_type == "error":
                    error_msg = event.get("error", {}).get("message", "Unknown error")
                    logger.error(f"[{self.call_uuid}] OpenAI error: {error_msg}")
                    
        except Exception as e:
            if self.is_active:
                logger.error(f"[{self.call_uuid}] Error receiving from OpenAI: {e}")
    
    async def _send_audio_to_vonage(self, audio_b64: str):
        """Send audio from OpenAI to Vonage (with resampling)"""
        try:
            # Decode base64 audio (24kHz from OpenAI)
            audio_24k = np.frombuffer(
                base64.b64decode(audio_b64), 
                dtype=np.int16
            ).astype(np.float32) / 32767.0
            
            # Resample from 24kHz (OpenAI) to 16kHz (Vonage)
            num_samples = int(len(audio_24k) * VONAGE_SAMPLE_RATE / OPENAI_SAMPLE_RATE)
            audio_16k = signal.resample(audio_24k, num_samples)
            
            # Convert to int16 bytes
            audio_bytes = (audio_16k * 32767).astype(np.int16).tobytes()
            
            # Send to Vonage WebSocket
            await self.vonage_ws.send_bytes(audio_bytes)
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error sending audio to Vonage: {e}")
    
    async def _send_cartesia_audio(self, text: str) -> bool:
        """Generate audio using Cartesia WebSocket streaming (real-time, low latency) and send to Vonage."""
        try:
            # Clean up text - remove extra whitespace/newlines that can cause audio issues
            text = text.strip()
            if not text:
                logger.warning(f"[{self.call_uuid}] Empty text for Cartesia, skipping")
                return False
                
            logger.info(f"[{self.call_uuid}] 🎙️ Starting Cartesia real-time audio for: {text[:50]}...")
            
            # Get user's selected Cartesia voice ID
            voice_id = getattr(self, 'cartesia_voice_id', 'a0e99841-438c-4a64-b679-ae501e7d6091')
            logger.info(f"[{self.call_uuid}] Using Cartesia voice ID: {voice_id}")
            
            # Use WebSocket for real-time streaming
            ws = cartesia_client.tts.websocket()
            
            # Collect all audio chunks first to ensure smooth continuous playback
            audio_chunks = []
            for chunk in ws.send(
                model_id="sonic-english",
                transcript=text,
                voice={
                    "mode": "id",
                    "id": voice_id,
                },
                output_format={
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 16000,
                },
                stream=True
            ):
                if chunk.audio:
                    audio_chunks.append(chunk.audio)
            
            # Combine into single continuous stream
            full_audio = b''.join(audio_chunks)
            
            if not full_audio:
                logger.warning(f"[{self.call_uuid}] Cartesia returned no audio")
                return False
            
            logger.info(f"[{self.call_uuid}] Generated {len(full_audio)} bytes, sending to Vonage...")
            
            # Send the complete audio as one stream for smooth playback
            if self.vonage_ws and self.is_active:
                await self.vonage_ws.send_bytes(full_audio)
            
            logger.info(f"[{self.call_uuid}] ✅ Cartesia streaming audio sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Cartesia audio generation error: {e}")
            return False
    
    async def _send_elevenlabs_audio(self, text: str) -> bool:
        """Generate audio using ElevenLabs and send to Vonage. Returns True on success."""
        try:
            logger.info(f"[{self.call_uuid}] 🎙️ Starting ElevenLabs audio generation for: {text[:50]}...")
            
            if not eleven_client:
                logger.error(f"[{self.call_uuid}] ElevenLabs client not initialized!")
                return False
            
            # Get user's selected ElevenLabs voice (default to Bella if not set)
            voice_id = getattr(self, 'elevenlabs_voice_id', 'EXAVITQu4vr4xnSDxMaL')
            logger.info(f"[{self.call_uuid}] Using ElevenLabs voice ID: {voice_id}")
            
            # Generate audio using ElevenLabs with user's selected voice
            # Using eleven_turbo_v2_5 for optimal speed (AI-optimized)
            # Streaming enabled for concurrent processing
            logger.info(f"[{self.call_uuid}] Calling ElevenLabs API (turbo model)...")
            audio_generator = eleven_client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",  # Fastest model available
                output_format="pcm_16000",  # Request PCM at 16kHz directly
                optimize_streaming_latency=3,  # Balanced streaming optimization
                voice_settings=VoiceSettings(
                    stability=0.4,  # Balanced quality/speed
                    similarity_boost=0.6,  # Better voice quality
                    style=0.0,
                    use_speaker_boost=True  # Better voice quality
                )
            )
            
            logger.info(f"[{self.call_uuid}] Collecting audio chunks from ElevenLabs...")
            # Collect audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            # Combine all chunks
            audio_data = b''.join(audio_chunks)
            logger.info(f"[{self.call_uuid}] ElevenLabs generated {len(audio_data)} bytes of audio")
            
            if len(audio_data) == 0:
                logger.error(f"[{self.call_uuid}] ElevenLabs returned empty audio!")
                return False
            
            # Audio is already PCM 16kHz (as requested)
            # Convert to int16 numpy array, then to bytes (matching OpenAI format)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Send in the same way as OpenAI audio - all at once
            if self.vonage_ws and self.is_active:
                await self.vonage_ws.send_bytes(audio_array.tobytes())
                logger.info(f"[{self.call_uuid}] ✅ ElevenLabs audio sent successfully ({len(audio_data)} bytes)")
            else:
                logger.warning(f"[{self.call_uuid}] Vonage WS disconnected, cannot send audio")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Error generating/sending ElevenLabs audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _send_google_tts_audio(self, text: str) -> bool:
        """Generate audio using Google Cloud TTS and send to Vonage. Returns True on success."""
        try:
            logger.info(f"[{self.call_uuid}] 🎙️ Starting Google Cloud TTS audio generation for: {text[:50]}...")
            
            if not google_tts_client:
                logger.error(f"[{self.call_uuid}] Google TTS client not initialized!")
                return False
            
            # Clean the text - remove stage directions, formatting, and unwanted markers
            cleaned_text = text
            
            # Remove content in square brackets [like this]
            import re
            cleaned_text = re.sub(r'\[.*?\]', '', cleaned_text)
            
            # Remove content in parentheses that looks like stage directions
            cleaned_text = re.sub(r'\([a-z\s]+\)', '', cleaned_text, flags=re.IGNORECASE)
            
            # Remove asterisks used for actions *like this*
            cleaned_text = re.sub(r'\*.*?\*', '', cleaned_text)
            
            # Remove markdown formatting
            cleaned_text = re.sub(r'\*\*|__|~~', '', cleaned_text)
            
            # Remove common LLM artifacts and meta-commentary
            # Remove phrases like "Assistant:", "AI:", "wrong assistant content", etc.
            cleaned_text = re.sub(r'^(Assistant|AI|Human|User|System):\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'wrong\s+(assistant|content|response)', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'(assistant|AI)\s+(content|response|message)', '', cleaned_text, flags=re.IGNORECASE)
            
            # Remove "mode:" prefixes
            cleaned_text = re.sub(r'mode:\s*\w+', '', cleaned_text, flags=re.IGNORECASE)
            
            # Remove multiple spaces and trim
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            # Remove any leading/trailing punctuation that might be left over
            cleaned_text = cleaned_text.strip('.,;:- ')
            
            if cleaned_text != text:
                logger.info(f"[{self.call_uuid}] Cleaned text from '{text[:100]}' to '{cleaned_text[:100]}'")
            
            if not cleaned_text:
                logger.warning(f"[{self.call_uuid}] Text became empty after cleaning, skipping TTS")
                return False
            
            # Get user's selected Google voice (default to en-GB-Neural2-A if not set)
            voice_name = getattr(self, 'google_voice', 'en-GB-Neural2-A')
            logger.info(f"[{self.call_uuid}] Using Google voice: {voice_name}")
            
            # Set up synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
            
            # Set up voice parameters
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-GB",
                name=voice_name
            )
            
            # Set up audio configuration (PCM 16kHz for Vonage)
            # Increase speaking rate slightly for faster responses
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                speaking_rate=1.1,  # 10% faster for quicker responses
                pitch=0.0
            )
            
            logger.info(f"[{self.call_uuid}] Calling Google Cloud TTS API...")
            # Perform TTS request
            response = google_tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            audio_data = response.audio_content
            logger.info(f"[{self.call_uuid}] Google TTS generated {len(audio_data)} bytes of audio")
            
            if len(audio_data) == 0:
                logger.error(f"[{self.call_uuid}] Google TTS returned empty audio!")
                return False
            
            # Audio is already PCM 16kHz
            # Convert to int16 numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Send all at once (like OpenAI/ElevenLabs)
            if self.vonage_ws and self.is_active:
                await self.vonage_ws.send_bytes(audio_array.tobytes())
                logger.info(f"[{self.call_uuid}] ✅ Google TTS audio sent successfully ({len(audio_data)} bytes)")
            else:
                logger.warning(f"[{self.call_uuid}] Vonage WS disconnected, cannot send audio")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Error generating/sending Google TTS audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _send_playht_audio(self, text: str) -> bool:
        """Generate audio using PlayHT API v2 and send to Vonage. Returns True on success."""
        try:
            logger.info(f"[{self.call_uuid}] 🎙️ Starting PlayHT audio generation for: {text[:50]}...")
            
            if not playht_api_key or not playht_user_id:
                logger.error(f"[{self.call_uuid}] PlayHT credentials not configured!")
                return False
            
            # Clean the text like we do for Google TTS
            import re
            cleaned_text = re.sub(r'\[.*?\]', '', text)
            cleaned_text = re.sub(r'\([a-z\s]+\)', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\*.*?\*', '', cleaned_text)
            cleaned_text = re.sub(r'\*\*|__|~~', '', cleaned_text)
            cleaned_text = re.sub(r'^(Assistant|AI|Human|User|System):\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'wrong\s+(assistant|content|response)', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'mode:\s*\w+', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip().strip('.,;:- ')
            
            if not cleaned_text:
                logger.warning(f"[{self.call_uuid}] Text became empty after cleaning, skipping TTS")
                return False
            
            # Get user's selected PlayHT voice
            voice_id = getattr(self, 'playht_voice_id', 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json')
            logger.info(f"[{self.call_uuid}] Using PlayHT voice: {voice_id[:50]}...")
            
            import httpx
            
            # PlayHT API v2 endpoint
            url = "https://api.play.ht/api/v2/tts"
            
            headers = {
                "Authorization": f"Bearer {playht_api_key}",
                "X-USER-ID": playht_user_id,
                "Content-Type": "application/json",
                "accept": "audio/mpeg"
            }
            
            # Request payload - using PlayHT 2.0 turbo for fastest response
            payload = {
                "text": cleaned_text,
                "voice": voice_id,
                "quality": "draft",  # Faster generation
                "output_format": "mp3",
                "speed": 1.05,  # Slightly faster for quicker responses
                "sample_rate": 24000
            }
            
            logger.info(f"[{self.call_uuid}] Calling PlayHT API...")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=20.0)
                
                if response.status_code != 200:
                    logger.error(f"[{self.call_uuid}] PlayHT API error: {response.status_code} - {response.text}")
                    return False
                
                audio_data = response.content
            
            logger.info(f"[{self.call_uuid}] PlayHT generated {len(audio_data)} bytes of audio")
            
            if len(audio_data) == 0:
                logger.error(f"[{self.call_uuid}] PlayHT returned empty audio!")
                return False
            
            # Convert MP3 to PCM 16kHz for Vonage
            from pydub import AudioSegment
            from io import BytesIO
            
            audio = AudioSegment.from_mp3(BytesIO(audio_data))
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            pcm_data = audio.raw_data
            
            # Send all at once
            if self.vonage_ws and self.is_active:
                await self.vonage_ws.send_bytes(pcm_data)
                logger.info(f"[{self.call_uuid}] ✅ PlayHT audio sent successfully ({len(pcm_data)} bytes)")
            else:
                logger.warning(f"[{self.call_uuid}] Vonage WS disconnected, cannot send audio")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error generating/sending PlayHT audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _handle_book_appointment(self, call_id: str, arguments: dict):
        """Handle appointment booking function call from AI"""
        try:
            # Extract appointment details
            date = arguments.get("date")
            time = arguments.get("time")
            customer_name = arguments.get("customer_name", "")
            customer_phone = arguments.get("customer_phone", self.caller_number)
            description = arguments.get("description", "")
            
            conn = sqlite3.connect('call_logs.db')
            cursor = conn.cursor()
            
            # Check for double bookings
            cursor.execute('''
                SELECT time FROM appointments 
                WHERE date = ? AND status = 'scheduled'
                ORDER BY time
            ''', (date,))
            existing_times = [row[0] for row in cursor.fetchall()]
            
            # Check if requested time is already booked
            if time in existing_times:
                # Find alternative times (9 AM - 5 PM, on the hour)
                all_times = [f"{h:02d}:00" for h in range(9, 18)]
                available_times = [t for t in all_times if t not in existing_times]
                
                alternatives = available_times[:3] if len(available_times) >= 3 else available_times
                
                conn.close()
                
                logger.warning(f"[{self.call_uuid}] Double booking prevented for {date} at {time}")
                
                # Send double booking response
                await self.openai_ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps({
                            "success": False,
                            "error": "double_booking",
                            "message": f"Sorry, {time} is already booked on {date}",
                            "alternatives": alternatives
                        })
                    }
                }))
                await self.openai_ws.send(json.dumps({"type": "response.create"}))
                return
            
            # Generate brief call summary using DeepSeek
            full_transcript = "\n".join(self.transcript_parts)
            call_summary = "Call summary not available"
            
            try:
                import openai as openai_module
                client = openai_module.OpenAI(
                    api_key=CONFIG['DEEPSEEK_API_KEY'],
                    base_url="https://api.deepseek.com"
                )
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "Summarize this phone call in 1-2 brief sentences."},
                        {"role": "user", "content": f"Call transcript:\n{full_transcript}"}
                    ],
                    max_tokens=100
                )
                call_summary = response.choices[0].message.content.strip()
                logger.info(f"[{self.call_uuid}] Generated appointment summary")
            except Exception as e:
                logger.error(f"[{self.call_uuid}] Failed to generate call summary: {e}")
                call_summary = f"Call from {customer_name or 'customer'} regarding: {description}"
            
            # Add call summary to description
            full_description = f"{description}\n\n--- Call Summary ---\n{call_summary}" if description else f"--- Call Summary ---\n{call_summary}"
            
            # Get user_id and voice from session (assigned during call creation)
            user_id = getattr(self, 'user_id', None)
            
            # Save appointment to database
            cursor.execute('''
                INSERT INTO appointments 
                (date, time, duration, title, description, customer_name, customer_phone, status, created_by, call_uuid, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, time, 30, "Phone Appointment", full_description,
                customer_name, customer_phone, "scheduled", "ai_agent", self.call_uuid, user_id
            ))
            appointment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"[{self.call_uuid}] Appointment {appointment_id} booked for {customer_name} on {date} at {time}")
            
            # Send success response back to AI
            await self.openai_ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps({
                        "success": True,
                        "appointment_id": appointment_id,
                        "message": f"Appointment successfully booked for {date} at {time}"
                    })
                }
            }))
            
            # Trigger response generation
            await self.openai_ws.send(json.dumps({"type": "response.create"}))
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error booking appointment: {e}")
            # Send error response back to AI
            await self.openai_ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps({
                        "success": False,
                        "error": str(e)
                    })
                }
            }))
            await self.openai_ws.send(json.dumps({"type": "response.create"}))
    
    async def _monitor_timeout(self):
        """Monitor for caller silence and end call after 15 seconds of no speech"""
        try:
            while self.is_active:
                await asyncio.sleep(1)  # Check every second
                
                if self._last_speech_time is None:
                    continue
                    
                current_time = asyncio.get_event_loop().time()
                silence_duration = current_time - self._last_speech_time
                
                # If no speech for 60 seconds, end call
                if silence_duration >= 60.0:
                    logger.warning(f"[{self.call_uuid}] No caller response for 60 seconds - ending call")
                    # Actually terminate the Vonage call
                    await self._terminate_vonage_call()
                    await self.close()
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error in timeout monitor: {e}")
    
    async def _terminate_vonage_call(self):
        """Send hangup command to Vonage to terminate the call"""
        try:
            # Close the Vonage WebSocket to terminate audio
            if self.vonage_ws:
                await self.vonage_ws.close()
                self.vonage_ws = None
            
            # Use Vonage API to hang up the call
            from vonage import Client, Auth
            auth = Auth(application_id=CONFIG['VONAGE_APP_ID'], private_key=CONFIG['VONAGE_PRIVATE_KEY'])
            client = Client(auth=auth)
            
            try:
                # Update call status to 'completed' to hang up
                client.voice.update_call(self.call_uuid, action='hangup')
                logger.info(f"[{self.call_uuid}] Vonage call terminated via API")
            except Exception as api_error:
                logger.warning(f"[{self.call_uuid}] Could not terminate via API: {api_error}")
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error terminating Vonage call: {e}")
    
    def start_openai_listener(self):
        """Start background task to listen for OpenAI responses"""
        self._openai_task = asyncio.create_task(self.receive_from_openai())
    
    async def close(self):
        """Clean up the session"""
        self.is_active = False
        
        # Cancel timeout monitoring
        if self._timeout_task:
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
        
        if self._openai_task:
            self._openai_task.cancel()
            try:
                await self._openai_task
            except asyncio.CancelledError:
                pass
        
        if self.openai_ws:
            try:
                await self.openai_ws.close()
            except:
                pass
            self.openai_ws = None
        
        # Log call end with transcript
        full_transcript = "\n".join(self.transcript_parts)
        
        # Calculate average response time
        avg_response_time = None
        if self._response_times:
            avg_response_time = sum(self._response_times) / len(self._response_times)
            logger.info(f"[{self.call_uuid}] Average response time: {avg_response_time:.0f}ms from {len(self._response_times)} responses")
        
        CallLogger.log_call_end(self.call_uuid, full_transcript, avg_response_time)
        
        # Generate AI summary in background
        asyncio.create_task(CallLogger.generate_summary(self.call_uuid))
            
        logger.info(f"[{self.call_uuid}] Session closed")


# ============================================================================
# ACTIVE SESSIONS MANAGER
# ============================================================================

class SessionManager:
    """Manages all active call sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, CallSession] = {}
    
    async def create_session(self, call_uuid: str, caller: str = "", called: str = "", user_id: Optional[int] = None) -> CallSession:
        """Create a new call session"""
        session = CallSession(call_uuid, caller, called)
        session.user_id = user_id  # Store user_id in session
        
        # Load user's voice and provider preference from database
        if user_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT voice, use_elevenlabs, elevenlabs_voice_id, voice_provider, cartesia_voice_id, google_voice, playht_voice_id
                    FROM account_settings WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    # OpenAI voice
                    session.user_voice = row[0] if row[0] else 'shimmer'
                    logger.info(f"[{call_uuid}] Loaded voice preference: {session.user_voice}")
                    
                    # Voice provider (openai, elevenlabs, cartesia, google, playht)
                    session.voice_provider = row[3] if row[3] else 'openai'
                    logger.info(f"[{call_uuid}] Voice provider: {session.voice_provider}")
                    
                    # Legacy ElevenLabs toggle (for backwards compatibility)
                    session.use_elevenlabs = bool(row[1]) if row[1] is not None else False
                    
                    # ElevenLabs voice ID
                    session.elevenlabs_voice_id = row[2] if row[2] else 'EXAVITQu4vr4xnSDxMaL'
                    if session.voice_provider == 'elevenlabs':
                        logger.info(f"[{call_uuid}] ElevenLabs voice ID: {session.elevenlabs_voice_id}")
                    
                    # Cartesia voice ID
                    session.cartesia_voice_id = row[4] if row[4] else 'a0e99841-438c-4a64-b679-ae501e7d6091'
                    if session.voice_provider == 'cartesia':
                        logger.info(f"[{call_uuid}] Cartesia voice ID: {session.cartesia_voice_id}")
                    
                    # Google voice
                    session.google_voice = row[5] if row[5] else 'en-GB-Neural2-A'
                    if session.voice_provider == 'google':
                        logger.info(f"[{call_uuid}] Google voice: {session.google_voice}")
                    
                    # PlayHT voice
                    session.playht_voice_id = row[6] if row[6] else 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json'
                    if session.voice_provider == 'playht':
                        logger.info(f"[{call_uuid}] PlayHT voice ID: {session.playht_voice_id}")
                else:
                    session.user_voice = 'shimmer'
                    session.voice_provider = 'openai'
                    session.use_elevenlabs = False
                    session.elevenlabs_voice_id = 'EXAVITQu4vr4xnSDxMaL'
                    session.cartesia_voice_id = 'a0e99841-438c-4a64-b679-ae501e7d6091'
                    session.google_voice = 'en-GB-Neural2-A'
                    session.playht_voice_id = 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json'
            except Exception as e:
                logger.error(f"[{call_uuid}] Failed to load preferences: {e}")
                session.user_voice = 'shimmer'
                session.use_elevenlabs = False
                session.elevenlabs_voice_id = 'EXAVITQu4vr4xnSDxMaL'
                session.google_voice = 'en-GB-Neural2-A'
                session.playht_voice_id = 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json'
        else:
            session.user_voice = 'shimmer'
            session.use_elevenlabs = False
            session.elevenlabs_voice_id = 'EXAVITQu4vr4xnSDxMaL'
            session.playht_voice_id = 's3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json'
        
        self._sessions[call_uuid] = session
        # Log call start with user_id
        CallLogger.log_call_start(call_uuid, caller, called, user_id)
        return session
    
    def get_session(self, call_uuid: str) -> Optional[CallSession]:
        """Get an existing session"""
        return self._sessions.get(call_uuid)
    
    async def close_session(self, call_uuid: str):
        """Close and remove a session"""
        if call_uuid in self._sessions:
            await self._sessions[call_uuid].close()
            del self._sessions[call_uuid]
    
    async def close_all(self):
        """Close all sessions"""
        for call_uuid in list(self._sessions.keys()):
            await self.close_session(call_uuid)


sessions = SessionManager()

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Vonage Voice Agent starting...")
    logger.info(f"📞 Answer URL: {CONFIG['PUBLIC_URL']}/webhooks/answer")
    logger.info(f"📋 Event URL: {CONFIG['PUBLIC_URL']}/webhooks/events")
    yield
    logger.info("Shutting down...")
    await sessions.close_all()


app = FastAPI(
    title="Vonage Voice Agent",
    description="AI-powered phone agent using OpenAI Realtime API",
    lifespan=lifespan
)

# Mount static files for the UI
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page"""
    with open("static/landing.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/landing.html", response_class=HTMLResponse)
async def landing():
    """Serve the landing page"""
    with open("static/landing.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/signup.html", response_class=HTMLResponse)
async def signup():
    """Serve the signup page"""
    with open("static/signup.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/signin.html", response_class=HTMLResponse)
async def signin():
    """Serve the signin page"""
    with open("static/signin.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/faq.html", response_class=HTMLResponse)
async def faq():
    """Serve the FAQ page"""
    with open("static/faq.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/admin", response_class=HTMLResponse)
async def admin():
    """Serve the admin dashboard"""
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/admin.html", response_class=HTMLResponse)
async def admin_html():
    """Serve the admin dashboard"""
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/super-admin", response_class=HTMLResponse)
async def super_admin():
    """Serve the super admin dashboard"""
    with open("static/super-admin.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/super-admin.html", response_class=HTMLResponse)
@app.get("/super-admin.html", response_class=HTMLResponse)
async def super_admin_html():
    """Serve the super admin dashboard"""
    with open("static/super-admin.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/active-calls")
async def get_active_calls():
    """Get count of active call sessions"""
    return {"count": len(sessions._sessions)}


@app.get("/api/config")
async def get_config(authorization: Optional[str] = Header(None)):
    """Get current agent configuration for user"""
    user_id = await get_current_user(authorization)
    voice = 'shimmer'
    use_elevenlabs = False
    elevenlabs_voice_id = 'EXAVITQu4vr4xnSDxMaL'
    voice_provider = 'openai'
    cartesia_voice_id = 'a0e99841-438c-4a64-b679-ae501e7d6091'
    google_voice = 'en-GB-Neural2-A'
    phone_number = ''
    response_latency = 300
    agent_name = 'Judie'
    business_info = ''
    agent_personality = 'Friendly and professional. Keep responses brief and conversational.'
    agent_instructions = 'Answer questions about the business. Take messages if needed.'
    calendar_booking_enabled = True
    
    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT voice, use_elevenlabs, elevenlabs_voice_id, phone_number, 
                       response_latency, voice_provider, cartesia_voice_id, google_voice,
                       agent_name, business_info, agent_personality, agent_instructions,
                       calendar_booking_enabled
                FROM account_settings WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                if row[0]:
                    voice = row[0]
                if row[1] is not None:
                    use_elevenlabs = bool(row[1])
                if row[2]:
                    elevenlabs_voice_id = row[2]
                if row[3]:
                    phone_number = row[3]
                if row[4] is not None:
                    response_latency = row[4]
                if row[5]:
                    voice_provider = row[5]
                if row[6]:
                    cartesia_voice_id = row[6]
                if row[7]:
                    google_voice = row[7]
                if row[8]:
                    agent_name = row[8]
                    CONFIG["AGENT_NAME"] = agent_name  # Update in-memory config
                if row[9]:
                    business_info = row[9]
                    CONFIG["BUSINESS_INFO"] = business_info
                if row[10]:
                    agent_personality = row[10]
                    CONFIG["AGENT_PERSONALITY"] = agent_personality
                if row[11]:
                    agent_instructions = row[11]
                    CONFIG["AGENT_INSTRUCTIONS"] = agent_instructions
                if row[12] is not None:
                    calendar_booking_enabled = bool(row[12])
        except Exception as e:
            logger.error(f"Failed to load user config: {e}")
    
    return {
        "AGENT_NAME": agent_name,
        "BUSINESS_INFO": business_info,
        "AGENT_PERSONALITY": agent_personality,
        "AGENT_INSTRUCTIONS": agent_instructions,
        "VOICE": voice,
        "USE_ELEVENLABS": use_elevenlabs,
        "ELEVENLABS_VOICE_ID": elevenlabs_voice_id,
        "VOICE_PROVIDER": voice_provider,
        "CARTESIA_VOICE_ID": cartesia_voice_id,
        "GOOGLE_VOICE": google_voice,
        "PHONE_NUMBER": phone_number,
        "RESPONSE_LATENCY": response_latency,
        "CALENDAR_BOOKING_ENABLED": calendar_booking_enabled
    }


@app.post("/api/config")
async def update_config(request: Request, authorization: Optional[str] = Header(None)):
    """Update agent configuration"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update all configuration fields in database
        if "AGENT_NAME" in data:
            CONFIG["AGENT_NAME"] = data["AGENT_NAME"]
            cursor.execute('UPDATE account_settings SET agent_name = ? WHERE user_id = ?', 
                         (data["AGENT_NAME"], user_id))
            logger.info(f"Agent name updated to {data['AGENT_NAME']} for user {user_id}")
        
        if "BUSINESS_INFO" in data:
            CONFIG["BUSINESS_INFO"] = data["BUSINESS_INFO"]
            cursor.execute('UPDATE account_settings SET business_info = ? WHERE user_id = ?', 
                         (data["BUSINESS_INFO"], user_id))
            logger.info(f"Business info updated for user {user_id}")
        
        if "AGENT_PERSONALITY" in data:
            CONFIG["AGENT_PERSONALITY"] = data["AGENT_PERSONALITY"]
            cursor.execute('UPDATE account_settings SET agent_personality = ? WHERE user_id = ?', 
                         (data["AGENT_PERSONALITY"], user_id))
            logger.info(f"Agent personality updated for user {user_id}")
        
        if "AGENT_INSTRUCTIONS" in data:
            CONFIG["AGENT_INSTRUCTIONS"] = data["AGENT_INSTRUCTIONS"]
            cursor.execute('UPDATE account_settings SET agent_instructions = ? WHERE user_id = ?', 
                         (data["AGENT_INSTRUCTIONS"], user_id))
            logger.info(f"Agent instructions updated for user {user_id}")
        
        if "VOICE" in data:
            cursor.execute('UPDATE account_settings SET voice = ? WHERE user_id = ?', 
                         (data["VOICE"], user_id))
            logger.info(f"Voice updated to {data['VOICE']} for user {user_id}")
        
        if "USE_ELEVENLABS" in data:
            use_el = 1 if data["USE_ELEVENLABS"] else 0
            cursor.execute('UPDATE account_settings SET use_elevenlabs = ? WHERE user_id = ?', 
                         (use_el, user_id))
            logger.info(f"ElevenLabs setting updated to {data['USE_ELEVENLABS']} for user {user_id}")
        
        if "ELEVENLABS_VOICE_ID" in data:
            cursor.execute('UPDATE account_settings SET elevenlabs_voice_id = ? WHERE user_id = ?', 
                         (data["ELEVENLABS_VOICE_ID"], user_id))
            logger.info(f"ElevenLabs voice ID updated to {data['ELEVENLABS_VOICE_ID']} for user {user_id}")
        
        if "GOOGLE_VOICE" in data:
            cursor.execute('UPDATE account_settings SET google_voice = ? WHERE user_id = ?', 
                         (data["GOOGLE_VOICE"], user_id))
            logger.info(f"Google voice updated to {data['GOOGLE_VOICE']} for user {user_id}")
        
        if "PHONE_NUMBER" in data:
            cursor.execute('UPDATE account_settings SET phone_number = ? WHERE user_id = ?', 
                         (data["PHONE_NUMBER"], user_id))
            logger.info(f"Phone number updated to {data['PHONE_NUMBER']} for user {user_id}")
        
        if "RESPONSE_LATENCY" in data:
            cursor.execute('UPDATE account_settings SET response_latency = ? WHERE user_id = ?', 
                         (data["RESPONSE_LATENCY"], user_id))
            logger.info(f"Response latency updated to {data['RESPONSE_LATENCY']}ms for user {user_id}")
        
        if "CALENDAR_BOOKING_ENABLED" in data:
            calendar_enabled = 1 if data["CALENDAR_BOOKING_ENABLED"] else 0
            cursor.execute('UPDATE account_settings SET calendar_booking_enabled = ? WHERE user_id = ?', 
                         (calendar_enabled, user_id))
            logger.info(f"Calendar booking enabled updated to {data['CALENDAR_BOOKING_ENABLED']} for user {user_id}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Configuration saved to database for user {user_id}")
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "config": {
                "AGENT_NAME": CONFIG["AGENT_NAME"],
                "AGENT_INSTRUCTIONS": CONFIG["AGENT_INSTRUCTIONS"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.post("/api/analyze-latency")
async def analyze_latency(authorization: Optional[str] = Header(None)):
    """Analyze call response times and optimize settings using DeepSeek AI"""
    try:
        user_id = await get_current_user(authorization)
        
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        
        # Get recent calls with response times
        cursor.execute('''
            SELECT call_uuid, average_response_time, duration, created_at
            FROM calls
            WHERE user_id = ? AND average_response_time IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
        ''', (user_id,))
        
        calls = cursor.fetchall()
        
        if not calls:
            conn.close()
            return JSONResponse({
                "success": False,
                "message": "No call data available yet. Make some calls first to analyze response times."
            })
        
        # Calculate statistics
        response_times = [call[1] for call in calls if call[1] is not None]
        avg_response = sum(response_times) / len(response_times)
        min_response = min(response_times)
        max_response = max(response_times)
        
        # Sort for percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        
        # Get current settings
        cursor.execute('''
            SELECT response_latency, voice, use_elevenlabs
            FROM account_settings
            WHERE user_id = ?
        ''', (user_id,))
        
        settings = cursor.fetchone()
        current_latency = settings[0] if settings else 700
        voice = settings[1] if settings else "shimmer"
        use_elevenlabs = settings[2] if settings else 0
        
        conn.close()
        
        # Human baseline: 600-800ms is natural conversation timing
        human_baseline = 700
        
        # Determine if optimization is needed
        needs_optimization = avg_response > 1000  # More than 1 second
        
        analysis = {
            "success": True,
            "statistics": {
                "total_calls_analyzed": len(calls),
                "average_response_ms": round(avg_response, 0),
                "median_response_ms": round(p50, 0),
                "95th_percentile_ms": round(p95, 0),
                "min_response_ms": round(min_response, 0),
                "max_response_ms": round(max_response, 0)
            },
            "current_settings": {
                "response_latency": current_latency,
                "voice": voice,
                "use_elevenlabs": bool(use_elevenlabs)
            },
            "assessment": {
                "human_baseline_ms": human_baseline,
                "performance_vs_human": round((avg_response / human_baseline - 1) * 100, 1),
                "needs_optimization": needs_optimization
            }
        }
        
        # Use DeepSeek AI to analyze and recommend optimizations
        if needs_optimization and CONFIG.get("DEEPSEEK_API_KEY"):
            try:
                import openai as openai_module
                
                client = openai_module.OpenAI(
                    api_key=CONFIG['DEEPSEEK_API_KEY'],
                    base_url="https://api.deepseek.com"
                )
                
                prompt = f"""You are an AI performance optimization expert. Analyze these response time metrics from a voice AI system:

CURRENT PERFORMANCE:
- Average response time: {avg_response:.0f}ms
- Median: {p50:.0f}ms
- 95th percentile: {p95:.0f}ms
- Min/Max: {min_response:.0f}ms / {max_response:.0f}ms
- Calls analyzed: {len(calls)}

CURRENT SETTINGS:
- VAD silence_duration_ms: {current_latency}
- Voice: {voice}
- Using ElevenLabs: {bool(use_elevenlabs)}

HUMAN BASELINE: 600-800ms is natural conversation timing

TASK: Identify the likely bottlenecks and provide specific numeric recommendations:
1. What is causing the delay? (Network, API latency, VAD settings, audio processing)
2. What should silence_duration_ms be set to? (Give exact number in ms)
3. Should any other settings change?
4. What response time improvement can we expect?

Be specific and concise. Focus on actionable recommendations."""

                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                ai_recommendations = response.choices[0].message.content
                
                # Parse recommendations to extract specific values
                recommended_latency = current_latency
                
                # Try to extract numeric recommendation
                import re
                latency_match = re.search(r'silence_duration_ms[:\s]+(\d+)', ai_recommendations)
                if latency_match:
                    recommended_latency = int(latency_match.group(1))
                elif avg_response > 1500:
                    recommended_latency = max(300, current_latency - 200)
                elif avg_response > 1000:
                    recommended_latency = max(400, current_latency - 100)
                
                analysis["ai_analysis"] = {
                    "recommendations": ai_recommendations,
                    "suggested_latency_ms": recommended_latency,
                    "auto_apply_available": True
                }
                
                # Auto-apply if significantly better and reasonable
                if 200 <= recommended_latency <= 1000 and recommended_latency != current_latency:
                    conn = sqlite3.connect('call_logs.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE account_settings 
                        SET response_latency = ? 
                        WHERE user_id = ?
                    ''', (recommended_latency, user_id))
                    conn.commit()
                    conn.close()
                    
                    # Detailed change log
                    change_summary = f"""OPTIMIZATION APPLIED:
• silence_duration_ms: {current_latency}ms → {recommended_latency}ms
• Voice: {voice} ({"ElevenLabs eleven_turbo_v2_5" if use_elevenlabs else "OpenAI"})
• VAD threshold: 0.5 (unchanged)
• Prefix padding: 300ms (unchanged)
• Reason: {ai_recommendations[:100]}..."""
                    
                    analysis["auto_applied"] = {
                        "old_latency": current_latency,
                        "new_latency": recommended_latency,
                        "message": f"Settings automatically optimized! Response latency adjusted from {current_latency}ms to {recommended_latency}ms.",
                        "detailed_changes": change_summary
                    }
                    logger.info(f"""\n{'='*60}\n⚡ AUTO-OPTIMIZATION APPLIED FOR USER {user_id}\n{'='*60}\n{change_summary}\n{'='*60}""")
                
            except Exception as e:
                logger.error(f"DeepSeek analysis failed: {e}")
                analysis["ai_analysis"] = {
                    "error": "AI analysis unavailable",
                    "fallback_recommendation": "Average response time is high. Consider reducing response_latency setting."
                }
        
        return JSONResponse(analysis)
        
    except Exception as e:
        logger.error(f"Latency analysis error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/status")
async def status():
    """API health check endpoint"""
    return {
        "status": "running",
        "agent": CONFIG["AGENT_NAME"],
        "endpoints": {
            "answer_url": f"{CONFIG['PUBLIC_URL']}/webhooks/answer",
            "event_url": f"{CONFIG['PUBLIC_URL']}/webhooks/events",
            "websocket": f"wss://{CONFIG['PUBLIC_URL'].replace('https://', '')}/socket/{{call_uuid}}"
        }
    }


@app.get("/api/calls")
async def get_calls(limit: int = 20, authorization: Optional[str] = Header(None)):
    """Get recent call logs (user-specific)"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    calls = CallLogger.get_recent_calls(limit, user_id)
    return {"calls": calls}


@app.post("/api/calls/{call_uuid}/complete")
async def mark_call_complete(call_uuid: str):
    """Mark a call as completed"""
    try:
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE calls SET status = ? WHERE call_uuid = ?', ('completed', call_uuid))
        conn.commit()
        conn.close()
        
        logger.info(f"Call {call_uuid} marked as completed")
        return {"status": "success", "message": "Call marked as completed"}
    except Exception as e:
        logger.error(f"Failed to mark call complete: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.delete("/api/calls/{call_uuid}")
async def delete_call(call_uuid: str):
    """Delete a call record"""
    try:
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM calls WHERE call_uuid = ?', (call_uuid,))
        conn.commit()
        conn.close()
        
        logger.info(f"Call {call_uuid} deleted")
        return {"status": "success", "message": "Call deleted"}
    except Exception as e:
        logger.error(f"Failed to delete call: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


# ============================================================================
# CALENDAR / APPOINTMENTS API
# ============================================================================

@app.get("/api/appointments")
async def get_appointments(date: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Get appointments for current user, optionally filtered by date (YYYY-MM-DD)"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if date:
            cursor.execute('''
                SELECT * FROM appointments 
                WHERE date = ? AND (user_id = ? OR user_id IS NULL)
                ORDER BY time
            ''', (date, user_id))
        else:
            cursor.execute('''
                SELECT * FROM appointments 
                WHERE user_id = ? OR user_id IS NULL 
                ORDER BY date, time
            ''', (user_id,))
        
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Fetched {len(appointments)} appointments for user {user_id}")
        return {"appointments": appointments}
    except Exception as e:
        logger.error(f"Failed to fetch appointments: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.post("/api/appointments")
async def create_appointment(request: Request, authorization: Optional[str] = Header(None)):
    """Create a new appointment for current user"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO appointments 
            (date, time, duration, title, description, customer_name, customer_phone, status, created_by, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('date'),
            data.get('time'),
            data.get('duration', 30),
            data.get('title', 'Appointment'),
            data.get('description', ''),
            data.get('customer_name', ''),
            data.get('customer_phone', ''),
            data.get('status', 'scheduled'),
            data.get('created_by', 'user'),
            user_id
        ))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Appointment {appointment_id} created for {data.get('date')} at {data.get('time')}")
        return {"status": "success", "appointment_id": appointment_id}
    except Exception as e:
        logger.error(f"Failed to create appointment: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.put("/api/appointments/{appointment_id}")
async def update_appointment(appointment_id: int, request: Request):
    """Update an appointment"""
    try:
        data = await request.json()
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        
        # Build dynamic UPDATE query based on provided fields
        update_fields = []
        values = []
        
        for field in ['date', 'time', 'duration', 'title', 'description', 'customer_name', 'customer_phone', 'status']:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])
        
        if update_fields:
            values.append(appointment_id)
            query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        
        logger.info(f"Appointment {appointment_id} updated")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to update appointment: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: int):
    """Delete an appointment"""
    try:
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Appointment {appointment_id} deleted")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to delete appointment: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.get("/api/minutes")
async def get_minutes(authorization: Optional[str] = Header(None)):
    """Get remaining minutes for current user"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        minutes = MinutesTracker.get_minutes_remaining(user_id)
        return JSONResponse({"minutes_remaining": minutes})
    except Exception as e:
        logger.error(f"Error getting minutes: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/stats/today")
async def get_today_stats(authorization: Optional[str] = Header(None)):
    """Get stats for today (user-specific)"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get calls today for this user
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM calls 
            WHERE DATE(start_time) = ? AND user_id = ?
        ''', (today, user_id))
        calls_today = cursor.fetchone()[0]
        
        # Get messages today (calls with transcripts that are not empty)
        cursor.execute('''
            SELECT COUNT(*) FROM calls 
            WHERE DATE(start_time) = ? AND user_id = ? AND transcript IS NOT NULL AND transcript != ''
        ''', (today, user_id))
        messages_today = cursor.fetchone()[0]
        
        # Get unread appointments for this user
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE status = 'scheduled' AND created_by = 'ai_agent' AND user_id = ?
        ''', (user_id,))
        unread_appointments = cursor.fetchone()[0]
        
        conn.close()
        
        return JSONResponse({
            "calls_today": calls_today,
            "messages_today": messages_today,
            "unread_appointments": unread_appointments
        })
    except Exception as e:
        logger.error(f"Error getting today stats: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/billing-config")
async def get_billing_config():
    """Get billing configuration (credits pricing)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create billing_config table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billing_config (
                id INTEGER PRIMARY KEY,
                credits_per_connected_call REAL DEFAULT 5.0,
                credits_per_minute REAL DEFAULT 2.0,
                credits_per_calendar_booking REAL DEFAULT 10.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get config or insert defaults
        cursor.execute('SELECT * FROM billing_config WHERE id = 1')
        config = cursor.fetchone()
        if not config:
            cursor.execute('''
                INSERT INTO billing_config (id, credits_per_connected_call, credits_per_minute, credits_per_calendar_booking)
                VALUES (1, 5.0, 2.0, 10.0)
            ''')
            conn.commit()
            config = (1, 5.0, 2.0, 10.0, None)
        
        conn.close()
        
        return JSONResponse({
            "credits_per_connected_call": config[1],
            "credits_per_minute": config[2],
            "credits_per_calendar_booking": config[3]
        })
    except Exception as e:
        logger.error(f"Error getting billing config: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/billing-history")
async def get_billing_history(authorization: Optional[str] = Header(None)):
    """Get billing/usage history for current user"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get billing config
        cursor.execute('SELECT * FROM billing_config WHERE id = 1')
        config = cursor.fetchone()
        if not config:
            config = (1, 5.0, 2.0, 10.0, None)
        
        credits_per_call = config[1]
        credits_per_minute = config[2]
        credits_per_booking = config[3]
        
        # Get all calls for this user
        cursor.execute('''
            SELECT call_uuid, start_time, duration, caller_number, summary
            FROM calls 
            WHERE user_id = ?
            ORDER BY start_time DESC
        ''', (user_id,))
        
        calls = []
        total_credits = 0
        
        for row in cursor.fetchall():
            call_uuid, start_time, duration, caller_number, summary = row
            
            # Calculate credits for this call
            call_credits = credits_per_call  # Connection charge
            if duration:
                minutes = duration / 60
                call_credits += minutes * credits_per_minute
            
            total_credits += call_credits
            
            calls.append({
                "type": "call",
                "call_uuid": call_uuid,
                "date": start_time,
                "description": f"Call from {caller_number}",
                "duration": duration,
                "credits": round(call_credits, 2)
            })
        
        # Get calendar bookings made by AI
        cursor.execute('''
            SELECT id, title, date, time, created_at
            FROM appointments 
            WHERE user_id = ? AND created_by = 'ai_agent'
            ORDER BY created_at DESC
        ''', (user_id,))
        
        bookings = []
        for row in cursor.fetchall():
            appt_id, title, date, time, created_at = row
            total_credits += credits_per_booking
            
            bookings.append({
                "type": "booking",
                "id": appt_id,
                "date": created_at,
                "description": f"Calendar booking: {title}",
                "appointment_date": f"{date} {time}",
                "credits": credits_per_booking
            })
        
        # Combine and sort by date
        all_transactions = calls + bookings
        all_transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Get current credits balance from account_settings
        cursor.execute('SELECT minutes_remaining FROM account_settings WHERE user_id = ?', (user_id,))
        balance_row = cursor.fetchone()
        current_balance = balance_row[0] if balance_row else 0
        
        conn.close()
        
        return JSONResponse({
            "current_balance": current_balance,
            "total_used": round(total_credits, 2),
            "transactions": all_transactions,
            "pricing": {
                "per_call": credits_per_call,
                "per_minute": credits_per_minute,
                "per_booking": credits_per_booking
            }
        })
    except Exception as e:
        logger.error(f"Error getting billing history: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/owned-numbers")
async def get_owned_numbers(authorization: Optional[str] = Header(None)):
    """Get all owned Vonage numbers and their account assignments"""
    try:
        import httpx
        
        api_key = CONFIG["VONAGE_API_KEY"]
        api_secret = CONFIG["VONAGE_API_SECRET"]
        
        # Get all owned numbers from Vonage
        url = "https://rest.nexmo.com/account/numbers"
        params = {
            "api_key": api_key,
            "api_secret": api_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            result = response.json()
        
        logger.info(f"Vonage API response status: {response.status_code}")
        logger.info(f"Vonage API response: {result}")
        
        owned_numbers = []
        if response.status_code == 200:
            numbers = result.get("numbers", [])
            logger.info(f"Found {len(numbers)} numbers from Vonage API")
            
            # Get account assignments from database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user assignments
            cursor.execute('''
                SELECT user_id, phone_number 
                FROM account_settings 
                WHERE phone_number IS NOT NULL AND phone_number != ''
            ''')
            assignments = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Get user names for display
            cursor.execute('SELECT id, name FROM users')
            users = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Create availability table if doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS number_availability (
                    phone_number TEXT PRIMARY KEY,
                    is_available INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Get manual availability settings
            cursor.execute('SELECT phone_number, is_available FROM number_availability')
            availability_settings = {row[0]: bool(row[1]) for row in cursor.fetchall()}
            
            conn.close()
            
            for number in numbers:
                msisdn = number.get("msisdn")
                user_id = assignments.get(msisdn)
                
                # Check manual availability setting
                # If no record exists, default to available (True)
                # If record exists, use the stored value
                if msisdn in availability_settings:
                    manually_available = availability_settings[msisdn]
                else:
                    manually_available = True  # Default to available if no record
                
                # Number is available if: not assigned to user AND manually available
                is_available = user_id is None and manually_available
                
                owned_numbers.append({
                    "number": msisdn,
                    "country": number.get("country"),
                    "type": number.get("type"),
                    "assigned_to": users.get(user_id) if user_id else None,
                    "user_id": user_id,
                    "available": is_available
                })
        
        return JSONResponse({
            "success": True,
            "numbers": owned_numbers,
            "total": len(owned_numbers)
        })
        
    except Exception as e:
        logger.error(f"Error fetching owned numbers: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/available-numbers")
async def get_available_numbers(
    country: str = "GB",
    search_pattern: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Search for available phone numbers to purchase"""
    logger.info(f"Available numbers request - Country: {country}, Pattern: {search_pattern}")
    
    user_id = await get_current_user(authorization)
    if not user_id:
        logger.warning("Unauthorized access attempt to available-numbers")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        api_key = CONFIG["VONAGE_API_KEY"]
        api_secret = CONFIG["VONAGE_API_SECRET"]
        
        logger.info(f"Using Vonage API key: {api_key[:8]}...")
        
        # Build search URL
        url = f"https://rest.nexmo.com/number/search"
        params = {
            "api_key": api_key,
            "api_secret": api_secret,
            "country": country,
            "type": "mobile-lvn",  # Local virtual numbers
            "features": "VOICE",
            "size": 20
        }
        
        if search_pattern:
            params["pattern"] = search_pattern
        
        logger.info(f"Searching Vonage API: {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            logger.info(f"Vonage API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Vonage API error: {error_text}")
                return JSONResponse({
                    "success": False,
                    "error": f"Vonage API error: {error_text}"
                }, status_code=500)
            
            data = response.json()
        
        numbers = data.get("numbers", [])
        logger.info(f"Found {len(numbers)} available numbers")
        
        return JSONResponse({
            "success": True,
            "count": len(numbers),
            "numbers": numbers
        })
        
    except httpx.TimeoutException:
        logger.error("Timeout searching Vonage API")
        return JSONResponse({
            "success": False,
            "error": "Request timeout - Vonage API took too long to respond"
        }, status_code=500)
    except Exception as e:
        logger.error(f"Error searching numbers: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }, status_code=500)

@app.post("/api/purchase-number")
async def purchase_number(request: Request, authorization: Optional[str] = Header(None)):
    """Purchase a phone number"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        body = await request.json()
        country = body.get("country", "GB")
        msisdn = body.get("msisdn")  # Phone number to purchase
        
        if not msisdn:
            return JSONResponse({"success": False, "error": "Phone number required"}, status_code=400)
        
        import httpx
        
        api_key = CONFIG["VONAGE_API_KEY"]
        api_secret = CONFIG["VONAGE_API_SECRET"]
        
        # Purchase the number
        url = "https://rest.nexmo.com/number/buy"
        params = {
            "api_key": api_key,
            "api_secret": api_secret,
            "country": country,
            "msisdn": msisdn
        }
        
        logger.info(f"Attempting to purchase number: {msisdn}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=params, timeout=10.0)
            result = response.json()
        
        if response.status_code == 200 and result.get("error-code") == "200":
            # Update user's phone number in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE account_settings 
                SET phone_number = ?
                WHERE user_id = ?
            ''', (msisdn, user_id))
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully purchased number {msisdn} for user {user_id}")
            
            return JSONResponse({
                "success": True,
                "message": "Number purchased successfully!",
                "number": msisdn
            })
        else:
            error_msg = result.get("error-code-label", "Failed to purchase number")
            logger.error(f"Failed to purchase number: {error_msg}")
            return JSONResponse({
                "success": False,
                "error": error_msg
            }, status_code=400)
        
    except Exception as e:
        logger.error(f"Error purchasing number: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/minutes/buy")
async def buy_minutes(request: Request, authorization: Optional[str] = Header(None)):
    """Add 60 minutes to account (simulated purchase)"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        new_balance = MinutesTracker.add_minutes(user_id, 60)
        logger.info(f"💳 User {user_id} purchased 60 minutes - New balance: {new_balance}")
        return JSONResponse({
            "success": True,
            "minutes_remaining": new_balance,
            "minutes_added": 60
        })
    except Exception as e:
        logger.error(f"Error buying minutes: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/appointments/{appointment_id}/read")
async def mark_appointment_read(appointment_id: int, authorization: Optional[str] = Header(None)):
    """Mark appointment as read"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE appointments 
            SET status = 'read'
            WHERE id = ? AND status = 'scheduled' AND user_id = ?
        ''', (appointment_id, user_id))
        conn.commit()
        conn.close()
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error marking appointment as read: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ============================================================================
# AUTHENTICATION API ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup")
async def signup(request: Request):
    """Create a new user account"""
    conn = None
    try:
        data = await request.json()
        name = data.get('name', '').strip()
        
        if not name:
            return JSONResponse({"success": False, "error": "Name is required"}, status_code=400)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE name = ?', (name,))
        if cursor.fetchone():
            return JSONResponse({"success": False, "error": "Name already taken"}, status_code=400)
        
        # Create user
        cursor.execute('INSERT INTO users (name, last_login) VALUES (?, ?)', 
                      (name, datetime.now().isoformat()))
        user_id = cursor.lastrowid
        
        # Create initial account settings for user
        cursor.execute('INSERT INTO account_settings (user_id, minutes_remaining) VALUES (?, 60)', (user_id,))
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        cursor.execute('INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
                      (user_id, session_token, expires_at))
        
        conn.commit()
        
        logger.info(f"New user created: {name} (ID: {user_id})")
        
        return JSONResponse({
            "success": True,
            "session_token": session_token,
            "user_name": name,
            "user_id": user_id
        })
        
    except sqlite3.OperationalError as e:
        logger.error(f"Database error during signup: {e}")
        return JSONResponse({"success": False, "error": "database is locked"}, status_code=500)
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()


@app.post("/api/auth/signin")
async def signin(request: Request):
    """Sign in existing user"""
    conn = None
    try:
        data = await request.json()
        name = data.get('name', '').strip()
        
        if not name:
            return JSONResponse({"success": False, "error": "Name is required"}, status_code=400)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find user and check status
        cursor.execute('SELECT id, status, suspension_message FROM users WHERE name = ?', (name,))
        user = cursor.fetchone()
        
        if not user:
            return JSONResponse({"success": False, "error": "User not found"}, status_code=404)
        
        user_id = user[0]
        status = user[1] or 'active'
        suspension_message = user[2]
        
        # Check if account is suspended or banned
        if status == 'banned':
            return JSONResponse({
                "success": False, 
                "error": "Account Banned",
                "message": suspension_message or "Your account has been permanently banned. Please contact support."
            }, status_code=403)
        
        if status == 'suspended':
            return JSONResponse({
                "success": False,
                "error": "Account Suspended", 
                "message": suspension_message or "Your account has been suspended. Please contact support."
            }, status_code=403)
        
        # Update last login
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                      (datetime.now().isoformat(), user_id))
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        cursor.execute('INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
                      (user_id, session_token, expires_at))
        
        conn.commit()
        
        logger.info(f"User signed in: {name} (ID: {user_id})")
        
        return JSONResponse({
            "success": True,
            "session_token": session_token,
            "user_name": name,
            "user_id": user_id
        })
        
    except sqlite3.OperationalError as e:
        logger.error(f"Database error during signin: {e}")
        return JSONResponse({"success": False, "error": "database is locked"}, status_code=500)
    except Exception as e:
        logger.error(f"Signin error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        if conn:
            conn.close()


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and invalidate session"""
    try:
        data = await request.json()
        session_token = data.get('session_token')
        
        if not session_token:
            return JSONResponse({"success": False, "error": "No session token"}, status_code=400)
        
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/auth/verify")
async def verify_session(request: Request):
    """Verify if session is valid"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JSONResponse({"valid": False, "error": "No token"}, status_code=401)
        
        session_token = auth_header.replace('Bearer ', '')
        
        conn = sqlite3.connect('call_logs.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.user_id, u.name, s.expires_at, a.phone_number
            FROM sessions s 
            JOIN users u ON s.user_id = u.id 
            LEFT JOIN account_settings a ON u.id = a.user_id
            WHERE s.session_token = ?
        ''', (session_token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return JSONResponse({"valid": False, "error": "Invalid session"}, status_code=401)
        
        user_id, user_name, expires_at, phone_number = result
        
        # Check if expired
        if datetime.fromisoformat(expires_at) < datetime.now():
            return JSONResponse({"valid": False, "error": "Session expired"}, status_code=401)
        
        return JSONResponse({
            "valid": True,
            "user_id": user_id,
            "user_name": user_name,
            "phone_number": phone_number or "Not set"
        })
        
    except Exception as e:
        logger.error(f"Session verification error: {e}")
        return JSONResponse({"valid": False, "error": "Verification failed"}, status_code=500)


@app.post("/api/test-elevenlabs-voice")
async def test_elevenlabs_voice(request: Request):
    """Generate a sample audio with selected ElevenLabs voice"""
    try:
        # Parse request
        body = await request.json()
        voice_id = body.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')
        
        # Sample text for testing
        sample_text = "Hello! This is a preview of my voice. I'm here to help answer calls and assist your customers with a natural, friendly conversation. How does this sound?"
        
        # Generate audio using ElevenLabs
        logger.info(f"🔊 Generating test audio with voice ID: {voice_id}")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": CONFIG['ELEVENLABS_API_KEY']
        }
        
        data = {
            "text": sample_text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return JSONResponse(
                    {"success": False, "error": "Failed to generate voice sample"},
                    status_code=500
                )
            
            audio_data = response.content
            logger.info(f"✅ Test audio generated: {len(audio_data)} bytes")
            
            # Return audio as MP3
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=voice_sample.mp3"
                }
            )
        
    except Exception as e:
        logger.error(f"Voice test error: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/api/test-openai-voice")
async def test_openai_voice(request: Request):
    """Generate a sample audio with selected OpenAI voice"""
    try:
        # Parse request
        body = await request.json()
        voice_name = body.get('voice', 'shimmer')
        
        # Sample text for testing
        sample_text = "Hello! This is a preview of my voice. I'm here to help answer calls and assist your customers with a natural, friendly conversation. How does this sound?"
        
        # Generate audio using OpenAI TTS
        logger.info(f"🔊 Generating test audio with OpenAI voice: {voice_name}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {CONFIG['OPENAI_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tts-1",
                    "input": sample_text,
                    "voice": voice_name
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI TTS API error: {response.status_code} - {response.text}")
                return JSONResponse(
                    {"success": False, "error": "Failed to generate voice sample"},
                    status_code=500
                )
            
            audio_data = response.content
            logger.info(f"✅ OpenAI test audio generated: {len(audio_data)} bytes")
            
            # Return audio as MP3
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=openai_voice_sample.mp3"
                }
            )
        
    except Exception as e:
        logger.error(f"OpenAI voice test error: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/api/cartesia-voices")
async def get_cartesia_voices():
    """Get list of popular Cartesia voices (curated selection)"""
    try:
        if not cartesia_client:
            return JSONResponse({"success": False, "error": "Cartesia not configured"}, status_code=400)
        
        # Curated list of popular voices (much faster than fetching all 100+)
        # Focus on UK voices with some variety
        popular_voices = [
            # UK Female Voices
            {"id": "a0e99841-438c-4a64-b679-ae501e7d6091", "name": "British Narration Lady", "description": "Natural UK Female", "language": "en"},
            {"id": "79a125e8-cd45-4c13-8a67-188112f4dd22", "name": "British Reading Lady", "description": "Clear UK Female", "language": "en"},
            {"id": "5619d38c-cf51-4d8e-9575-48f61a280413", "name": "British Lady", "description": "Professional UK Female", "language": "en"},
            {"id": "71a7ad14-091c-4e8e-a314-022ece01c121", "name": "Classy British Lady", "description": "Refined UK Female", "language": "en"},
            {"id": "156fb8d2-335b-4950-9cb3-a2d33befec77", "name": "Friendly Reading Lady", "description": "Warm UK Female", "language": "en"},
            
            # UK Male Voices
            {"id": "694f9389-aac1-45b6-b726-9d9369183238", "name": "Barbershop Man", "description": "Friendly UK Male", "language": "en"},
            {"id": "c2ac25f9-ecc4-4f56-9095-651354df60c0", "name": "British Narration Man", "description": "Professional UK Male", "language": "en"},
            {"id": "41534e16-2966-4c6b-9670-111411def906", "name": "Wise Guide Man", "description": "Authoritative UK Male", "language": "en"},
            {"id": "63ff761f-c1e8-414b-b969-d1833d1c870c", "name": "Kentucky Man", "description": "Deep UK Male", "language": "en"},
            
            # US Female (popular alternatives)
            {"id": "846d6cb0-2301-48b6-9683-48f5618ea2f6", "name": "Newslady", "description": "Professional US Female", "language": "en"},
            {"id": "e3e7c709-0efc-4029-b09a-7868b997bb5e", "name": "Teacher Lady", "description": "Clear US Female", "language": "en"},
            
            # US Male (popular alternatives)
            {"id": "95856005-0332-41b0-935f-352e296aa0df", "name": "Wise Guide", "description": "Calm US Male", "language": "en"},
            {"id": "87748186-23bb-4158-a1eb-332911b0b708", "name": "Newsman", "description": "Professional US Male", "language": "en"},
        ]
        
        return JSONResponse({"success": True, "voices": popular_voices})
        
    except Exception as e:
        logger.error(f"Error loading Cartesia voices: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/update-voice-provider")
async def update_voice_provider(request: Request, authorization: Optional[str] = Header(None)):
    """Update user's voice provider and voice selection"""
    try:
        # Get user_id from auth or body
        user_id = await get_current_user(authorization)
        
        body = await request.json()
        # Allow override from body for backwards compatibility
        if body.get('user_id'):
            user_id = body.get('user_id')
            
        voice_provider = body.get('voice_provider', 'openai')
        openai_voice = body.get('openai_voice')
        elevenlabs_voice_id = body.get('elevenlabs_voice_id')
        cartesia_voice_id = body.get('cartesia_voice_id')
        google_voice = body.get('google_voice')
        playht_voice_id = body.get('playht_voice_id')
        
        if not user_id:
            logger.error(f"update_voice_provider: No user_id - auth: {authorization}, body: {body}")
            return JSONResponse({"success": False, "error": "user_id required"}, status_code=400)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update voice provider
        cursor.execute('''
            UPDATE account_settings 
            SET voice_provider = ?,
                voice = ?,
                elevenlabs_voice_id = ?,
                cartesia_voice_id = ?,
                google_voice = ?,
                playht_voice_id = ?
            WHERE user_id = ?
        ''', (voice_provider, openai_voice, elevenlabs_voice_id, cartesia_voice_id, google_voice, playht_voice_id, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated voice provider for user {user_id}: {voice_provider}")
        
        return JSONResponse({"success": True, "message": "Voice provider updated"})
        
    except Exception as e:
        logger.error(f"Error updating voice provider: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/test-google-voice")
async def test_google_voice(request: Request, authorization: Optional[str] = Header(None)):
    """Generate a sample audio with selected Google Cloud TTS voice"""
    try:
        # Authentication optional for voice testing, but log if authenticated
        user_id = await get_current_user(authorization)
        if user_id:
            logger.info(f"Google voice test for user {user_id}")
        
        body = await request.json()
        voice_name = body.get('voice_name', 'en-GB-Neural2-A')
        
        logger.info(f"🔊 Testing Google voice: {voice_name}")
        
        if not google_tts_client:
            logger.error("Google Cloud TTS client not initialized")
            return JSONResponse({"success": False, "error": "Google Cloud TTS not configured"}, status_code=400)
        
        sample_text = "Hello! This is a preview of my voice. I'm here to help answer calls and assist your customers with a natural, friendly conversation. How does this sound?"
        
        logger.info(f"🔊 Generating test audio with Google voice: {voice_name}")
        
        # Set up synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=sample_text)
        
        # Set up voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-GB",
            name=voice_name
        )
        
        # Set up audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000
        )
        
        # Perform TTS request
        response = google_tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        audio_data = response.audio_content
        logger.info(f"✅ Google TTS test audio generated: {len(audio_data)} bytes")
        
        # Convert raw PCM to WAV format for browser playback
        import wave
        import io
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(audio_data)
        
        wav_data = wav_buffer.getvalue()
        
        # Return as WAV file
        return Response(
            content=wav_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=google_voice_sample.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Google TTS voice test error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/test-cartesia-voice")
async def test_cartesia_voice(request: Request):
    """Generate a sample audio with selected Cartesia voice"""
    try:
        body = await request.json()
        voice_id = body.get('voice_id', 'a0e99841-438c-4a64-b679-ae501e7d6091')
        
        if not cartesia_client:
            return JSONResponse({"success": False, "error": "Cartesia not configured"}, status_code=400)
        
        sample_text = "Hello! This is a preview of my voice. I'm here to help answer calls and assist your customers with a natural, friendly conversation. How does this sound?"
        
        logger.info(f"🔊 Generating test audio with Cartesia voice ID: {voice_id}")
        
        # Generate audio (regular for loop, not async)
        ws = cartesia_client.tts.websocket()
        audio_chunks = []
        
        for chunk in ws.send(
            model_id="sonic-english",
            transcript=sample_text,
            voice={
                "mode": "id",
                "id": voice_id,
            },
            output_format={
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000,
            },
            stream=True
        ):
            # Audio is already raw bytes from Cartesia
            if chunk.audio:
                audio_chunks.append(chunk.audio)
        
        # Combine chunks
        audio_data = b''.join(audio_chunks)
        logger.info(f"✅ Cartesia test audio generated: {len(audio_data)} bytes")
        
        # Convert raw PCM to WAV format for browser playback
        import wave
        import io
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(audio_data)
        
        wav_data = wav_buffer.getvalue()
        
        # Return as WAV file
        return Response(
            content=wav_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=cartesia_voice_sample.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Cartesia voice test error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)



        logger.error(f"Verify error: {e}")
        return JSONResponse({"valid": False, "error": str(e)}, status_code=500)


@app.post("/api/appointments/mark-busy")
async def mark_date_busy(request: Request, authorization: Optional[str] = Header(None)):
    """Mark an entire date as busy"""
    user_id = await get_current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO appointments 
            (date, time, duration, title, status, created_by, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('date'),
            '00:00',
            1440,  # All day (1440 minutes)
            'Busy - All Day',
            'busy',
            'user',
            user_id
        ))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Date {data.get('date')} marked as busy for user {user_id}")
        return {"status": "success", "appointment_id": appointment_id}
    except Exception as e:
        logger.error(f"Failed to mark date busy: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)}
        )


@app.get("/api/admin/ngrok-status")
async def ngrok_status():
    """Check ngrok tunnel status"""
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        data = response.json()
        
        if data.get("tunnels"):
            tunnel = data["tunnels"][0]
            return {
                "running": True,
                "url": tunnel["public_url"],
                "config": tunnel["config"]
            }
        return {"running": False, "message": "No tunnels found"}
    except requests.exceptions.Timeout:
        return {"running": False, "message": "Timeout connecting to ngrok"}
    except requests.exceptions.ConnectionError:
        return {"running": False, "message": "ngrok not responding (not running?)"}
    except Exception as e:
        return {"running": False, "message": f"Error: {str(e)}"}


@app.post("/api/admin/restart")
async def restart_ngrok():
    """Restart ngrok tunnel"""
    try:
        # Kill existing ngrok
        subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                      capture_output=True, shell=True)
        await asyncio.sleep(1)
        
        # Start ngrok on port 5004
        subprocess.Popen(
            ["C:\\ngrok\\ngrok.exe", "http", "5004"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        await asyncio.sleep(3)
        
        # Get new URL
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        data = response.json()
        
        if data.get("tunnels"):
            url = data["tunnels"][0]["public_url"]
            CONFIG["PUBLIC_URL"] = url
            return {"success": True, "url": url, "message": "ngrok restarted"}
        
        return {"success": False, "message": "ngrok started but no tunnel found"}
    except Exception as e:
        logger.error(f"Restart ngrok error: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/admin/restart-ngrok")
async def restart_ngrok_only():
    """Restart ngrok tunnel only"""
    try:
        # Kill existing ngrok
        subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                      capture_output=True, shell=True)
        await asyncio.sleep(2)
        
        # Try to find ngrok in common locations
        ngrok_paths = [
            "C:\\ngrok\\ngrok.exe",
            "ngrok",  # If in PATH
            os.path.expanduser("~/ngrok/ngrok.exe"),
        ]
        
        ngrok_started = False
        for ngrok_path in ngrok_paths:
            try:
                subprocess.Popen(
                    [ngrok_path, "http", "5004"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                ngrok_started = True
                break
            except:
                continue
        
        if not ngrok_started:
            return {"success": False, "message": "Could not find ngrok executable. Please start it manually."}
        
        await asyncio.sleep(3)
        
        # Get new URL
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        data = response.json()
        
        if data.get("tunnels"):
            url = data["tunnels"][0]["public_url"]
            CONFIG["PUBLIC_URL"] = url
            logger.info(f"ngrok restarted with new URL: {url}")
            return {"success": True, "url": url}
        
        return {"success": False, "message": "ngrok started but no tunnel found yet. Wait a few seconds and check status."}
    except Exception as e:
        logger.error(f"Failed to restart ngrok: {e}")
        return {"success": False, "message": str(e)}


@app.get("/api/admin/logs")
async def get_logs():
    """Get recent log entries"""
    # Return last 50 lines from log
    logs = []
    try:
        # In a real implementation, you'd read from a log file
        # For now, return a simple message
        logs = [
            "Logs feature - coming soon",
            "Check terminal/console for detailed logs"
        ]
    except:
        pass
    return {"logs": logs}


@app.post("/api/admin/diagnostics")
async def run_diagnostics():
    """Run comprehensive system diagnostics and auto-fix issues"""
    tests = []
    fixed_count = 0
    failed_count = 0
    
    # Test 1: Check database connectivity
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        tests.append({
            "name": "Database Connection",
            "passed": True,
            "message": f"Connected - {user_count} users found",
            "fixed": False
        })
    except Exception as e:
        tests.append({
            "name": "Database Connection",
            "passed": False,
            "message": f"Failed: {str(e)}",
            "fixed": False
        })
        failed_count += 1
    
    # Test 2: Check if any users have minutes
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM account_settings WHERE minutes_remaining > 0')
        users_with_minutes = cursor.fetchone()[0]
        conn.close()
        
        if users_with_minutes > 0:
            tests.append({
                "name": "User Minutes Available",
                "passed": True,
                "message": f"{users_with_minutes} user(s) have minutes",
                "fixed": False
            })
        else:
            tests.append({
                "name": "User Minutes Available",
                "passed": False,
                "message": "No users have minutes - calls will be rejected",
                "fixed": False
            })
            failed_count += 1
    except Exception as e:
        tests.append({
            "name": "User Minutes Check",
            "passed": False,
            "message": f"Failed: {str(e)}",
            "fixed": False
        })
        failed_count += 1
    
    # Test 3: Check ngrok status
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        data = response.json()
        
        if data.get("tunnels"):
            url = data["tunnels"][0]["public_url"]
            tests.append({
                "name": "ngrok Tunnel",
                "passed": True,
                "message": f"Active: {url}",
                "fixed": False
            })
        else:
            tests.append({
                "name": "ngrok Tunnel",
                "passed": False,
                "message": "No tunnel found - trying to restart...",
                "fixed": False
            })
            
            # Try to auto-fix by restarting ngrok
            try:
                subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                              capture_output=True, shell=True)
                await asyncio.sleep(1)
                
                ngrok_paths = ["C:\\ngrok\\ngrok.exe", "ngrok"]
                for ngrok_path in ngrok_paths:
                    try:
                        subprocess.Popen([ngrok_path, "http", "5004"],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                        await asyncio.sleep(3)
                        
                        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
                        data = response.json()
                        if data.get("tunnels"):
                            url = data["tunnels"][0]["public_url"]
                            tests[-1]["fixed"] = True
                            tests[-1]["fix_message"] = f"Restarted ngrok: {url}"
                            fixed_count += 1
                            break
                    except:
                        continue
            except:
                pass
            
            if not tests[-1].get("fixed"):
                failed_count += 1
                
    except Exception as e:
        tests.append({
            "name": "ngrok Tunnel",
            "passed": False,
            "message": f"Not running: {str(e)}",
            "fixed": False
        })
        failed_count += 1
    
    # Test 4: Check OpenAI API key
    try:
        if CONFIG.get("OPENAI_API_KEY") and len(CONFIG["OPENAI_API_KEY"]) > 20:
            tests.append({
                "name": "OpenAI API Key",
                "passed": True,
                "message": "Configured",
                "fixed": False
            })
        else:
            tests.append({
                "name": "OpenAI API Key",
                "passed": False,
                "message": "Not configured or invalid",
                "fixed": False
            })
            failed_count += 1
    except:
        tests.append({
            "name": "OpenAI API Key",
            "passed": False,
            "message": "Configuration error",
            "fixed": False
        })
        failed_count += 1
    
    # Test 5: Check database schema
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(calls)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "user_id" in columns:
            tests.append({
                "name": "Database Schema",
                "passed": True,
                "message": "Multi-user schema active",
                "fixed": False
            })
        else:
            tests.append({
                "name": "Database Schema",
                "passed": False,
                "message": "Missing user_id column - database needs update",
                "fixed": False
            })
            failed_count += 1
        conn.close()
    except Exception as e:
        tests.append({
            "name": "Database Schema",
            "passed": False,
            "message": f"Failed: {str(e)}",
            "fixed": False
        })
        failed_count += 1
    
    all_passed = failed_count == 0
    
    return {
        "all_passed": all_passed,
        "failed_count": failed_count,
        "fixed_count": fixed_count,
        "tests": tests
    }


@app.get("/test-openai")
async def test_openai():
    """Test OpenAI connection from within the FastAPI context"""
    from websockets import connect
    
    try:
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        api_key = CONFIG['OPENAI_API_KEY']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        logger.info(f"Testing OpenAI connection...")
        logger.info(f"API Key: {api_key[:20]}...{api_key[-10:]}")
        
        ws = await asyncio.wait_for(connect(url, additional_headers=headers), timeout=10.0)
        await ws.close()
        return {"status": "success", "message": "Connected to OpenAI OK!"}
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {"status": "error", "message": str(e)}


@app.api_route("/webhooks/answer", methods=["GET", "POST"])
async def answer_call(request: Request):
    """
    Vonage Answer Webhook
    ---------------------
    Called when an incoming call is received.
    Returns NCCO (Nexmo Call Control Object) to handle the call.
    """
    try:
        if request.method == "POST":
            data = await request.json()
        else:
            data = dict(request.query_params)
    except:
        data = dict(request.query_params)
    
    call_uuid = data.get("uuid", "unknown")
    caller = data.get("from", "unknown")
    called = data.get("to", "unknown")
    
    logger.info(f"📞 Incoming call: {caller} -> {called} (UUID: {call_uuid})")
    
    # Look up which user owns the phone number that was called
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, try to find the user who owns this phone number
    cursor.execute('''
        SELECT a.user_id, a.minutes_remaining, u.name 
        FROM account_settings a 
        JOIN users u ON a.user_id = u.id 
        WHERE a.phone_number = ?
    ''', (called,))
    result = cursor.fetchone()
    
    if not result:
        # No user assigned to this number - reject the call
        conn.close()
        logger.warning(f"⚠️ Call rejected - No user assigned to phone number {called}")
        return JSONResponse([
            {
                "action": "talk",
                "text": "We're sorry, but this phone number is not currently assigned. Please contact support."
            },
            {
                "action": "hangup"
            }
        ])
    
    assigned_user_id = result[0]
    minutes_remaining = result[1]
    user_name = result[2]
    
    if minutes_remaining <= 0:
        # User exists but no minutes
        conn.close()
        logger.warning(f"⚠️ Call rejected - User {user_name} has no credits remaining")
        return JSONResponse([
            {
                "action": "talk",
                "text": "We're sorry, but this account has no credits remaining. Please contact support to add more credits."
            },
            {
                "action": "hangup"
            }
        ])
    
    conn.close()
    logger.info(f"📞 Call assigned to {user_name} (user_id: {assigned_user_id})")
    
    # Create session and connect to OpenAI
    session = await sessions.create_session(call_uuid, caller, called, assigned_user_id)
    connected = await session.connect_to_openai()
    
    if not connected:
        # Fallback if OpenAI connection fails
        return JSONResponse([
            {
                "action": "talk",
                "text": "I'm sorry, I'm having technical difficulties. Please try again later."
            }
        ])
    
    # Start listening for OpenAI responses
    session.start_openai_listener()
    
    # Build WebSocket URL (remove https:// and use wss://)
    ws_host = CONFIG["PUBLIC_URL"].replace("https://", "").replace("http://", "")
    ws_url = f"wss://{ws_host}/socket/{call_uuid}"
    
    # Return NCCO to connect audio via WebSocket
    # The AI agent will handle the greeting
    ncco = [
        {
            "action": "connect",
            "endpoint": [
                {
                    "type": "websocket",
                    "uri": ws_url,
                    "content-type": "audio/l16;rate=16000"
                }
            ]
        }
    ]
    
    logger.info(f"[{call_uuid}] Returning NCCO with WebSocket: {ws_url}")
    return JSONResponse(ncco)


@app.api_route("/webhooks/events", methods=["GET", "POST"])
async def call_events(request: Request):
    """
    Vonage Event Webhook
    --------------------
    Receives call status events (ringing, answered, completed, etc.)
    """
    try:
        if request.method == "POST":
            data = await request.json()
        else:
            data = dict(request.query_params)
    except:
        data = dict(request.query_params)
    
    call_uuid = data.get("uuid", data.get("conversation_uuid", "unknown"))
    status = data.get("status", "unknown")
    
    logger.info(f"📋 Event [{call_uuid}]: {status}")
    
    # Clean up when call ends
    if status in ["completed", "failed", "rejected", "timeout", "cancelled", "busy"]:
        await sessions.close_session(call_uuid)
        logger.info(f"[{call_uuid}] Call ended - session cleaned up")
    
    return JSONResponse({"status": "received"})


@app.websocket("/socket/{call_uuid}")
async def websocket_endpoint(websocket: WebSocket, call_uuid: str):
    """
    WebSocket endpoint for Vonage audio streaming
    ---------------------------------------------
    Vonage streams caller audio here, and we stream responses back.
    """
    await websocket.accept()
    logger.info(f"[{call_uuid}] 🔌 WebSocket connected")
    
    session = sessions.get_session(call_uuid)
    if not session:
        logger.error(f"[{call_uuid}] No session found for WebSocket")
        await websocket.close()
        return
    
    session.vonage_ws = websocket
    
    # Trigger the AI to greet the caller
    try:
        if session.openai_ws:
            await session.openai_ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "Greet the caller warmly. Say hello and ask how you can help them today. Keep it brief and natural."
                }
            }))
            logger.info(f"[{call_uuid}] Triggered greeting")
    except Exception as e:
        logger.error(f"[{call_uuid}] Failed to trigger greeting: {e}")
    
    try:
        while True:
            # Receive audio from Vonage
            data = await websocket.receive()
            
            if "bytes" in data:
                # Audio data from caller
                await session.send_audio_to_openai(data["bytes"])
            elif "text" in data:
                # Could be metadata
                logger.debug(f"[{call_uuid}] Received text: {data['text']}")
                
    except WebSocketDisconnect:
        logger.info(f"[{call_uuid}] 🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"[{call_uuid}] WebSocket error: {e}")
    finally:
        session.vonage_ws = None


# ============================================================================
# SUPER ADMIN ENDPOINTS
# ============================================================================

@app.get("/api/super-admin/stats")
async def get_super_admin_stats():
    """Get overall system statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total accounts
        cursor.execute('SELECT COUNT(*) FROM users')
        total_accounts = cursor.fetchone()[0]
        
        # Total minutes used this month
        cursor.execute('''
            SELECT SUM(total_minutes_purchased - minutes_remaining) 
            FROM account_settings
        ''')
        total_minutes_used = cursor.fetchone()[0] or 0
        
        # Total revenue (assuming $10 per 60 minutes)
        cursor.execute('SELECT SUM(total_minutes_purchased) FROM account_settings')
        total_purchased = cursor.fetchone()[0] or 0
        total_revenue = (total_purchased / 60) * 10
        
        conn.close()
        
        return {
            "total_accounts": total_accounts,
            "total_minutes_used": total_minutes_used,
            "total_revenue": round(total_revenue, 2)
        }
    except Exception as e:
        logger.error(f"Failed to get super admin stats: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/super-admin/calls-today")
async def get_calls_today():
    """Get total calls across all accounts today"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM calls 
            WHERE DATE(start_time) = DATE('now')
        ''')
        total_calls = cursor.fetchone()[0]
        
        conn.close()
        
        return {"total_calls": total_calls}
    except Exception as e:
        logger.error(f"Failed to get calls today: {e}")
        return {"total_calls": 0}


@app.get("/api/super-admin/accounts")
async def get_all_accounts():
    """Get all user accounts with stats"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                u.id as user_id,
                u.name,
                COALESCE(a.minutes_remaining, 0) as minutes_remaining,
                COALESCE(a.total_minutes_purchased, 0) as total_minutes_purchased,
                COALESCE(a.voice, 'shimmer') as voice,
                COALESCE(a.use_elevenlabs, 0) as use_elevenlabs,
                (SELECT COUNT(*) FROM calls c WHERE c.user_id = u.id AND DATE(c.start_time) = DATE('now')) as calls_today,
                (SELECT MAX(start_time) FROM calls c WHERE c.user_id = u.id) as last_call,
                COALESCE(u.status, 'active') as status
            FROM users u
            LEFT JOIN account_settings a ON u.id = a.user_id
            ORDER BY u.id
        ''')
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                "user_id": row[0],
                "name": row[1],
                "minutes_remaining": row[2],
                "total_minutes_purchased": row[3],
                "voice": row[4],
                "use_elevenlabs": bool(row[5]),
                "calls_today": row[6],
                "last_call": row[7],
                "status": row[8]
            })
        
        conn.close()
        return accounts
    except Exception as e:
        logger.error(f"Failed to get accounts: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/super-admin/account/{user_id}")
async def get_account_details(user_id: int):
    """Get detailed account information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                u.id, u.name,
                COALESCE(a.minutes_remaining, 0),
                COALESCE(a.total_minutes_purchased, 0),
                COALESCE(a.voice, 'shimmer'),
                COALESCE(a.use_elevenlabs, 0),
                COALESCE(a.elevenlabs_voice_id, 'EXAVITQu4vr4xnSDxMaL'),
                COALESCE(u.status, 'active'),
                u.suspension_message,
                u.suspended_at,
                u.suspended_by
            FROM users u
            LEFT JOIN account_settings a ON u.id = a.user_id
            WHERE u.id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return JSONResponse({"error": "Account not found"}, status_code=404)
        
        return {
            "user_id": row[0],
            "name": row[1],
            "minutes_remaining": row[2],
            "total_minutes_purchased": row[3],
            "voice": row[4],
            "use_elevenlabs": bool(row[5]),
            "elevenlabs_voice_id": row[6],
            "status": row[7],
            "suspension_message": row[8],
            "suspended_at": row[9],
            "suspended_by": row[10]
        }
    except Exception as e:
        logger.error(f"Failed to get account details: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/super-admin/account/{user_id}/calls")
async def get_account_calls(user_id: int):
    """Get call history for specific account"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT call_uuid, caller_number, start_time, end_time, duration, summary
            FROM calls
            WHERE user_id = ?
            ORDER BY start_time DESC
            LIMIT 50
        ''', (user_id,))
        
        calls = []
        for row in cursor.fetchall():
            calls.append({
                "call_uuid": row[0],
                "caller_number": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "duration": row[4],
                "summary": row[5]
            })
        
        conn.close()
        return calls
    except Exception as e:
        logger.error(f"Failed to get account calls: {e}")
        return []


@app.get("/api/super-admin/activity")
async def get_recent_activity():
    """Get recent system activity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.start_time as timestamp,
                'Call from ' || c.caller_number || ' to user ' || u.name as message
            FROM calls c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.start_time DESC
            LIMIT 20
        ''')
        
        activity = []
        for row in cursor.fetchall():
            activity.append({
                "timestamp": row[0],
                "message": row[1]
            })
        
        conn.close()
        return activity
    except Exception as e:
        logger.error(f"Failed to get activity: {e}")
        return []


@app.post("/api/super-admin/account/{user_id}/add-minutes")
async def add_minutes_to_account(user_id: int, request: Request):
    """Add minutes to user account"""
    try:
        body = await request.json()
        minutes = body.get('minutes', 0)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE account_settings
            SET minutes_remaining = minutes_remaining + ?,
                total_minutes_purchased = total_minutes_purchased + ?
            WHERE user_id = ?
        ''', (minutes, minutes, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added {minutes} minutes to user {user_id}")
        return {"success": True, "minutes_added": minutes}
    except Exception as e:
        logger.error(f"Failed to add minutes: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/super-admin/account/{user_id}/reset")
async def reset_account(user_id: int):
    """Reset account data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete calls
        cursor.execute('DELETE FROM calls WHERE user_id = ?', (user_id,))
        
        # Delete appointments
        cursor.execute('DELETE FROM appointments WHERE user_id = ?', (user_id,))
        
        # Reset account settings
        cursor.execute('''
            UPDATE account_settings
            SET minutes_remaining = 0,
                total_minutes_purchased = 0
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Reset account for user {user_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to reset account: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/super-admin/account/{user_id}/suspend")
async def suspend_account(user_id: int, request: Request):
    """Suspend account with message"""
    try:
        body = await request.json()
        message = body.get('message', 'Your account has been suspended.')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET status = 'suspended',
                suspension_message = ?,
                suspended_at = CURRENT_TIMESTAMP,
                suspended_by = 'Admin'
            WHERE id = ?
        ''', (message, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Suspended account {user_id} with message: {message}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to suspend account: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/super-admin/account/{user_id}/ban")
async def ban_account(user_id: int):
    """Ban account permanently"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET status = 'banned',
                suspension_message = 'Your account has been permanently banned.',
                suspended_at = CURRENT_TIMESTAMP,
                suspended_by = 'Admin'
            WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Banned account {user_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to ban account: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/super-admin/account/{user_id}/reactivate")
async def reactivate_account(user_id: int):
    """Reactivate suspended or banned account"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET status = 'active',
                suspension_message = NULL,
                suspended_at = NULL,
                suspended_by = NULL
            WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Reactivated account {user_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to reactivate account: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/super-admin/backup")
async def create_backup():
    """Create database backup"""
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"call_logs_backup_{timestamp}.db"
        
        shutil.copy2('call_logs.db', backup_file)
        
        logger.info(f"Created backup: {backup_file}")
        return {"success": True, "backup_file": backup_file}
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/super-admin/export-reports")
async def export_reports():
    """Export usage reports as CSV"""
    try:
        import csv
        from io import StringIO
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                u.id, u.name,
                COALESCE(a.minutes_remaining, 0),
                COALESCE(a.total_minutes_purchased, 0),
                (SELECT COUNT(*) FROM calls c WHERE c.user_id = u.id) as total_calls
            FROM users u
            LEFT JOIN account_settings a ON u.id = a.user_id
            ORDER BY u.id
        ''')
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['User ID', 'Name', 'Minutes Remaining', 'Total Purchased', 'Total Calls'])
        
        for row in cursor.fetchall():
            writer.writerow(row)
        
        conn.close()
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=usage_report.csv"}
        )
    except Exception as e:
        logger.error(f"Failed to export reports: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/super-admin/global-instructions")
async def get_global_instructions():
    """Get current global instructions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT global_instructions, last_updated, updated_by FROM global_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "success": True,
                "global_instructions": result[0] or "",
                "last_updated": result[1],
                "updated_by": result[2]
            }
        else:
            return {
                "success": True,
                "global_instructions": "",
                "last_updated": None,
                "updated_by": None
            }
    except Exception as e:
        logger.error(f"Failed to get global instructions: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/super-admin/global-instructions")
async def update_global_instructions(request: Request):
    """Update global instructions that apply to all AI agents"""
    try:
        body = await request.json()
        global_instructions = body.get('global_instructions', '')
        updated_by = body.get('updated_by', 'admin')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE global_settings 
            SET global_instructions = ?, 
                last_updated = CURRENT_TIMESTAMP,
                updated_by = ?
            WHERE id = 1
        ''', (global_instructions, updated_by))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Global instructions updated by {updated_by}")
        return {
            "success": True,
            "message": "Global instructions updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update global instructions: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def print_setup_instructions():
    """Print setup instructions (ASCII only to avoid encoding issues)."""
    lines = [
        "",
        "======================================================================",
        "  VONAGE VOICE AGENT - Control Panel",
        "======================================================================",
        "",
        "  Web Interface: http://localhost:5004",
        "",
        "  Configure your AI agent through the web interface!",
        "",
        "  STEP 1: Start ngrok (in another terminal)",
        "  ngrok http 5004",
        "",
        "  STEP 2: Set Vonage webhooks in your Voice Application:",
        ""
    ]
    try:
        for line in lines:
            print(line)
    except UnicodeEncodeError:
        # Absolute fallback: write via stdout.buffer to bypass encoding
        for line in lines:
            sys.stdout.buffer.write((line + "\n").encode("ascii", "ignore"))
        sys.stdout.flush()

    ascii_block = [
        "  +-------------------------------------------------------------+",
        "  |  Answer URL:  https://YOUR_NGROK_URL/webhooks/answer        |",
        "  |  Event URL:   https://YOUR_NGROK_URL/webhooks/events        |",
        "  |  HTTP Method: POST (for both)                               |",
        "  +-------------------------------------------------------------+",
        "",
        "  STEP 3: Call your Vonage phone number!",
        "",
        "=" * 70,
        ""
    ]
    try:
        for line in ascii_block:
            print(line)
    except UnicodeEncodeError:
        for line in ascii_block:
            sys.stdout.buffer.write((line + "\n").encode("ascii", "ignore"))
        sys.stdout.flush()


if __name__ == "__main__":
    print_setup_instructions()
    
    print(f"Starting server on http://{CONFIG['HOST']}:{CONFIG['PORT']}")
    print()
    
    uvicorn.run(
        app,
        host=CONFIG["HOST"],
        port=CONFIG["PORT"],
        log_level="info"
    )
