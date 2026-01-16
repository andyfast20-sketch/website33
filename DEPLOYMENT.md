# DEPLOYMENT GUIDE - Voice Agent Server

## Prerequisites on New Server
- Python 3.10 or 3.11 (check: `python --version`)
- Git installed
- VS Code installed (for GitHub Copilot)

## Step 1: Clone Repository
```bash
git clone https://github.com/andyfast20-sketch/website33.git
cd website33/website33-main/website33-main
```

## Step 2: Create Virtual Environment
```bash
python -m venv .venv
```

**Windows:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

## Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**If errors occur:**
- PyAudio issues on Windows: `pip install pipwin && pipwin install pyaudio`
- On Linux: `sudo apt-get install portaudio19-dev python3-pyaudio`

## Step 4: Copy Database File
Transfer `call_logs.db` from old server to new server (same directory as vonage_agent.py)

**Important:** Database contains encrypted credentials, so you MUST copy it, don't create a new one.

## Step 5: Copy Google Credentials (if using Google TTS)
Transfer `google-credentials.json` if it exists

## Step 6: Test Server
```bash
python vonage_agent.py
```

Should see: `Uvicorn running on http://0.0.0.0:5004`

## Step 7: Install GitHub Copilot in VS Code
1. Open VS Code on new server
2. Install "GitHub Copilot" extension
3. Sign in with your GitHub account
4. Open the project folder: `website33-main/website33-main`

## Troubleshooting

### "Module not found" errors
```bash
pip install [missing-module-name]
```

### Port 5004 already in use
```bash
# Windows
netstat -ano | findstr :5004
taskkill /PID [PID_NUMBER] /F

# Linux
lsof -i :5004
kill -9 [PID]
```

### Database locked
Make sure old server is stopped before copying database

### Audio device errors
Server doesn't need audio devices - ignore these warnings

## Files You MUST Copy
1. ✅ call_logs.db (contains all credentials and settings)
2. ✅ google-credentials.json (if using Google TTS)
3. ✅ static/ folder (all HTML files)
4. ✅ vonage_agent.py (main server file)
5. ✅ filler_audios/ folder (if it exists)

## Files You DON'T Need to Copy
- ❌ .venv/ (create fresh on new server)
- ❌ __pycache__/
- ❌ *.log files
- ❌ server_log*.txt files
