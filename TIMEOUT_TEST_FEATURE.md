# Timeout Test Feature - Implementation Summary

## Overview
Added a testing feature in the Super Admin panel that allows you to test AI agent response behavior when it takes too long to respond. When enabled, if the AI agent doesn't start producing audio within a configurable timeout period, a "deleted response" audio message is automatically played.

## What Was Added

### 1. Database Changes
- **Migration Script**: [add_timeout_test_columns.py](add_timeout_test_columns.py)
  - Added `timeout_test_enabled` (INTEGER, default 0) - Enable/disable the feature
  - Added `timeout_test_seconds` (REAL, default 2.0) - Timeout threshold in seconds
  - Both columns added to `global_settings` table

### 2. Super Admin UI ([static/super-admin_current.html](static/super-admin_current.html))
- Added new "Testing Features" panel with:
  - Toggle checkbox to enable/disable timeout test
  - Number input to configure timeout value (0.5 - 10.0 seconds)
  - Save and Reload buttons
  - Status indicator
- Panel is located before the "Global Instructions" section
- Settings are loaded automatically when the Super Admin page loads

### 3. Backend API Endpoints ([vonage_agent.py](vonage_agent.py))
- **GET** `/api/super-admin/timeout-test-settings` - Retrieves current settings
- **POST** `/api/super-admin/timeout-test-settings` - Updates settings
  - Validates timeout between 0.5 and 10.0 seconds
  - Updates CONFIG immediately (no restart required)
  - Settings persist in database

### 4. Timeout Detection Logic ([vonage_agent.py](vonage_agent.py))
- Added to `VonageCallSession` class:
  - `_timeout_test_task` - Background task monitoring timeout
  - `_timeout_test_triggered` - Flag to prevent duplicate audio playback
  - `_start_timeout_test_monitor()` - Starts monitoring when response is triggered
  - `_monitor_timeout_test()` - Checks if timeout exceeded and plays audio
  - `_generate_and_play_timeout_audio()` - Generates "deleted response" audio using Speechmatics TTS
- Timeout monitoring starts when ANY brain provider triggers a response:
  - OpenAI Realtime
  - DeepSeek
  - Groq
  - Grok (xAI)
  - OpenRouter
- Automatically cancelled when new turn starts or audio begins playing

### 5. Settings Loading ([vonage_agent.py](vonage_agent.py))
- `load_timeout_test_settings()` - Loads settings from database on startup
- Called automatically after backchannel settings load
- Defaults to disabled (enabled=False, seconds=2.0)

## How It Works

1. **Super Admin enables the feature**: Toggle the checkbox and set desired timeout (e.g., 2.0 seconds)
2. **During a call**: When the AI agent is triggered to respond:
   - A timeout monitoring task starts
   - If the AI doesn't start sending audio within the timeout period
   - "Deleted response" audio is generated and played using Speechmatics TTS
   - Logged as: `⏰ TIMEOUT TEST: AI response exceeded Xs - playing 'deleted response' audio`
3. **If AI responds in time**: The timeout task completes normally without playing audio
4. **Turn cleanup**: Timeout task is automatically cancelled when:
   - A new caller turn begins
   - The audio starts playing normally
   - The call ends

## Usage

### Enable the Feature
1. Go to Super Admin panel (http://your-server/super-admin)
2. Scroll to "🧪 Testing Features" panel
3. Check "Play deleted response if AI takes too long to respond"
4. Set timeout value (default: 2.0 seconds)
5. Click "💾 Save Testing Settings"

### Change Timeout Value
- Minimum: 0.5 seconds
- Maximum: 10.0 seconds
- Default: 2.0 seconds
- Can be changed anytime without restarting the server

### Disable the Feature
1. Uncheck the "Response Timeout Test" checkbox
2. Click "💾 Save Testing Settings"

## Technical Details

### Audio Generation
- Uses Speechmatics TTS API (same as the voice provider)
- Generates "Deleted response." message in Sarah voice
- Format: PCM 16-bit signed little-endian, 16kHz sample rate
- Sent directly to Vonage WebSocket (no file storage needed)

### Performance Impact
- Minimal: Only active when enabled
- Task is lightweight (just waits and checks a flag)
- Automatically cancelled if not needed

### Thread Safety
- Task creation/cancellation is exception-safe
- Uses asyncio properly for concurrent operations
- Per-turn flags prevent race conditions

## Files Modified

1. ✅ `add_timeout_test_columns.py` (NEW) - Database migration
2. ✅ `static/super-admin_current.html` - UI controls and JavaScript
3. ✅ `vonage_agent.py` - Backend logic, API endpoints, timeout monitoring

## Testing Recommendations

1. **Basic Test**: Enable feature with 2s timeout, make a call, verify audio plays if AI is slow
2. **Adjustment Test**: Change timeout to different values (0.5s, 5s, 10s) and verify behavior
3. **Disable Test**: Turn off feature and verify no timeout audio plays
4. **Fast Response Test**: With feature enabled, verify timeout audio doesn't play when AI responds quickly
5. **Multiple Turns**: Verify timeout monitoring works correctly across multiple conversation turns

## Notes

- This is a **testing/development feature** - use it to diagnose slow AI responses
- The "deleted response" audio will interrupt the natural flow of conversation
- Recommended to keep disabled in production unless actively testing
- Settings are saved in the database and persist across server restarts
- Changes take effect immediately (no server restart required)
