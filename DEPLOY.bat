@echo off
REM ============================================================================
REM  ONE-CLICK DEPLOYMENT SCRIPT FOR VONAGE VOICE AGENT
REM ============================================================================
REM  This script will:
REM  1. Check Python installation
REM  2. Create virtual environment
REM  3. Install all dependencies
REM  4. Setup database
REM  5. Configure environment
REM  6. Start the server
REM ============================================================================

setlocal enabledelayedexpansion
cls

echo.
echo ============================================================================
echo   VONAGE VOICE AGENT - AUTOMATIC DEPLOYMENT
echo ============================================================================
echo.

REM Step 1: Check Python
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    Found Python %PYTHON_VERSION%
echo.

REM Step 2: Create virtual environment
echo [2/7] Creating virtual environment...
if exist .venv (
    echo    Virtual environment already exists, skipping...
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo    Virtual environment created successfully!
)
echo.

REM Step 3: Activate virtual environment and upgrade pip
echo [3/7] Activating virtual environment and upgrading pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo    Pip upgraded successfully!
echo.

REM Step 4: Install dependencies
echo [4/7] Installing Python dependencies (this may take several minutes)...
echo    Please be patient, installing 40+ packages...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo Trying again with verbose output...
    pip install -r requirements.txt
    pause
    exit /b 1
)
echo    All dependencies installed successfully!
echo.

REM Step 5: Setup database
echo [5/7] Setting up database...
if exist call_logs.db (
    echo    Database already exists, skipping setup...
) else (
    python setup_database.py
    if errorlevel 1 (
        echo ERROR: Database setup failed!
        pause
        exit /b 1
    )
    echo    Database created successfully!
)
echo.

REM Step 6: Check environment file
echo [6/7] Checking environment configuration...
if exist .env (
    echo    .env file found!
    echo.
    echo    IMPORTANT: Make sure your .env file contains all required API keys:
    echo    - OPENAI_API_KEY
    echo    - VONAGE_API_KEY
    echo    - VONAGE_API_SECRET
    echo    - And any other services you plan to use
    echo.
) else (
    echo    Creating .env file from template...
    copy .env.example .env >nul
    echo.
    echo    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo    IMPORTANT: You MUST edit the .env file and add your API keys!
    echo    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo.
    echo    Opening .env file in notepad for you to edit...
    timeout /t 3 >nul
    notepad .env
    echo.
    echo    Have you finished editing the .env file with your API keys?
    echo    Press any key once you've saved your changes...
    pause >nul
)
echo.

REM Step 7: Installation complete
echo [7/7] Installation Complete!
echo.
echo ============================================================================
echo   DEPLOYMENT SUCCESSFUL!
echo ============================================================================
echo.
echo   Your Vonage Voice Agent is ready to run!
echo.
echo   To start the server, you have two options:
echo.
echo   Option 1 - Run with this script:
echo      Just press any key to start the server now
echo.
echo   Option 2 - Manual start (recommended for first time):
echo      .venv\Scripts\activate
echo      python start_server_clean.py
echo.
echo   The server will run on: http://localhost:5004
echo.
echo   NEXT STEPS:
echo   1. Make sure ngrok is installed (for public access)
echo   2. Configure your Vonage webhooks to point to your ngrok URL
echo   3. Access the admin interface at: http://localhost:5004/super-admin
echo.
echo ============================================================================
echo.

set /p START="Do you want to start the server now? (Y/N): "
if /i "%START%"=="Y" (
    echo.
    echo Starting server...
    echo.
    python start_server_clean.py
) else (
    echo.
    echo   To start the server later, run:
    echo   .venv\Scripts\activate
    echo   python start_server_clean.py
    echo.
)

pause
