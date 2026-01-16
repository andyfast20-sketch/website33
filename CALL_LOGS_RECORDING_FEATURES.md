# Call Logs & Recording Features - Implementation Summary

## Overview
Added comprehensive call logging, transcription, and recording capabilities for both traditional (Speechmatics/OpenAI) and Vapi assistant calls.

## Changes Made

### 1. Database Schema
- **Added Column**: `recording_url` to `calls` table
- Stores URLs for call recordings from both Vonage and Vapi

### 2. Vapi Webhook Integration
Added two new webhook endpoints to receive call data from Vapi:

#### `/webhooks/vapi-end-of-call` (POST)
- Receives complete call data after call ends
- Extracts transcript from Vapi messages
- Stores recording URLs (supports both mono and stereo recordings)
- Matches Vapi calls to existing database records by phone number and timing
- Triggers AI summary generation automatically
- **Configure in Vapi Dashboard**: Server URL → End-of-Call Callback

#### `/webhooks/vapi-status` (POST)
- Receives real-time status updates during calls
- Logs call progress (started, transcript updates, ended)
- **Configure in Vapi Dashboard**: Status Callback URL

### 3. Vonage Call Recording
Added automatic recording for all Vonage calls:

#### `/webhooks/recording` (POST)
- Receives recording URL when Vonage finishes processing the recording
- Updates database with recording URL
- Recordings are in MP3 format with stereo (2 channels)
- Channel 1: Customer, Channel 2: Agent

#### Modified `/webhooks/answer`
- Added `record` action before `connect` in NCCO
- Settings:
  - Format: MP3
  - Channels: 2 (stereo - separate customer/agent tracks)
  - Max duration: 2 hours
  - No beep when recording starts
  - Ends after 3 seconds of silence

### 4. DailyBotSession Updates
Modified Vapi call handling to save call logs:

#### `cleanup()` method
- Now calls `CallLogger.log_call_end()` when Vapi calls end
- Saves placeholder transcript: "(Transcript pending from Vapi webhook)"
- Actual transcript arrives later via `/webhooks/vapi-end-of-call`

### 5. API Updates
Modified `CallLogger.get_recent_calls()`:
- Added `recording_url` to SELECT query
- Returns recording URL in API response for frontend display

### 6. Admin UI Enhancements
Updated `viewCallSummary()` function in [admin.html](static/admin.html):
- Added audio player when `recording_url` is available
- Shows 🎧 Call Recording section with:
  - HTML5 `<audio>` player (supports MP3/WAV)
  - Download link for recordings
  - Styled purple/pink theme to distinguish from transcript

## Configuration Required

### For Vapi Calls (if using Vapi assistants):
1. Go to Vapi Dashboard: https://dashboard.vapi.ai
2. For each assistant, configure webhooks:
   - **Server URL (End-of-Call)**: `https://YOUR_DOMAIN/webhooks/vapi-end-of-call`
   - **Status Callback URL**: `https://YOUR_DOMAIN/webhooks/vapi-status`

Replace `YOUR_DOMAIN` with your public URL (Cloudflare tunnel or ngrok).

### For Vonage Recordings:
- No additional configuration needed
- Recording starts automatically for all calls
- Vonage stores recordings in their cloud
- URLs are temporary (typically expire after 30 days)
- To keep recordings permanently, download them via the admin interface

## How It Works

### Traditional Calls (OpenAI/Speechmatics):
1. Call starts → Vonage records audio
2. Call ends → CallSession logs transcript immediately
3. Vonage processes recording → Sends URL to `/webhooks/recording`
4. Admin sees transcript + recording

### Vapi Calls:
1. Call starts → Vonage/Vapi records audio (if enabled in Vapi)
2. Call ends → DailyBotSession saves basic log
3. Vapi processes call → Sends transcript + recording to `/webhooks/vapi-end-of-call`
4. Webhook updates database with transcript and recording URL
5. Admin sees transcript + recording

## Testing

1. Make a test call to your Vonage number
2. Check server logs for:
   ```
   📼 Recording webhook for [uuid]: [url]
   ✅ Recording URL saved for [uuid]
   ```
3. In admin panel, view the call
4. You should see the recording player in the call summary

## Files Modified
- [vonage_agent.py](vonage_agent.py) - Added webhooks, modified call logging
- [static/admin.html](static/admin.html) - Updated UI to show recordings
- [add_recording_url_column.py](add_recording_url_column.py) - Database migration (already run)

## Notes
- Recordings are stored by Vonage/Vapi, not on your server
- URLs are typically temporary (check provider documentation for expiry)
- For long-term storage, download recordings and store locally
- Stereo recordings allow separate analysis of customer vs agent audio
- Vapi may charge extra for recording features (check your Vapi plan)
