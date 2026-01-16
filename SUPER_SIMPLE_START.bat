@echo off
REM ============================================================================
REM  👋 SUPER SIMPLE START - CLICK ME!
REM ============================================================================
REM  This is the easiest way to use the Vonage Voice Agent
REM  Just answer the questions - no technical knowledge needed!
REM ============================================================================

color 0A
mode con: cols=80 lines=35
cls

:START
cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                                                                    ║
echo    ║              👋 WELCOME TO VONAGE VOICE AGENT! 👋                  ║
echo    ║                                                                    ║
echo    ║                    Super Simple Setup                              ║
echo    ║                                                                    ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo    📝 IMPORTANT: If you downloaded a ZIP file from GitHub:
echo       1. Right-click the ZIP file
echo       2. Click "Extract All"
echo       3. Open the extracted folder
echo       4. Then run this file
echo.
echo    Let me help you get started! I'll guide you through everything.
echo.
echo    First, let me ask you a simple question:
echo.
echo    ┌────────────────────────────────────────────────────────────────────┐
echo    │                                                                    │
echo    │  What do you want to do?                                           │
echo    │                                                                    │
echo    │  1. 🚀 Set up on THIS computer (first time)                        │
echo    │                                                                    │
echo    │  2. 📦 Move to ANOTHER computer (keep my settings)                 │
echo    │                                                                    │
echo    │  3. ▶️  Start the voice agent (already set up)                     │
echo    │                                                                    │
echo    │  4. 🆘 Help - I'm not sure what to do                              │
echo    │                                                                    │
echo    └────────────────────────────────────────────────────────────────────┘
echo.
echo.
set /p SIMPLE_CHOICE="    Type 1, 2, 3, or 4 and press Enter: "

if "%SIMPLE_CHOICE%"=="1" goto FIRST_TIME_SETUP
if "%SIMPLE_CHOICE%"=="2" goto MOVE_TO_ANOTHER
if "%SIMPLE_CHOICE%"=="3" goto START_IT
if "%SIMPLE_CHOICE%"=="4" goto HELP_ME

echo.
echo    Oops! Please type just the number (1, 2, 3, or 4)
timeout /t 3 >nul
goto START

REM ============================================================================
REM  FIRST TIME SETUP
REM ============================================================================
:FIRST_TIME_SETUP
cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║              🚀 FIRST TIME SETUP - LET'S DO THIS!                  ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo    Great! I'm going to install everything you need.
echo.
echo    This will take about 10 minutes. Here's what I'll do:
echo.
echo    ✅ Install all the required programs
echo    ✅ Set up the database
echo    ✅ Get everything ready
echo.
echo    You just need to wait - I'll do all the hard work! 😊
echo.
echo    Ready?
echo.
echo.
set /p GO="    Press Y to start, or N to go back: "
if /i not "%GO%"=="Y" goto START

cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                    ⏳ INSTALLING... PLEASE WAIT                     ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo    This might take a few minutes. Don't close this window!
echo.
echo    You can get a coffee or watch a YouTube video while you wait... ☕
echo.

call DEPLOY.bat

cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                    ✅ ALL DONE! SUCCESS!                            ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo    Great news! Everything is installed and ready! 🎉
echo.
echo    Now you can start using the voice agent.
echo.
echo    Press any key to go back to the menu...
pause >nul
goto START

REM ============================================================================
REM  MOVE TO ANOTHER COMPUTER
REM ============================================================================
:MOVE_TO_ANOTHER
cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║           📦 MOVING TO ANOTHER COMPUTER - EASY PEASY!              ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo    No problem! I'll create a file you can copy to your other computer.
echo.
echo    I'll keep ALL your settings, so you don't have to set up again!
echo.
echo    Here's what will happen:
echo.
echo    1. I'll create a ZIP file (like a package) 📦
echo    2. I'll show you where it is
echo    3. You copy it to your other computer (USB stick, etc.)
echo    4. On the other computer, unzip it and run this file again
echo    5. Choose option 1 (First time setup)
echo    6. Done! Everything works just like here!
echo.
echo    Ready to create the package?
echo.
echo.
set /p CREATE="    Press Y to create the package, or N to go back: "
if /i not "%CREATE%"=="Y" goto START

cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                ⏳ CREATING PACKAGE... PLEASE WAIT                   ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo    This will take about 1 minute...
echo.

call CREATE_PACKAGE_WITH_DB.bat

cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                  ✅ PACKAGE CREATED! HERE'S WHAT TO DO              ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo    🎉 Success! I created a ZIP file for you!
echo.
echo    NEXT STEPS (Super Easy):
echo    ════════════════════════
echo.
echo    1. I'm going to open a folder showing the ZIP file
echo.
echo    2. Copy that ZIP file to a USB stick (or send it however you want)
echo.
echo    3. On your OTHER computer:
echo       • Copy the ZIP file there
echo       • Right-click the ZIP → "Extract All"
echo       • Open the extracted folder
echo       • Double-click "SUPER_SIMPLE_START.bat"
echo       • Choose option 1 (First time setup)
echo.
echo    That's it! Your other computer will have everything set up! 🎊
echo.
echo.
echo    Press any key and I'll show you the ZIP file...
pause >nul

REM Find the most recent package
for /f "delims=" %%a in ('dir /b /od "..\vonage-agent-with-db-*.zip" 2^>nul') do set "LATEST_ZIP=%%a"
if defined LATEST_ZIP (
    explorer /select,"..\%LATEST_ZIP%"
) else (
    explorer ..
)

echo.
echo    Did you see the ZIP file?
echo.
echo    Press any key to go back to the menu...
pause >nul
goto START

REM ============================================================================
REM  START THE VOICE AGENT
REM ============================================================================
:START_IT
cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                  ▶️  STARTING THE VOICE AGENT                       ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo.

REM Check if it's set up
if not exist .venv (
    echo    ⚠️  Oops! It looks like you haven't set up yet.
    echo.
    echo    You need to do the First Time Setup first.
    echo.
    echo    Don't worry - just go back and choose option 1!
    echo.
    echo.
    echo    Press any key to go back...
    pause >nul
    goto START
)

echo    Great! Starting the voice agent now...
echo.
echo    The server will start and you'll see some messages.
echo.
echo    When you see "Server Started Successfully", you're good to go!
echo.
echo    To STOP the server later, just press Ctrl+C
echo.
echo    ════════════════════════════════════════════════════════════════════
echo.

call START_SERVER.bat

echo.
echo    Server stopped.
echo.
echo    Press any key to go back to the menu...
pause >nul
goto START

REM ============================================================================
REM  HELP
REM ============================================================================
:HELP_ME
cls
echo.
echo    ╔════════════════════════════════════════════════════════════════════╗
echo    ║                       🆘 HELP - DON'T WORRY!                        ║
echo    ╚════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo    No worries! Let me explain what each option does:
echo.
echo.
echo    OPTION 1: First Time Setup 🚀
echo    ════════════════════════════
echo    Choose this if:
echo    • This is your first time using this
echo    • You just copied the files to this computer
echo    • You want to install everything
echo.
echo    This option sets up everything automatically. Just wait and it's done!
echo.
echo.
echo    OPTION 2: Move to Another Computer 📦
echo    ══════════════════════════════════════
echo    Choose this if:
echo    • You want to use this on a different computer
echo    • You want to make a backup
echo    • You want to copy your setup to another machine
echo.
echo    This creates a ZIP file you can copy to another computer.
echo    All your settings go with it!
echo.
echo.
echo    OPTION 3: Start the Voice Agent ▶️
echo    ═══════════════════════════════════
echo    Choose this if:
echo    • Everything is already set up
echo    • You want to start using the voice agent
echo    • You just want to turn it on
echo.
echo    This is what you'll use every day after setup!
echo.
echo.
echo    ════════════════════════════════════════════════════════════════════
echo.
echo    💡 STILL NOT SURE?
echo.
echo    If this is your very FIRST time: Choose option 1
echo    If you want to START using it: Choose option 3
echo    If you want to COPY to another computer: Choose option 2
echo.
echo.
echo    Press any key to go back to the menu...
pause >nul
goto START
