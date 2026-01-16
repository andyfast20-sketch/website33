@echo off
REM ============================================================================
REM  QUICK START - For servers where DEPLOY.bat was already run
REM ============================================================================
REM  Use this to start the server after initial deployment
REM ============================================================================

cls
echo.
echo ============================================================================
echo   VONAGE VOICE AGENT - QUICK START
echo ============================================================================
echo.

REM Check if virtual environment exists
if not exist .venv (
    echo ERROR: Virtual environment not found!
    echo.
    echo This script is for starting the server after initial deployment.
    echo Please run DEPLOY.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if database exists
if not exist call_logs.db (
    echo WARNING: Database not found!
    echo Creating database now...
    python setup_database.py
    if errorlevel 1 (
        echo ERROR: Database setup failed!
        pause
        exit /b 1
    )
)

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env and add your API keys!
    echo Opening .env now...
    timeout /t 2 >nul
    notepad .env
    echo.
    echo Press any key once you've saved your API keys...
    pause >nul
)

REM Start server
echo.
echo Starting Vonage Voice Agent...
echo.
python start_server_clean.py

REM If server stops, keep window open
echo.
echo Server stopped.
pause
