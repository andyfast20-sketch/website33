@echo off
REM ============================================================================
REM  CREATE DEPLOYMENT PACKAGE
REM ============================================================================
REM  This script creates a clean deployment package ready for transfer
REM  to another server. It excludes virtual environment, cache files,
REM  databases, and sensitive data.
REM ============================================================================

setlocal enabledelayedexpansion
cls

echo.
echo ============================================================================
echo   CREATE DEPLOYMENT PACKAGE FOR NEW SERVER
echo ============================================================================
echo.

set "PACKAGE_NAME=vonage-agent-deployment-%date:~-4%%date:~-10,2%%date:~-7,2%"
set "PACKAGE_DIR=..\%PACKAGE_NAME%"

echo Creating deployment package: %PACKAGE_NAME%
echo.

REM Create package directory
if exist "%PACKAGE_DIR%" (
    echo Removing old package directory...
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"

echo [1/6] Copying Python source files...
REM Copy all .py files
xcopy /Y /Q *.py "%PACKAGE_DIR%\" >nul 2>&1

echo [2/6] Copying configuration files...
REM Copy configuration files
copy /Y requirements.txt "%PACKAGE_DIR%\" >nul 2>&1
copy /Y .env.example "%PACKAGE_DIR%\" >nul 2>&1
copy /Y .gitignore "%PACKAGE_DIR%\" >nul 2>&1

echo [3/6] Copying documentation...
REM Copy documentation
copy /Y README.md "%PACKAGE_DIR%\" >nul 2>&1
copy /Y DEPLOYMENT_GUIDE.md "%PACKAGE_DIR%\" >nul 2>&1
copy /Y DEPLOYMENT_CHECKLIST.md "%PACKAGE_DIR%\" >nul 2>&1
copy /Y *.md "%PACKAGE_DIR%\" >nul 2>&1

REM Copy deployment scripts
copy /Y DEPLOY.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y START_SERVER.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y MENU.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y SUPER_SIMPLE_START.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y CHECK_SYSTEM.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y CREATE_PACKAGE.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y CREATE_PACKAGE_WITH_DB.bat "%PACKAGE_DIR%\" >nul 2>&1

echo [4/6] Copying directories...
REM Copy static files if exists
if exist static (
    mkdir "%PACKAGE_DIR%\static"
    xcopy /E /I /Y /Q static "%PACKAGE_DIR%\static\" >nul 2>&1
)

REM Copy agent directory if exists
if exist agent (
    mkdir "%PACKAGE_DIR%\agent"
    xcopy /E /I /Y /Q agent "%PACKAGE_DIR%\agent\" >nul 2>&1
)

REM Copy vendor directory if exists
if exist vendor (
    mkdir "%PACKAGE_DIR%\vendor"
    xcopy /E /I /Y /Q vendor "%PACKAGE_DIR%\vendor\" >nul 2>&1
)

REM Copy logs directory structure (but not the log files)
if exist logs (
    mkdir "%PACKAGE_DIR%\logs"
    echo. > "%PACKAGE_DIR%\logs\.gitkeep"
)

REM Copy filler_audios if exists
if exist filler_audios (
    mkdir "%PACKAGE_DIR%\filler_audios"
    xcopy /E /I /Y /Q filler_audios "%PACKAGE_DIR%\filler_audios\" >nul 2>&1
)

echo [5/6] Creating README for package...
(
echo # VONAGE VOICE AGENT - DEPLOYMENT PACKAGE
echo.
echo This package contains everything needed to deploy the Vonage Voice Agent
echo to a new Windows server.
echo.
echo ## QUICK START
echo.
echo 1. Extract this package to your new server
echo 2. Make sure Python 3.10+ is installed
echo 3. Open Command Prompt in this folder
echo 4. Run: DEPLOY.bat
echo 5. Follow the on-screen instructions
echo.
echo ## WHAT'S INCLUDED
echo.
echo - All Python source code
echo - Requirements file ^(dependencies^)
echo - Configuration templates
echo - Deployment automation scripts
echo - Complete documentation
echo.
echo ## WHAT YOU NEED TO PROVIDE
echo.
echo - Python 3.10 or higher installed on target server
echo - Your API keys:
echo   * OpenAI API Key
echo   * Vonage API Key and Secret
echo   * Any optional service keys you use
echo - ngrok for public access ^(download from ngrok.com^)
echo.
echo ## DOCUMENTATION
echo.
echo - DEPLOYMENT_GUIDE.md - Complete step-by-step guide
echo - DEPLOYMENT_CHECKLIST.md - Pre-deployment checklist
echo - README.md - General project information
echo.
echo ## DEPLOYMENT TIME
echo.
echo Total: 10-20 minutes
echo - File extraction: 1 min
echo - Running DEPLOY.bat: 5-10 min
echo - Configuration: 2-3 min
echo - First start: 1 min
echo.
echo ## SUPPORT
echo.
echo If you encounter issues, see DEPLOYMENT_GUIDE.md troubleshooting section.
echo.
echo Generated: %date% %time%
) > "%PACKAGE_DIR%\START_HERE.txt"

echo [6/6] Creating package info file...
(
echo Deployment Package Information
echo ===============================
echo.
echo Package Name: %PACKAGE_NAME%
echo Created: %date% %time%
echo Source: %CD%
echo.
echo Contents:
echo - Python source files: %CD%\*.py
echo - Requirements: requirements.txt
echo - Configuration template: .env.example
echo - Documentation: *.md files
echo - Deployment scripts: DEPLOY.bat, START_SERVER.bat
echo.
echo EXCLUDED ^(will be regenerated on target server^):
echo - Virtual environment ^(.venv^)
echo - Database files ^(*.db^)
echo - Cache files ^(__pycache__^)
echo - Log files ^(*.log^)
echo - .env file ^(contains secrets^)
echo - Debug audio files ^(*.wav^)
echo.
echo NEXT STEPS:
echo 1. Compress this folder to a ZIP file
echo 2. Transfer to new server
echo 3. Extract and run DEPLOY.bat
echo.
) > "%PACKAGE_DIR%\PACKAGE_INFO.txt"

echo.
echo ============================================================================
echo   PACKAGE CREATED SUCCESSFULLY!
echo ============================================================================
echo.
echo   Location: %PACKAGE_DIR%
echo.
echo   NEXT STEPS:
echo.
echo   1. Review the package folder to ensure everything is included
echo   2. Create a ZIP file of the folder:
echo      Right-click folder ^> Send to ^> Compressed ^(zipped^) folder
echo.
echo   3. Transfer the ZIP file to your new server using:
echo      - USB drive
echo      - Network share
echo      - Cloud storage
echo      - Email ^(if small enough^)
echo.
echo   4. On new server:
echo      - Extract the ZIP file
echo      - Open START_HERE.txt for instructions
echo      - Run DEPLOY.bat
echo.
echo ============================================================================
echo.

set /p OPEN="Do you want to open the package folder now? (Y/N): "
if /i "%OPEN%"=="Y" (
    explorer "%PACKAGE_DIR%"
)

set /p ZIP="Do you want to create a ZIP file now? (Y/N): "
if /i "%ZIP%"=="Y" (
    echo.
    echo Creating ZIP file...
    echo This will use PowerShell to compress the folder...
    powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%' -DestinationPath '%PACKAGE_DIR%.zip' -Force"
    if exist "%PACKAGE_DIR%.zip" (
        echo.
        echo ZIP file created: %PACKAGE_DIR%.zip
        echo.
        set /p SHOWZIP="Open folder with ZIP file? (Y/N): "
        if /i "!SHOWZIP!"=="Y" (
            explorer /select,"%PACKAGE_DIR%.zip"
        )
    ) else (
        echo.
        echo Failed to create ZIP automatically.
        echo Please right-click the folder and create ZIP manually.
    )
)

echo.
echo Done!
pause
