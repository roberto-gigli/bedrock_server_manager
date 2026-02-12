#!/bin/bash

# Bedrock Server Updater - Linux Bash Script
# This script simplifies updater execution on Linux

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==============================================="
echo "    BEDROCK SERVER UPDATER - Linux"
echo "==============================================="
echo

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found!"
    echo "Install Python3 with: sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 not found!"
    echo "Install pip3 with: sudo apt install python3-pip"
    exit 1
fi

# Check if requests is installed
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing requests library..."
    pip3 install requests
    if [ $? -ne 0 ]; then
        echo "ERROR: Unable to install requests"
        echo "Try with: sudo pip3 install requests"
        exit 1
    fi
fi

# Function for menu
show_menu() {
    echo
    echo "Choose an option:"
    echo "1. Check updates"
    echo "2. Update server (Release)"
    echo "3. Update server (Preview)"
    echo "4. Force update"
    echo "5. Install server from scratch (Release)"
    echo "6. Install server from scratch (Preview)"
    echo "7. Exit"
    echo
}

# Main menu
while true; do
    show_menu
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1)
            echo
            echo "Checking for updates..."
            python3 "$SCRIPT_DIR/bedrock_server_manager.py" --check-only
            ;;
        2)
            echo
            echo "Updating server (Release)..."
            python3 "$SCRIPT_DIR/bedrock_server_manager.py"
            ;;
        3)
            echo
            echo "Updating server (Preview)..."
            python3 "$SCRIPT_DIR/bedrock_server_manager.py" --preview
            ;;
        4)
            echo
            echo "Force update..."
            python3 "$SCRIPT_DIR/bedrock_server_manager.py" --force
            ;;
        5)
            echo
            echo "Installing server from scratch (Release)..."
            python3 "$SCRIPT_DIR/bedrock_server_manager.py" --install
            ;;
        6)
            echo
            echo "Installing server from scratch (Preview)..."
            python3 "$SCRIPT_DIR/bedrock_server_manager.py" --install --preview
            ;;
        7)
            echo "Exit..."
            exit 0
            ;;
        *)
            echo "Invalid choice!"
            ;;
    esac
done
