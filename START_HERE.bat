@echo off
echo.
echo ═══════════════════════════════════════════════════════════════════
echo   VONAGE VOICE AGENT - DEPLOYMENT PACKAGE
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   Welcome! This package contains everything you need to deploy
echo   the Vonage Voice Agent to a new Windows server.
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   🎯 EASIEST WAY - USE THE MENU!
echo.
echo   Just run: MENU.bat
echo   Then press 1 to deploy, or choose any other option!
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   OR QUICK START (Manual):
echo.
echo   1. Make sure Python 3.10+ is installed
echo      Download: https://python.org/downloads/
echo      IMPORTANT: Check "Add Python to PATH" during installation!
echo.
echo   2. Run: MENU.bat (recommended)
echo      OR run: DEPLOY.bat (direct deployment)
echo.
echo   3. Follow the on-screen instructions
echo.
echo   That's it! Total time: 10-20 minutes
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   WHAT YOU NEED:
echo.
echo   ✓ Python 3.10 or higher
echo   ✓ Internet connection
echo   ✓ 2GB+ free disk space
echo   ✓ Your API keys:
echo      - OpenAI API Key
echo      - Vonage API Key and Secret
echo      - (Optional) Other service keys
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   DOCUMENTATION:
echo.
echo   • QUICK_START.md           - Quick reference guide
echo   • DEPLOYMENT_GUIDE.md      - Complete detailed guide
echo   • DEPLOYMENT_CHECKLIST.md  - Pre-deployment checklist
echo   • WORKFLOW.md              - Visual workflow diagram
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
echo   NEXT STEPS:
echo.
set /p NEXT="What would you like to do? (1=Open Menu, 2=Deploy Now, 3=Read Docs, 4=Exit): "

if "%NEXT%"=="1" (
    echo.
    echo Opening main menu...
    echo.
    call MENU.bat
    goto :END
)

if "%NEXT%"=="2" (
    echo.
    echo Starting deployment...
    echo.
    call DEPLOY.bat
    goto :END
)

if "%NEXT%"=="3" (
    echo.
    echo Opening MENU_GUIDE.md...
    if exist MENU_GUIDE.md (
        start MENU_GUIDE.md
    ) else if exist QUICK_START.md (
        start QUICK_START.md
    ) else (
        echo Documentation files not found.
    )
    goto :END
)

if "%NEXT%"=="4" (
    goto :END
)

echo.
echo Invalid option. Please run this script again.
echo.

:END
pause
