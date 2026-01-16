@echo off
REM ============================================================================
REM  PRE-DEPLOYMENT CHECKER
REM ============================================================================
REM  Run this on your NEW server BEFORE running DEPLOY.bat
REM  It checks if your server is ready for deployment
REM ============================================================================

setlocal enabledelayedexpansion
cls

echo.
echo ============================================================================
echo   PRE-DEPLOYMENT SYSTEM CHECK
echo ============================================================================
echo.
echo This script checks if your server is ready for Vonage Voice Agent
echo deployment. It will verify all prerequisites are met.
echo.
echo ============================================================================
echo.

set "CHECKS_PASSED=0"
set "CHECKS_FAILED=0"
set "CHECKS_WARNING=0"

REM Check 1: Windows Version
echo [CHECK 1/8] Windows Version...
ver | findstr /i "10\. 11\. Server" >nul
if errorlevel 1 (
    echo    ❌ FAILED: Unsupported Windows version
    echo       Recommended: Windows 10, 11, or Server 2016+
    set /a CHECKS_WARNING+=1
) else (
    echo    ✅ PASSED: Windows version compatible
    set /a CHECKS_PASSED+=1
)
echo.

REM Check 2: Python Installation
echo [CHECK 2/8] Python Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ FAILED: Python not found or not in PATH
    echo       Action: Install Python 3.10+ from python.org
    echo       Make sure to check "Add Python to PATH"!
    set /a CHECKS_FAILED+=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo    ✅ PASSED: Python !PYTHON_VERSION! found
    set /a CHECKS_PASSED+=1
)
echo.

REM Check 3: Python Version
echo [CHECK 3/8] Python Version...
python --version 2>&1 | findstr /r "3\.1[0-9]\. 3\.[2-9][0-9]\." >nul
if errorlevel 1 (
    echo    ⚠️  WARNING: Python version may be too old
    echo       Recommended: Python 3.10 or higher
    set /a CHECKS_WARNING+=1
) else (
    echo    ✅ PASSED: Python version is compatible
    set /a CHECKS_PASSED+=1
)
echo.

REM Check 4: pip availability
echo [CHECK 4/8] pip ^(Package Manager^)...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ FAILED: pip not available
    echo       Action: Reinstall Python with pip included
    set /a CHECKS_FAILED+=1
) else (
    echo    ✅ PASSED: pip is available
    set /a CHECKS_PASSED+=1
)
echo.

REM Check 5: Disk Space
echo [CHECK 5/8] Disk Space...
for /f "tokens=3" %%a in ('dir /-c ^| findstr /C:"bytes free"') do set FREE_SPACE=%%a
if defined FREE_SPACE (
    REM Remove commas from number
    set "FREE_SPACE=!FREE_SPACE:,=!"
    REM Check if greater than 2GB (2147483648 bytes)
    if !FREE_SPACE! GTR 2147483648 (
        echo    ✅ PASSED: Sufficient disk space
        set /a CHECKS_PASSED+=1
    ) else (
        echo    ⚠️  WARNING: Low disk space
        echo       Recommended: At least 2GB free
        set /a CHECKS_WARNING+=1
    )
) else (
    echo    ⚠️  WARNING: Could not determine disk space
    set /a CHECKS_WARNING+=1
)
echo.

REM Check 6: Internet Connection
echo [CHECK 6/8] Internet Connection...
ping -n 1 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    echo    ❌ FAILED: No internet connection detected
    echo       Action: Connect to the internet before deployment
    set /a CHECKS_FAILED+=1
) else (
    echo    ✅ PASSED: Internet connection active
    set /a CHECKS_PASSED+=1
)
echo.

REM Check 7: Port 5004 availability
echo [CHECK 7/8] Port 5004 Availability...
netstat -ano | findstr ":5004" >nul
if errorlevel 1 (
    echo    ✅ PASSED: Port 5004 is available
    set /a CHECKS_PASSED+=1
) else (
    echo    ⚠️  WARNING: Port 5004 is in use
    echo       Note: DEPLOY.bat will handle this automatically
    set /a CHECKS_WARNING+=1
)
echo.

REM Check 8: Administrator privileges (optional but recommended)
echo [CHECK 8/8] Administrator Privileges...
net session >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  WARNING: Not running as Administrator
    echo       Note: May be needed for some installations
    echo       Tip: Right-click Command Prompt ^> Run as administrator
    set /a CHECKS_WARNING+=1
) else (
    echo    ✅ PASSED: Running with Administrator privileges
    set /a CHECKS_PASSED+=1
)
echo.

REM Summary
echo ============================================================================
echo   CHECK SUMMARY
echo ============================================================================
echo.
echo   ✅ Passed:   !CHECKS_PASSED!
if !CHECKS_WARNING! GTR 0 (
    echo   ⚠️  Warnings: !CHECKS_WARNING!
)
if !CHECKS_FAILED! GTR 0 (
    echo   ❌ Failed:   !CHECKS_FAILED!
)
echo.
echo ============================================================================
echo.

if !CHECKS_FAILED! GTR 0 (
    echo ❌ CRITICAL ISSUES FOUND
    echo.
    echo You must fix the failed checks before running DEPLOY.bat
    echo.
    echo Common fixes:
    echo   • Install Python 3.10+ from https://python.org/downloads/
    echo   • Make sure "Add Python to PATH" is checked during install
    echo   • Restart Command Prompt after installing Python
    echo   • Connect to the internet
    echo.
    echo ============================================================================
) else if !CHECKS_WARNING! GTR 0 (
    echo ⚠️  WARNINGS DETECTED
    echo.
    echo You can proceed with deployment, but be aware of the warnings above.
    echo Most warnings can be safely ignored if you understand the implications.
    echo.
    echo ============================================================================
    echo.
    set /p PROCEED="Do you want to run DEPLOY.bat now? (Y/N): "
    if /i "!PROCEED!"=="Y" (
        echo.
        echo Starting deployment...
        call DEPLOY.bat
        exit /b 0
    )
) else (
    echo ✅ ALL CHECKS PASSED!
    echo.
    echo Your server is ready for deployment!
    echo.
    echo ============================================================================
    echo.
    set /p PROCEED="Do you want to run DEPLOY.bat now? (Y/N): "
    if /i "!PROCEED!"=="Y" (
        echo.
        echo Starting deployment...
        call DEPLOY.bat
        exit /b 0
    )
)

echo.
echo To deploy manually, run:
echo    DEPLOY.bat
echo.
pause
