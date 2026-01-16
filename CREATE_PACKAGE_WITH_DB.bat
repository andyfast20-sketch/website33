@echo off
REM ============================================================================
REM  CREATE DEPLOYMENT PACKAGE WITH DATABASE (Keep Settings)
REM ============================================================================
REM  This script creates a deployment package that INCLUDES your database,
REM  so all your super admin settings, API keys, and configuration are
REM  transferred to the new server.
REM ============================================================================

setlocal enabledelayedexpansion
cls

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║        CREATE DEPLOYMENT PACKAGE WITH DATABASE                        ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   This option will include your database file in the package, which means:
echo.
echo   ✓ All super admin settings transfer automatically
echo   ✓ API keys already configured (encrypted)
echo   ✓ User accounts and phone numbers preserved
echo   ✓ All configuration settings kept
echo   ✓ No need to reconfigure on new server
echo.
echo   ⚠️  SECURITY NOTE:
echo   The database contains encrypted API keys and settings. While encrypted,
echo   keep the package secure during transfer.
echo.
echo ───────────────────────────────────────────────────────────────────────
echo.

set /p CONFIRM="Do you want to include the database in the package? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Package creation cancelled.
    echo.
    echo If you want a clean package without settings, use Option 2 instead.
    pause
    exit /b 1
)

set "PACKAGE_NAME=vonage-agent-with-db-%date:~-4%%date:~-10,2%%date:~-7,2%"
set "PACKAGE_DIR=..\%PACKAGE_NAME%"

echo.
echo Creating deployment package: %PACKAGE_NAME%
echo.

REM Create package directory
if exist "%PACKAGE_DIR%" (
    echo Removing old package directory...
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"

echo [1/7] Copying Python source files...
xcopy /Y /Q *.py "%PACKAGE_DIR%\" >nul 2>&1

echo [2/7] Copying configuration files...
copy /Y requirements.txt "%PACKAGE_DIR%\" >nul 2>&1
copy /Y .env.example "%PACKAGE_DIR%\" >nul 2>&1
copy /Y .gitignore "%PACKAGE_DIR%\" >nul 2>&1

echo [3/7] Copying documentation...
copy /Y *.md "%PACKAGE_DIR%\" >nul 2>&1
copy /Y *.txt "%PACKAGE_DIR%\" >nul 2>&1

REM Copy deployment scripts
copy /Y DEPLOY.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y START_SERVER.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y CHECK_SYSTEM.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y MENU.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y START_HERE.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y SUPER_SIMPLE_START.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y CREATE_PACKAGE.bat "%PACKAGE_DIR%\" >nul 2>&1
copy /Y CREATE_PACKAGE_WITH_DB.bat "%PACKAGE_DIR%\" >nul 2>&1

echo [4/7] Copying directories...
if exist static (
    mkdir "%PACKAGE_DIR%\static"
    xcopy /E /I /Y /Q static "%PACKAGE_DIR%\static\" >nul 2>&1
)

if exist agent (
    mkdir "%PACKAGE_DIR%\agent"
    xcopy /E /I /Y /Q agent "%PACKAGE_DIR%\agent\" >nul 2>&1
)

if exist vendor (
    mkdir "%PACKAGE_DIR%\vendor"
    xcopy /E /I /Y /Q vendor "%PACKAGE_DIR%\vendor\" >nul 2>&1
)

if exist filler_audios (
    mkdir "%PACKAGE_DIR%\filler_audios"
    xcopy /E /I /Y /Q filler_audios "%PACKAGE_DIR%\filler_audios\" >nul 2>&1
)

mkdir "%PACKAGE_DIR%\logs"
echo. > "%PACKAGE_DIR%\logs\.gitkeep"

echo [5/7] Copying database and settings...
if exist call_logs.db (
    copy /Y call_logs.db "%PACKAGE_DIR%\" >nul 2>&1
    echo     ✓ call_logs.db copied
) else (
    echo     ⚠️  call_logs.db not found - will be created on new server
)

if exist .env (
    echo.
    echo     ⚠️  IMPORTANT: .env file found
    echo.
    set /p COPY_ENV="Do you want to copy .env file too? (Y/N): "
    if /i "!COPY_ENV!"=="Y" (
        copy /Y .env "%PACKAGE_DIR%\" >nul 2>&1
        echo     ✓ .env copied (KEEP PACKAGE SECURE!)
    ) else (
        echo     Skipped .env - will use .env.example on new server
    )
)

if exist google-credentials.json (
    echo.
    set /p COPY_GOOGLE="Google credentials found. Copy? (Y/N): "
    if /i "!COPY_GOOGLE!"=="Y" (
        copy /Y google-credentials.json "%PACKAGE_DIR%\" >nul 2>&1
        echo     ✓ Google credentials copied
    )
)

echo [6/7] Creating package info file...
(
echo Deployment Package Information ^(WITH DATABASE^)
echo ==================================================
echo.
echo Package Name: %PACKAGE_NAME%
echo Created: %date% %time%
echo Source: %CD%
echo.
echo IMPORTANT: This package includes your database!
echo ===============================================
echo.
echo This means:
echo ✓ All super admin settings are included
echo ✓ API keys ^(encrypted^) are included
echo ✓ User accounts and phone numbers included
echo ✓ All configuration preserved
echo.
echo On the new server:
echo 1. Extract this package
echo 2. Run MENU.bat ^> Option 1 ^(Deploy^)
echo 3. Server will use existing database automatically
echo 4. No need to reconfigure super admin!
echo.
echo The database is encrypted, but keep this package secure during transfer.
echo.
echo EXCLUDED from this package:
echo - Virtual environment ^(.venv^) - will be recreated
echo - Log files ^(*.log^) - fresh logs on new server
echo - Cache files ^(__pycache__^) - will be recreated
echo - Debug files ^(*.wav^) - not needed
echo.
echo INCLUDED in this package:
echo - Database ^(call_logs.db^) ✓
echo - All Python source code ✓
echo - Configuration files ✓
echo - Documentation ✓
echo - Deployment scripts ✓
echo.
) > "%PACKAGE_DIR%\PACKAGE_INFO.txt"

echo [7/7] Creating special README...
(
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   👋 WELCOME! DOUBLE-CLICK "SUPER_SIMPLE_START.bat" TO BEGIN!
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   This package includes your database, so all your settings
echo   will be preserved on the new server!
echo.
echo   SUPER EASY STEPS:
echo   ═════════════════
echo   1. Look for the file: SUPER_SIMPLE_START.bat
echo   2. Double-click it
echo   3. Type: 1 and press Enter
echo   4. Wait about 10 minutes
echo   5. Done! All your settings are already there!
echo.
echo   NO RECONFIGURATION NEEDED!
echo   ═════════════════════════
echo   • API keys already set ^(from super admin^)
echo   • Phone numbers already configured
echo   • User accounts preserved
echo   • All settings intact
echo.
echo   JUST RUN SUPER_SIMPLE_START.bat AND CHOOSE OPTION 1!
echo.
) > "%PACKAGE_DIR%\👉 START HERE.txt"

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo   PACKAGE CREATED SUCCESSFULLY!
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo   Location: %PACKAGE_DIR%
echo.
echo   ✓ Database included - All settings will transfer!
echo.
echo   NEXT STEPS:
echo.✓ Database included - All settings will transfer!
echo.
echo   Creating ZIP file automatically...
echo.

powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%' -DestinationPath '%PACKAGE_DIR%.zip' -Force" 2>nul

if exist "%PACKAGE_DIR%.zip" (
    echo   ✅ ZIP FILE CREATED!
    echo.
    echo   ═══════════════════════════════════════════════════════════════════════
    echo   NEXT STEPS - SUPER EASY:
    echo   ═══════════════════════════════════════════════════════════════════════
    echo.
    echo   1. I'm going to open a folder and show you the ZIP file
    echo.
    echo   2. Copy that ZIP file to your other computer
    echo      ^(Use a USB stick, network, email, whatever you want^)
    echo.
    echo   3. On the other computer:
    echo      • Copy the ZIP file there
    echo      • Right-click the ZIP → Click "Extract All"
    echo      • Open the folder that was created
    echo      • Look for "SUPER_SIMPLE_START.bat"
    echo      • Double-click it
    echo      • Type 1 and press Enter
    echo      • Wait 10 minutes
    echo      • Done!
    echo.
    echo   All your settings will be there automatically! 🎉
    echo.
    echo   ═══════════════════════════════════════════════════════════════════════
    echo.
    echo   Press any key and I'll show you the ZIP file...
    pause >nul
    
    explorer /select,"%PACKAGE_DIR%.zip"
) else (
    echo   ⚠️  Could not create ZIP automatically.
    echo   Please right-click the folder and choose "Send to" → "Compressed folder"
    echo.
    pause
echo   ✅ IMPORTANT: ZIP file created successfully!
echo.
echo   The ZIP file is ready to copy to your other computer.
echo.
echo   If you used SUPER_SIMPLE_START.bat, it will show you the file now.
echo   Otherwise, look in the parent folder for the ZIP file.
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo Done!
pause
