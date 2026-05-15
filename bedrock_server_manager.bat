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
echo 2. Update server (Release) [requires Administrator]
echo 3. Update server (Preview) [requires Administrator]
echo 4. Force update [requires Administrator]
echo 5. Install server from scratch (Release) [requires Administrator]
echo 6. Install server from scratch (Preview) [requires Administrator]
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
python "%SCRIPT_DIR%bedrock_server_manager.py" --check-only
goto MENU

:OPTION2
call :CHECK_ADMIN
if errorlevel 1 (
    echo.
    echo ERROR: Administrator privileges are required for update/install operations.
    echo Re-run this .bat file as Administrator.
    pause
    goto MENU
)
echo.
echo Updating server (Release)...
python "%SCRIPT_DIR%bedrock_server_manager.py"
goto MENU

:OPTION3
call :CHECK_ADMIN
if errorlevel 1 (
    echo.
    echo ERROR: Administrator privileges are required for update/install operations.
    echo Re-run this .bat file as Administrator.
    pause
    goto MENU
)
echo.
echo Updating server (Preview)...
python "%SCRIPT_DIR%bedrock_server_manager.py" --preview
goto MENU

:OPTION4
call :CHECK_ADMIN
if errorlevel 1 (
    echo.
    echo ERROR: Administrator privileges are required for update/install operations.
    echo Re-run this .bat file as Administrator.
    pause
    goto MENU
)
echo.
echo Force update...
python "%SCRIPT_DIR%bedrock_server_manager.py" --force
goto MENU

:OPTION5
call :CHECK_ADMIN
if errorlevel 1 (
    echo.
    echo ERROR: Administrator privileges are required for update/install operations.
    echo Re-run this .bat file as Administrator.
    pause
    goto MENU
)
echo.
echo Installing server from scratch (Release)...
python "%SCRIPT_DIR%bedrock_server_manager.py" --install
goto MENU

:OPTION6
call :CHECK_ADMIN
if errorlevel 1 (
    echo.
    echo ERROR: Administrator privileges are required for update/install operations.
    echo Re-run this .bat file as Administrator.
    pause
    goto MENU
)
echo.
echo Installing server from scratch (Preview)...
python "%SCRIPT_DIR%bedrock_server_manager.py" --install --preview
goto MENU

:OPTION7
echo Exit...
exit /b 0

:CHECK_ADMIN
net session >nul 2>&1
if %errorlevel%==0 exit /b 0
exit /b 1
