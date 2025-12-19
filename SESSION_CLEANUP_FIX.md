# Session Cleanup Fix - Call Answer Failure Issue

## Problem Description
AI would answer first 1-2 calls perfectly, then subsequent calls would pick up but AI wouldn't respond (silence). Server restart was required to fix.

## Root Causes Identified

### 1. **Missing Vonage WebSocket Cleanup**
The `CallSession.close()` method was closing the OpenAI WebSocket and Speechmatics HTTP client, but **NOT** explicitly closing the Vonage WebSocket (`self.vonage_ws`). This caused WebSocket connections to accumulate.

### 2. **No Duplicate Session Prevention**
When creating a new session, the system didn't check if a session with the same `call_uuid` already existed. If the previous session wasn't properly cleaned up, it could cause conflicts.

### 3. **Insufficient Logging**
Limited logging made it difficult to diagnose when and how sessions were being cleaned up or if resources were properly released.

## Changes Made

### 1. Enhanced CallSession.close() Method
**Location**: `vonage_agent.py` lines ~3182-3240

**Added**:
- Explicit closure of Vonage WebSocket with error handling
- Better logging for each cleanup step
- Clear confirmation when all resources are released

```python
# Close OpenAI WebSocket
if self.openai_ws:
    try:
        await self.openai_ws.close()
        logger.info(f"[{self.call_uuid}] ✓ Closed OpenAI WebSocket")
    except Exception as e:
        logger.warning(f"[{self.call_uuid}] Error closing OpenAI WS: {e}")
    self.openai_ws = None

# Close Vonage WebSocket  
if self.vonage_ws:
    try:
        await self.vonage_ws.close()
        logger.info(f"[{self.call_uuid}] ✓ Closed Vonage WebSocket")
    except Exception as e:
        logger.warning(f"[{self.call_uuid}] Error closing Vonage WS: {e}")
    self.vonage_ws = None

# Close Speechmatics HTTP client
if hasattr(self, '_speechmatics_client'):
    try:
        await self._speechmatics_client.aclose()
        logger.info(f"[{self.call_uuid}] ✓ Closed Speechmatics HTTP client")
    except Exception as e:
        logger.warning(f"[{self.call_uuid}] Error closing Speechmatics client: {e}")
```

### 2. Duplicate Session Prevention
**Location**: `SessionManager.create_session()` lines ~3244-3250

**Added**:
- Check if session with same UUID already exists
- Clean up old session before creating new one
- Logging to track when this occurs

```python
async def create_session(self, call_uuid: str, caller: str = "", called: str = "", user_id: Optional[int] = None) -> CallSession:
    """Create a new call session"""
    # Clean up any existing session with same UUID first
    if call_uuid in self._sessions:
        logger.warning(f"[{call_uuid}] Cleaning up existing session before creating new one")
        await self.close_session(call_uuid)
    
    session = CallSession(call_uuid, caller, called)
    session.user_id = user_id
    # ...
```

### 3. Enhanced SessionManager Logging
**Location**: `SessionManager` class methods

**Added**:
- Detailed logging when sessions are closed
- Track active session count after operations
- Warning when attempting to close non-existent session

```python
async def close_session(self, call_uuid: str):
    """Close and remove a session"""
    if call_uuid in self._sessions:
        logger.info(f"[{call_uuid}] Closing and removing session from SessionManager")
        await self._sessions[call_uuid].close()
        del self._sessions[call_uuid]
        logger.info(f"[{call_uuid}] Session removed. Active sessions: {len(self._sessions)}")
    else:
        logger.warning(f"[{call_uuid}] Attempted to close non-existent session")
```

### 4. New SessionManager Methods
**Location**: `SessionManager` class

**Added**:
- `get_active_session_count()` - Returns number of active sessions
- `get_all_session_uuids()` - Returns list of all active session UUIDs

These methods enable monitoring and debugging of session state.

### 5. Enhanced Health Endpoint
**Location**: `/api/health` endpoint lines ~7515-7560

**Added**:
- Active session count in health response
- List of active session UUIDs
- Better visibility into system state

```python
# Get active session info
active_session_count = sessions.get_active_session_count()
active_session_uuids = sessions.get_all_session_uuids()

return {
    # ... other health data
    "sessions": {
        "active_count": active_session_count,
        "uuids": active_session_uuids
    }
}
```

## Testing Instructions

1. **Start the server** and make a test call - verify AI answers
2. **End the call** and check logs for cleanup messages:
   - Look for "🧹 Starting session cleanup..."
   - Verify "✓ Closed OpenAI WebSocket"
   - Verify "✓ Closed Vonage WebSocket"
   - Verify "✓ Closed Speechmatics HTTP client"
   - Confirm "✅ Session cleanup completed - all resources released"

3. **Make 5+ consecutive calls** to the same number
   - Each call should answer with AI greeting
   - No silence or failed answers
   - No need to restart server

4. **Check health endpoint** (`/api/health`) after calls
   - Verify `sessions.active_count` is 0 when no calls active
   - Verify `sessions.uuids` is empty array when idle

5. **Monitor logs** for any warnings:
   - "Cleaning up existing session before creating new one" (should be rare)
   - "Attempted to close non-existent session" (should not occur)

## Expected Behavior After Fix

✅ **First Call**: AI answers and greets caller  
✅ **Second Call**: AI answers and greets caller (no restart needed)  
✅ **Subsequent Calls**: Continue to work reliably  
✅ **Session Count**: Returns to 0 after each call ends  
✅ **Resource Usage**: Stable, no accumulation of connections  
✅ **Logs**: Clear cleanup confirmation after each call  

## Monitoring Commands

```bash
# Watch active sessions in real-time
curl http://localhost:5004/api/health | grep -A 5 "sessions"

# Check server logs for cleanup
# Look for patterns:
# - "Session cleanup completed"
# - "Session removed. Active sessions: 0"
# - "Closed OpenAI WebSocket"
# - "Closed Vonage WebSocket"
```

## Roll Back Plan

If issues persist, the changes are isolated to:
1. `CallSession.close()` method
2. `SessionManager.create_session()` method
3. `SessionManager.close_session()` method
4. `/api/health` endpoint

Previous behavior can be restored by reverting changes to these methods.

## Additional Notes

- Timeout monitoring already exists (`_timeout_task`) - no changes needed
- Background task for summary generation remains unchanged
- OpenAI connection retry logic (3 attempts) remains unchanged
- No changes to call routing or NCCO generation
