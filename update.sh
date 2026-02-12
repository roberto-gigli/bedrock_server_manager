#!/bin/bash

# Bedrock Server Updater - Linux Bash Script
# Questo script semplifica l'esecuzione dell'updater su Linux

echo "==============================================="
echo "    BEDROCK SERVER UPDATER - Linux"
echo "==============================================="
echo

# Verifica se Python è installato
if ! command -v python3 &> /dev/null; then
    echo "ERRORE: Python3 non trovato!"
    echo "Installa Python3 con: sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

# Verifica se pip è installato
if ! command -v pip3 &> /dev/null; then
    echo "ERRORE: pip3 non trovato!"
    echo "Installa pip3 con: sudo apt install python3-pip"
    exit 1
fi

# Verifica se requests è installato
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installazione della libreria requests..."
    pip3 install requests
    if [ $? -ne 0 ]; then
        echo "ERRORE: Impossibile installare requests"
        echo "Prova con: sudo pip3 install requests"
        exit 1
    fi
fi

# Funzione per il menu
show_menu() {
    echo
    echo "Scegli un'opzione:"
    echo "1. Controlla aggiornamenti"
    echo "2. Aggiorna server (Release)"
    echo "3. Aggiorna server (Preview)"
    echo "4. Aggiornamento forzato"
    echo "5. Esci"
    echo
}

# Menu principale
while true; do
    show_menu
    read -p "Inserisci la tua scelta (1-5): " choice
    
    case $choice in
        1)
            echo
            echo "Controllo aggiornamenti..."
            python3 update.py --check-only
            ;;
        2)
            echo
            echo "Aggiornamento del server (Release)..."
            python3 update.py
            ;;
        3)
            echo
            echo "Aggiornamento del server (Preview)..."
            python3 update.py --preview
            ;;
        4)
            echo
            echo "Aggiornamento forzato..."
            python3 update.py --force
            ;;
        5)
            echo "Uscita..."
            exit 0
            ;;
        *)
            echo "Scelta non valida!"
            ;;
    esac
done
