# 🚀 Complete Deployment Guide - Vonage Voice Agent

This guide will help you deploy the Vonage Voice Agent to a new Windows server with **ONE SIMPLE COMMAND**.

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Windows Server or Windows 10/11** (64-bit)
2. **Python 3.10 or higher** - [Download here](https://www.python.org/downloads/)
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation!
3. **Your API Keys** ready:
   - OpenAI API Key
   - Vonage API Key & Secret
   - (Optional) ElevenLabs, Google TTS, Deepgram, etc.
4. **ngrok** (for public access) - [Download here](https://ngrok.com/download)

---

## 🎯 One-Click Deployment

### Step 1: Copy Files to New Server

Transfer the entire project folder to your new server. You can use:
- USB drive
- Network share
- Git clone
- Cloud storage (OneDrive, Dropbox, etc.)

### Step 2: Run the Menu System (Recommended)

Open Command Prompt in the project folder and run:

```batch
MENU.bat
```

Then select **Option 1 (Deploy)** from the menu.

**OR** run the deployment script directly:

```batch
DEPLOY.bat
```

That's it! The script will automatically:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all dependencies (~40 packages)
- ✅ Setup the database
- ✅ Create configuration file
- ✅ Start the server (optional)

**Total Time**: ~5-10 minutes (depending on internet speed)

---

## 🔧 Manual Deployment (If Needed)

If you prefer to understand each step or the automatic script fails:

### 1. Install Python
```batch
# Download and install Python 3.10+ from python.org
# Make sure to check "Add Python to PATH"!
python --version
```

### 2. Create Virtual Environment
```batch
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```batch
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup Database
```batch
python setup_database.py
```

### 5. Configure Environment
```batch
# Copy the example file
copy .env.example .env

# Edit .env and add your API keys
notepad .env
```

### 6. Start Server
```batch
python start_server_clean.py
```

---

## 🔑 Required API Keys & Configuration

Edit the `.env` file with your credentials:

### Essential (Required):
```ini
OPENAI_API_KEY=sk-...
VONAGE_API_KEY=...
VONAGE_API_SECRET=...
```

### Optional Services:
```ini
# Text-to-Speech Providers
ELEVENLABS_API_KEY=...
GOOGLE_CREDENTIALS_PATH=google-credentials.json

# Speech-to-Text
DEEPGRAM_API_KEY=...
ASSEMBLYAI_API_KEY=...

# Alternative LLM Providers
DEEPSEEK_API_KEY=...

# Admin Access
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=your_secure_password_here
```

---

## 🌐 Setting Up Public Access (ngrok)

Your server needs to be accessible from the internet for Vonage to send webhooks.

### Option 1: Automatic (Built-in)
The server will attempt to start ngrok automatically if it's installed at:
- `C:\ngrok\ngrok.exe`

### Option 2: Manual
1. Download ngrok: https://ngrok.com/download
2. Extract to `C:\ngrok\`
3. Run in separate terminal:
```batch
C:\ngrok\ngrok.exe http 5004
```

### Option 3: Cloudflare Tunnel (Alternative)
```batch
cloudflared tunnel --url http://localhost:5004
```

---

## 📱 Vonage Webhook Configuration

Once your server is running with a public URL:

1. Log into [Vonage Dashboard](https://dashboard.nexmo.com/)
2. Go to your application settings
3. Set these webhook URLs (replace `YOUR_NGROK_URL`):

```
Answer URL: https://YOUR_NGROK_URL/webhooks/answer
Event URL: https://YOUR_NGROK_URL/webhooks/event
```

---

## ✅ Verification Checklist

After deployment, verify everything works:

- [ ] Python is installed and in PATH
- [ ] Virtual environment is created (`.venv` folder exists)
- [ ] All dependencies installed (no errors)
- [ ] Database created (`call_logs.db` exists)
- [ ] `.env` file configured with API keys
- [ ] Server starts without errors
- [ ] Can access http://localhost:5004
- [ ] ngrok is running and provides public URL
- [ ] Vonage webhooks are configured
- [ ] Can access super-admin panel

---

## 🎮 Using the System

### Access Points

1. **Web Interface**: http://localhost:5004
2. **Super Admin Panel**: http://localhost:5004/super-admin
3. **API Documentation**: http://localhost:5004/docs

### Starting the Server

**Recommended Method** (kills any existing instances):
```batch
.venv\Scripts\activate
python start_server_clean.py
```

**Alternative Methods**:
```batch
# Direct start
python vonage_agent.py

# Using the deployment script
DEPLOY.bat
```

### Stopping the Server

Press `Ctrl+C` in the terminal, or run:
```batch
# Kill any process on port 5004
powershell -Command "Get-NetTCPConnection -LocalPort 5004 | Stop-Process -Force"
```

---

## 🔧 Troubleshooting

### "Python is not recognized"
- Install Python from python.org
- Make sure "Add Python to PATH" was checked
- Restart Command Prompt after installation

### "pip install" fails
- Make sure you're in the virtual environment (you should see `(.venv)` in prompt)
- Try running as administrator
- Check internet connection

### Database errors
- Delete `call_logs.db` and run `python setup_database.py` again

### Port 5004 already in use
- Run: `python start_server_clean.py` (automatically kills existing process)
- Or manually kill: `taskkill /F /IM python.exe`

### ngrok connection issues
- Make sure ngrok is downloaded
- Check if antivirus is blocking it
- Try running ngrok manually first

### Missing API responses
- Check `.env` file has all required keys
- Verify API keys are valid
- Check server logs for errors

---

## 📁 What Gets Installed

The deployment script installs:

### Python Packages (~40):
- **Web Framework**: FastAPI, Uvicorn
- **AI/LLM**: OpenAI, Google Generative AI
- **Speech**: ElevenLabs, Google TTS, Whisper, Deepgram, AssemblyAI
- **Telephony**: Vonage
- **Audio**: PyAudio, SoundDevice, Pydub, NumPy
- **Database**: SQLAlchemy (SQLite)
- **Utilities**: python-dotenv, cryptography, requests, websockets

### Files Created:
- `.venv/` - Virtual environment
- `call_logs.db` - Main database
- `.env` - Your configuration (DO NOT share!)

---

## 🔐 Security Notes

⚠️ **IMPORTANT SECURITY REMINDERS**:

1. **Never commit `.env` to version control**
2. **Keep API keys secure**
3. **Change default admin password immediately**
4. **Use strong passwords**
5. **Keep your system updated**

---

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**:
   - Look for error messages in the terminal
   - Check log files in the project directory

2. **Common Solutions**:
   - Restart the server
   - Delete `.venv` and run `DEPLOY.bat` again
   - Make sure all API keys are correct
   - Check Windows Firewall settings

3. **Advanced Debugging**:
   ```batch
   # Run with verbose logging
   python vonage_agent.py
   ```

---

## 📊 System Requirements

**Minimum**:
- Windows 10/11 or Windows Server 2016+
- 4 GB RAM
- 2 GB disk space
- Internet connection

**Recommended**:
- 8 GB RAM
- 10 GB disk space
- SSD storage
- Stable internet (10+ Mbps)

---

## 🎉 Success!

If you see this message, you're ready to go:

```
========================================
🚀 Server Started Successfully!
========================================
Web Interface: http://localhost:5004
ngrok http 5004
========================================
```

You can now make and receive phone calls through your AI agent!

---

## 📝 License & Support

This is a production-ready voice AI system. For support and updates, maintain regular backups of:
- `call_logs.db` (your data)
- `.env` (your configuration)
- Any custom modifications you make

Happy deploying! 🚀
