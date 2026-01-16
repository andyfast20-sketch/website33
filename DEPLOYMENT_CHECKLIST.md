# 📦 DEPLOYMENT PACKAGE CHECKLIST

## Before You Copy to New Server

### ✅ Files to Include (Required)

Copy these to your new server:

```
📁 Project Root/
├── 📄 DEPLOY.bat                  ⭐ RUN THIS FIRST!
├── 📄 DEPLOYMENT_GUIDE.md         📖 Complete instructions
├── 📄 requirements.txt            📦 Python dependencies
├── 📄 setup_database.py           🗄️ Database setup
├── 📄 start_server_clean.py       🚀 Server startup script
├── 📄 vonage_agent.py             🤖 Main application
├── 📄 .env.example                ⚙️ Configuration template
├── 📄 README.md                   
└── 📁 static/                     (if exists)
└── 📁 agent/                      (if exists)
└── (all other .py files)
```

### ❌ Files to EXCLUDE (Do Not Copy)

These will be regenerated on new server:

```
❌ .venv/                   (Virtual environment - will be recreated)
❌ __pycache__/             (Python cache)
❌ *.pyc                    (Compiled Python files)
❌ .env                     (YOUR KEYS - configure manually on new server!)
❌ *.db                     (Databases - fresh start on new server)
❌ *.log                    (Log files)
❌ *.wav                    (Debug audio files)
```

### ⚠️ IMPORTANT: DO NOT COPY YOUR .env FILE!

Your `.env` file contains YOUR API keys. Instead:
1. Copy `.env.example` to new server
2. The DEPLOY script will create a new `.env` from the template
3. Then add your API keys to the new `.env`

---

## What to Bring Separately

### 🔑 Your API Keys (Keep Secure!)

Have these ready to enter on the new server:

```
□ OpenAI API Key (REQUIRED)
□ Vonage API Key (REQUIRED)
□ Vonage API Secret (REQUIRED)
□ ElevenLabs API Key (optional)
□ Google Cloud credentials JSON file (optional)
□ Deepgram API Key (optional)
□ Any other service API keys you use
```

### 💾 Optional: Your Data

If migrating from existing server:

```
□ call_logs.db (your call history & settings)
□ Any custom configuration files
□ Backup of working .env (for reference only)
```

---

## Installation Prerequisites on New Server

Before running DEPLOY.bat, install these:

### 1. Python 3.10+
- Download: https://www.python.org/downloads/
- ⚠️ CHECK "Add Python to PATH" during install!
- Verify: `python --version`

### 2. ngrok (for public access)
- Download: https://ngrok.com/download
- Extract to: `C:\ngrok\`
- Or install anywhere and update `.env`

### 3. (Optional) Visual C++ Redistributable
- Some audio packages may require this
- Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## Quick Deployment Steps on New Server

### 📝 Copy & Paste Version:

```batch
# 1. Copy entire project folder to new server

# 2. Open Command Prompt in project folder

# 3. Run the deployment script
DEPLOY.bat

# 4. Wait 5-10 minutes for installation

# 5. Edit .env file with your API keys when prompted

# 6. Start server when ready
```

That's it! ✅

---

## Package Transfer Methods

### Option 1: ZIP File (Recommended)
1. Select all project files (excluding .venv, __pycache__, *.db, .env)
2. Right-click → Send to → Compressed (zipped) folder
3. Transfer ZIP to new server
4. Extract and run DEPLOY.bat

### Option 2: Git Clone
```batch
git clone <your-repo-url>
cd <project-folder>
DEPLOY.bat
```

### Option 3: Network Share
1. Copy project folder to network location
2. Access from new server
3. Copy locally and run DEPLOY.bat

### Option 4: USB Drive
1. Copy to USB
2. Transfer to new server
3. Run DEPLOY.bat

---

## Estimated Installation Time

| Step | Duration |
|------|----------|
| File transfer | 1-5 min (depending on method) |
| Running DEPLOY.bat | 5-10 min |
| Configuring .env | 2-3 min |
| First server start | 1 min |
| **TOTAL** | **10-20 min** |

---

## Post-Deployment Verification

After DEPLOY.bat completes:

```batch
# 1. Check Python
python --version

# 2. Check virtual environment exists
dir .venv

# 3. Check database created
dir call_logs.db

# 4. Check .env exists
type .env

# 5. Start server
.venv\Scripts\activate
python start_server_clean.py

# 6. Open browser
start http://localhost:5004
```

---

## Troubleshooting Checklist

If deployment fails:

- [ ] Python installed? → `python --version`
- [ ] Python in PATH? → Reinstall with "Add to PATH" checked
- [ ] Internet connection? → Check network
- [ ] Antivirus blocking? → Temporarily disable
- [ ] Enough disk space? → Need 2GB+ free
- [ ] Running as admin? → Try right-click → Run as administrator
- [ ] Previous .venv exists? → Delete it and re-run DEPLOY.bat

---

## File Size Reference

Typical deployment package sizes:

```
Project files (without .venv):     ~50-100 MB
Virtual environment (.venv):       ~500-800 MB
Total after installation:          ~600-900 MB
```

---

## Security Checklist Before Deployment

- [ ] Removed any hardcoded API keys from source files
- [ ] .env file is excluded (or cleaned)
- [ ] No sensitive customer data in databases
- [ ] No debug WAV files with customer audio
- [ ] .gitignore is properly configured
- [ ] Log files don't contain sensitive info

---

## What DEPLOY.bat Does

For your reference, the script:

1. ✅ Checks Python is installed
2. ✅ Creates `.venv` virtual environment
3. ✅ Activates virtual environment
4. ✅ Upgrades pip to latest version
5. ✅ Installs all Python packages from requirements.txt
6. ✅ Runs setup_database.py to create database
7. ✅ Creates .env from .env.example
8. ✅ Opens .env in notepad for you to add keys
9. ✅ Optionally starts the server

**You just run it once and it does everything!**

---

## Need Help?

See DEPLOYMENT_GUIDE.md for:
- Detailed troubleshooting
- Manual installation steps
- Configuration details
- Usage instructions

---

## Ready to Deploy?

1. ✅ Read this checklist
2. ✅ Prepare your API keys
3. ✅ Install Python on new server
4. ✅ Copy project files
5. ✅ Run `DEPLOY.bat`
6. ✅ Configure .env
7. ✅ Start server
8. ✅ Make calls!

Good luck! 🚀
