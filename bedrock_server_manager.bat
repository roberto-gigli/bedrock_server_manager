@echo off
REM Bedrock Server Updater - Windows Batch Script
REM This script simplifies updater execution on Windows

REM Get script directory
set SCRIPT_DIR=%~dp0

echo ===============================================
echo    BEDROCK SERVER UPDATER - Windows
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if requests is installed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing requests library...
    pip install requests
    if errorlevel 1 (
        echo ERROR: Unable to install requests
        pause
        exit /b 1
    )
)

REM Main menu
:MENU
echo.
echo Choose an option:
echo 1. Check updates
echo 2. Update server (Release)
echo 3. Update server (Preview)
echo 4. Force update
echo 5. Install server from scratch (Release)
echo 6. Install server from scratch (Preview)
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto OPTION1
if "%choice%"=="2" goto OPTION2
if "%choice%"=="3" goto OPTION3
if "%choice%"=="4" goto OPTION4
if "%choice%"=="5" goto OPTION5
if "%choice%"=="6" goto OPTION6
if "%choice%"=="7" goto OPTION7

echo Scelta non valida!
goto MENU

:OPTION1
echo.
echo Checking for updates...
python "%SCRIPT_DIR%update.py" --check-only
goto MENU

:OPTION2
echo.
echo Updating server (Release)...
python "%SCRIPT_DIR%update.py"
goto MENU

:OPTION3
echo.
echo Updating server (Preview)...
python "%SCRIPT_DIR%update.py" --preview
goto MENU

:OPTION4
echo.
echo Force update...
python "%SCRIPT_DIR%update.py" --force
goto MENU

:OPTION5
echo.
echo Installing server from scratch (Release)...
python "%SCRIPT_DIR%update.py" --install
goto MENU

:OPTION6
echo.
echo Installing server from scratch (Preview)...
python "%SCRIPT_DIR%update.py" --install --preview
goto MENU

:OPTION7
echo Exit...
exit /b 0
