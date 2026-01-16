@echo off
REM ============================================================================
REM  VONAGE VOICE AGENT - MAIN MENU
REM ============================================================================
REM  Simple menu interface for all deployment and server operations
REM ============================================================================

setlocal enabledelayedexpansion

:MENU
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                    VONAGE VOICE AGENT - MAIN MENU                     ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   What would you like to do?
echo.
echo   ┌─────────────────────────────────────────────────────────────────────┐
echo   │  DEPLOYMENT                                                         │
echo   └─────────────────────────────────────────────────────────────────────┘
echo.
echo   [1] 🚀 DEPLOY - Install everything on this server (first time)
echo       └─ Installs all dependencies, sets up database, configures .env
echo.
echo   [2] 📦 CREATE PACKAGE - Clean package (no database/settings)
echo       └─ For fresh install on new server
echo.
echo   [3] 💾 CREATE PACKAGE WITH DATABASE - Keep all settings
echo       └─ Transfers your super admin config, API keys, users
echo.
echo   [4] ✅ CHECK SYSTEM - Verify this server is ready for deployment
echo       └─ Checks Python, disk space, internet, etc.
echo.
echo   ┌─────────────────────────────────────────────────────────────────────┐
echo   │  SERVER OPERATIONS                                                  │
echo   └─────────────────────────────────────────────────────────────────────┘
echo.
echo   [5] ▶️  START SERVER - Start the Vonage Voice Agent server
echo       └─ Quick daily server start
echo.
echo   [6] 🔧 CONFIGURE - Edit .env file (API keys and settings)
echo       └─ Opens configuration file in notepad
echo.
echo   ┌─────────────────────────────────────────────────────────────────────┐
echo   │  INFORMATION                                                        │
echo   └─────────────────────────────────────────────────────────────────────┘
echo.
echo   [7] 📖 HELP - View documentation and guides
echo       └─ Opens quick start guide
echo.
echo   [8] ℹ️  STATUS - Check current installation status
echo       └─ Shows what's installed and configured
echo.
echo   [9] 🚪 EXIT
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo.

set /p CHOICE="Enter your choice (1-9): "

if "%CHOICE%"=="1" goto DEPLOY
if "%CHOICE%"=="2" goto CREATE_PACKAGE
if "%CHOICE%"=="3" goto CREATE_PACKAGE_WITH_DB
if "%CHOICE%"=="4" goto CHECK_SYSTEM
if "%CHOICE%"=="5" goto START_SERVER
if "%CHOICE%"=="6" goto CONFIGURE
if "%CHOICE%"=="7" goto HELP
if "%CHOICE%"=="8" goto STATUS
if "%CHOICE%"=="9" goto EXIT

echo.
echo ❌ Invalid choice. Please enter a number from 1-9.
timeout /t 2 >nul
goto MENU

REM ============================================================================
REM  OPTION 1: DEPLOY
REM ============================================================================
:DEPLOY
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                          FULL DEPLOYMENT                              ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   This will install everything needed for the Vonage Voice Agent:
echo.
echo   ✓ Create virtual environment
echo   ✓ Install all Python dependencies (~40 packages)
echo   ✓ Setup database
echo   ✓ Configure .env file
echo   ✓ Optionally start the server
echo.
echo   Time required: 5-10 minutes
echo   Internet connection required: Yes
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.

set /p CONFIRM="Do you want to proceed with deployment? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Deployment cancelled.
    timeout /t 2 >nul
    goto MENU
)

echo.
echo Starting deployment...
echo.
call DEPLOY.bat
echo.
echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  OPTION 2: CREATE PACKAGE
REM ============================================================================
:CREATE_PACKAGE
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                        CREATE DEPLOYMENT PACKAGE                      ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   This will create a clean deployment package for transfer to another
echo   server. It will:
echo.
echo   ✓ Copy all necessary files
echo   ✓ Exclude virtual environment, databases, and sensitive data
echo   ✓ Create organized folder structure
echo   ✓ Optionally create ZIP file
echo.
echo   Time required: 1-2 minutes
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.

set /p CONFIRM="Do you want to create deployment package? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Package creation cancelled.
    timeout /t 2 >nul
    goto MENU
)

echo.
echo Creating deployment package...
echo.
call CREATE_PACKAGE.bat
echo.
echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============REATE PACKAGE WITH DATABASE
REM ============================================================================
:CREATE_PACKAGE_WITH_DB
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║              CREATE DEPLOYMENT PACKAGE WITH DATABASE                  ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   This option includes your database in the package, which means:
echo.
echo   ✓ Super admin settings transfer automatically
echo   ✓ API keys already configured (encrypted)
echo   ✓ User accounts preserved
echo   ✓ Phone numbers configured
echo   ✓ All webhooks and settings intact
echo   ✓ No need to reconfigure on new server!
echo.
echo   Perfect for:
echo   • Moving to a new server with same config
echo   • Backup and restore
echo   • Setting up identical servers
echo.
echo   Time required: 1-2 minutes
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.

set /p CONFIRM="Do you want to create package with database? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.5
    echo Package creation cancelled.
    timeout /t 2 >nul
    goto MENU
)

echo.
echo Creating deployment package with database...
echo.
call CREATE_PACKAGE_WITH_DB.bat
echo.
echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  OPTION 4: C================================================================
REM  OPTION 3: CHECK SYSTEM
REM ============================================================================
:CHECK_SYSTEM
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                          SYSTEM CHECK                                 ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   This will verify your system is ready for deployment by checking:
echo.
echo   ✓ Python installation and version
echo   ✓ pip availability
echo   ✓ Disk space
echo   ✓ Internet connection
echo   ✓ Port availability
echo   ✓ Administrator privileges
echo.
echo   Time required: 30 seconds
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.
call CHECK_SYSTEM.bat
echo.
echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  OPTION 4: START SERVER
REM ============================================================================
:START_SERVER
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                          START SERVER                                 ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   This will start the Vonage Voice Agent server.
echo.
echo   The server will run on: http://localhost:5004
echo   Admin panel: http://localhost:5004/super-admin
echo.
echo   Note: You must have completed deployment first (Option 1)
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.

REM Check if deployed
if not exist .venv (
    echo ❌ ERROR: Virtual environment not found!
    echo.
    echo It looks like you haven't deployed yet.
    echo Please run Option 1 ^(DEPLOY^) first.
    echo.
    echo Press any key to return to main menu...
    pause >nul
    goto MENU
)

if not exist6call_logs.db (
    echo ⚠️  WARNING: Database not found!
    echo.
    set /p SETUP_DB="Do you want to set up the database now? (Y/N): "
    if /i "!SETUP_DB!"=="Y" (
        echo.
        echo Setting up database...
        call .venv\Scripts\activate.bat
        python setup_database.py
    ) else (
        echo.
        echo Cannot start server without database.
        echo Press any key to return to main menu...
        pause >nul
        goto MENU
    )
)

if not exist .env (
    echo ⚠️  WARNING: .env file not found!
    echo.
    echo Creating .env from template...
    copy .env.example .env >nul
    echo.
    echo Opening .env for you to add your API keys...
    timeout /t 2 >nul
    notepad .env
    echo.
    echo Press any key once you've saved your API keys...
    pause >nul
)

echo.
echo Starting server...
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║  Press Ctrl+C to stop the server and return to menu                  ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
call START_SERVER.bat
echo.
echo Server stopped.
echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  OPTION 5: CONFIGURE
REM ============================================================================
:CONFIGURE
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                        CONFIGURATION EDITOR                           ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.

if not exist7.env (
    echo .env file not found.
    echo.
    set /p CREATE_ENV="Do you want to create .env from template? (Y/N): "
    if /i "!CREATE_ENV!"=="Y" (
        if exist .env.example (
            copy .env.example .env >nul
            echo.
            echo ✓ .env file created from template
        ) else (
            echo.
            echo ❌ ERROR: .env.example template not found!
            echo Press any key to return to main menu...
            pause >nul
            goto MENU
        )
    ) else (
        echo.
        echo Configuration cancelled.
        timeout /t 2 >nul
        goto MENU
    )
)

echo Opening .env file in Notepad...
echo.
echo IMPORTANT: Make sure to add your API keys:
echo   - OPENAI_API_KEY
echo   - VONAGE_API_KEY
echo   - VONAGE_API_SECRET
echo   - And any other services you plan to use
echo.
echo Press any key to open the file...
pause >nul

notepad .env

echo.
echo Configuration file closed.
echo.
echo If you made changes and the server is running, you'll need to restart it.
echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  OPTION 6: HELP
REM ============================================================================
:HELP
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                          DOCUMENTATION                                ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   Available documentation:
echo.
echo   [1] Quick Start Guide (QUICK_START.md) - Recommended for beginners
echo   [2] Complete Deployment Guide (DEPLOYMENT_GUIDE.md)
echo   [3] Deployment Checklist (DEPLOYMENT_CHECKLIST.md)
echo   [4] Visual Workflow (WORKFLOW.md)
echo   [5] Quick Reference Card (REFERENCE_CARD.txt)
echo   [6] Return to main menu
echo.

set /p DOC_CHOICE="Which document would you like to view? (1-6): "

if "%DOC_CHOICE%"=="1" (
    if exist8QUICK_START.md (
        start QUICK_START.md
    ) else (
        echo File not found: QUICK_START.md
        timeout /t 2 >nul
    )
)
if "%DOC_CHOICE%"=="2" (
    if exist DEPLOYMENT_GUIDE.md (
        start DEPLOYMENT_GUIDE.md
    ) else (
        echo File not found: DEPLOYMENT_GUIDE.md
        timeout /t 2 >nul
    )
)
if "%DOC_CHOICE%"=="3" (
    if exist DEPLOYMENT_CHECKLIST.md (
        start DEPLOYMENT_CHECKLIST.md
    ) else (
        echo File not found: DEPLOYMENT_CHECKLIST.md
        timeout /t 2 >nul
    )
)
if "%DOC_CHOICE%"=="4" (
    if exist WORKFLOW.md (
        start WORKFLOW.md
    ) else (
        echo File not found: WORKFLOW.md
        timeout /t 2 >nul
    )
)
if "%DOC_CHOICE%"=="5" (
    if exist REFERENCE_CARD.txt (
        start REFERENCE_CARD.txt
    ) else (
        echo File not found: REFERENCE_CARD.txt
        timeout /t 2 >nul
    )
)
if "%DOC_CHOICE%"=="6" goto MENU

echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  OPTION 7: STATUS
REM ============================================================================
:STATUS
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                      INSTALLATION STATUS                              ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.

echo Checking installation status...
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.

REM Check Python
echo [1/6] Python Installation:
python --version >nul 2>&1
if errorlevel 1 (
    echo     ❌ Python not found
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo     ✓ Python %%i installed
)
echo.

REM Check Virtual Environment
echo [2/6] Virtual Environment:
if exist .venv (
    echo     ✓ Virtual environment exists
) else (
    echo     ❌ Virtual environment not found - Run DEPLOY to create
)
echo.

REM Check Database
echo [3/6] Database:
if exist call_logs.db (
    echo     ✓ Database file exists ^(call_logs.db^)
) else (
    echo     ❌ Database not found - Run DEPLOY to create
)
echo.

REM Check Configuration
echo [4/6] Configuration:
if exist .env (
    echo     ✓ .env file exists
    findstr /C:"OPENAI_API_KEY=sk-" .env >nul 2>&1
    if errorlevel 1 (
        echo     ⚠️  OpenAI API key may not be configured
    ) else (
        echo     ✓ OpenAI API key appears to be set
    )
    findstr /C:"VONAGE_API_KEY=" .env >nul 2>&1
    if errorlevel 1 (
        echo     ⚠️  Vonage API key may not be configured
    ) else (
        echo     ✓ Vonage API key appears to be set
    )
) else (
    echo     ❌ .env file not found - Run DEPLOY or CONFIGURE
)
echo.

REM Check ngrok
echo [5/6] ngrok ^(for public access^):
if exist C:\ngrok\ngrok.exe (
    echo     ✓ ngrok found at C:\ngrok\ngrok.exe
) else (
    echo     ⚠️  ngrok not found at C:\ngrok\ngrok.exe
    echo        Download from: https://ngrok.com/download
)
echo.

REM Check Port
echo [6/6] Port 5004 Availability:
netstat -ano | findstr ":5004" >nul
if errorlevel 1 (
    echo     ✓ Port 5004 is available
) else (
    echo     ⚠️  Port 5004 is currently in use ^(server may be running^)
)
echo.

echo ───────────────────────────────────────────────────────────────────────
echo.

REM Overall Status
if exist .venv (
    if exist call_logs.db (
        if exist .env (
            echo ✅ OVERALL STATUS: Ready to start server!
            echo.
            echo    You can use Option 4 to start the server.
        ) else (
            echo ⚠️  OVERALL STATUS: Configuration needed
            echo.
            echo    Use Option 5 to configure .env with your API keys.
        )
    ) else (
        echo ⚠️  OVERALL STATUS: Database setup needed
        echo.
        echo    Use Option 1 to complete deployment.
    )
) else (
    echo ❌ OVERALL STATUS: Not deployed
    echo.
    echo    Use Option 1 to deploy the application.
)

echo.
echo Press any key to return to main menu...
pause >nul
goto MENU

REM ============================================================================
REM  EXIT
REM ============================================================================
:EXIT
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║                    Thank you for using                                ║
echo ║              VONAGE VOICE AGENT DEPLOYMENT SYSTEM                     ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   For help, documentation, or to restart the menu, run:
echo   MENU.bat
echo.
echo   To start the server quickly:
echo   START_SERVER.bat
echo.
echo.
timeout /t 3 >nul
exit /b 0
