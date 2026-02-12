@echo off
REM Bedrock Server Updater - Windows Batch Script
REM Questo script semplifica l'esecuzione dell'updater su Windows

echo ===============================================
echo    BEDROCK SERVER UPDATER - Windows
echo ===============================================
echo.

REM Verifica se Python è installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo Installa Python da: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verifica se requests è installato
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installazione della libreria requests...
    pip install requests
    if errorlevel 1 (
        echo ERRORE: Impossibile installare requests
        pause
        exit /b 1
    )
)

REM Menu principale
:MENU
echo.
echo Scegli un'opzione:
echo 1. Controlla aggiornamenti
echo 2. Aggiorna server (Release)
echo 3. Aggiorna server (Preview)
echo 4. Aggiornamento forzato
echo 5. Esci
echo.
set /p choice="Inserisci la tua scelta (1-5): "

if "%choice%"=="1" (
    echo.
    echo Controllo aggiornamenti...
    python update.py --check-only
    goto MENU
)

if "%choice%"=="2" (
    echo.
    echo Aggiornamento del server (Release)...
    python update.py
    goto MENU
)

if "%choice%"=="3" (
    echo.
    echo Aggiornamento del server (Preview)...
    python update.py --preview
    goto MENU
)

if "%choice%"=="4" (
    echo.
    echo Aggiornamento forzato...
    python update.py --force
    goto MENU
)

if "%choice%"=="5" (
    echo Uscita...
    exit /b 0
)

echo Scelta non valida!
goto MENU
