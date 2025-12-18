# Vapi Migration Guide

## Current Status: ✅ REALTIME MODE (Working)
Your system is currently using OpenAI Realtime mode. Calls work normally.

## When Ready to Switch to Vapi:

### Step 1: Create Vapi Assistant
1. Log into Vapi Dashboard: https://dashboard.vapi.ai
2. Go to **Assistants** → **Create Assistant**
3. Configure:
   - **Name:** Judie (or your agent name)
   - **First Message:** "Hello! This is Judie from [business name]. How can I help you today?"
   - **Model:** GPT-4o-mini (cost-effective)
   - **Voice Provider:** ElevenLabs
   - **Voice ID:** Use your ElevenLabs voice ID: `EXAVITQu4vr4xnSDxMaL`
   - **System Prompt:** Copy from your account settings business info
   
4. **Server URL (Function Calling):**
   ```
   https://unfasciate-unsurlily-suzanna.ngrok-free.dev/webhooks/vapi-callback
   ```

5. **Status Callback URL:**
   ```
   https://unfasciate-unsurlily-suzanna.ngrok-free.dev/webhooks/vapi-status
   ```

6. Save the assistant and **copy the Assistant ID**

---

### Step 2: Import Your Vonage Number to Vapi

⚠️ **IMPORTANT:** This will disconnect the number from your current system!

1. In Vonage Dashboard (https://dashboard.nexmo.com/):
   - Go to **Your Applications**
   - Find your Voice Application
   - Click **"Unlink Numbers"**
   - Unlink `+442039856179`

2. In Vapi Dashboard:
   - Go to **Phone Numbers** → **Create Phone Number**
   - Select **"Import Vonage"**
   - Enter phone number: `+44 20 3985 6179`
   - Select your assistant from Step 1
   - Click **"Import"**

3. ✅ **Your number is now managed by Vapi**

---

### Step 3: Test the Vapi System

1. Call your number: `+44 20 3985 6179`
2. Vapi should answer with your ElevenLabs voice
3. Test conversation quality
4. Check call logs in Vapi dashboard
5. Verify webhooks are received in your server logs (look for "Vapi status" messages)

---

### Step 4: Monitor Costs

- Vapi charges: **$0.05-0.10 per minute**
- Previous cost: **$0.30 per minute**
- Savings: **3-6x cheaper**

Check your Vapi dashboard for real-time billing.

---

## How to Switch BACK to Original System

If Vapi doesn't work or you want to go back:

### 1. Remove Number from Vapi
- In Vapi Dashboard → Phone Numbers
- Find your number
- Click **"Delete"** or **"Remove"**

### 2. Re-link to Vonage Application
- In Vonage Dashboard (https://dashboard.nexmo.com/)
- Go to **Your Applications** → Your Voice App
- Click **"Link Numbers"**
- Select `+442039856179`
- Link it back

### 3. Verify Webhooks
Make sure your Vonage application still has:
- **Answer URL:** `https://unfasciate-unsurlily-suzanna.ngrok-free.dev/webhooks/answer`
- **Event URL:** `https://unfasciate-unsurlily-suzanna.ngrok-free.dev/webhooks/events`
- **HTTP Method:** POST

### 4. Test Call
Call your number - it should work through your original system again.

---

## What Your App Does in Vapi Mode

**Your app KEEPS working**, but its role changes:

### Before (Current Mode):
- Handles calls directly via WebSocket
- Manages OpenAI Realtime API
- Controls entire conversation flow

### After (Vapi Mode):
- **Vapi handles calls** (you don't touch them)
- Your app receives **webhooks** for:
  - Call status updates
  - Function calling (appointments, etc.)
  - Call transcripts
  - Billing info
- Your **admin panel** still works for:
  - User management
  - Business configuration
  - Call logs (from Vapi webhooks)
  - Reporting

---

## Benefits of Vapi

✅ **Better voice quality** - ElevenLabs voices sound more natural
✅ **Faster responses** - 300-600ms vs 500-900ms
✅ **Lower cost** - $0.05-0.10/min vs $0.30/min
✅ **Less maintenance** - Vapi handles infrastructure
✅ **Reliability** - Production-grade system

## Downsides

❌ **Less control** - Can't modify conversation logic in real-time
❌ **Dependency** - Relies on Vapi's uptime
❌ **Learning curve** - Need to learn Vapi's assistant configuration

---

## Support

If you have issues:
1. Check Vapi docs: https://docs.vapi.ai
2. Check server logs: Look for "Vapi" messages
3. Test webhooks are working: `/webhooks/vapi-callback` and `/webhooks/vapi-status`
4. Vapi support: support@vapi.ai

---

## Next Steps

When you're ready to migrate:
1. Follow Step 1-3 above
2. Test thoroughly
3. Monitor for issues
4. If problems occur, follow "Switch BACK" instructions

**Your current system will keep working until you complete Step 2!**
