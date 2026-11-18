# Copyright (C) 2026 PixelSquad. All Rights Reserved.
# Author: Mohammed Shahid <hello@pixelsquad.in>

#!/bin/bash
# PixelSquad After Effects Suite - 1-Click macOS Setup

clear
echo "======================================================================"
echo "      PIXELSQUAD AFTER EFFECTS SUITE - 1-CLICK macOS INSTALLER"
echo "======================================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXT_SRC="$SCRIPT_DIR/Extensions"

USER_CEP="$HOME/Library/Application Support/Adobe/CEP/extensions"
SYS_CEP="/Library/Application Support/Adobe/CEP/extensions"

echo "[1/3] Enabling Adobe Debug Mode for macOS..."
for ver in {7..30}; do
    defaults write com.adobe.CSXS.$ver PlayerDebugMode 1 2>/dev/null
done
echo "     -> CSXS PlayerDebugMode enabled."

echo ""
echo "[2/3] Installing After Effects Extensions..."
mkdir -p "$USER_CEP"
sudo mkdir -p "$SYS_CEP" 2>/dev/null

for panel in "$EXT_SRC"/*; do
    if [ -d "$panel" ]; then
        panel_name=$(basename "$panel")
        echo "     -> Installing Panel: $panel_name"
        cp -R "$panel" "$USER_CEP/"
        sudo cp -R "$panel" "$SYS_CEP/" 2>/dev/null
    fi
done

echo ""
echo "[3/3] Clearing macOS Gatekeeper quarantine..."
xattr -dr com.apple.quarantine "$USER_CEP" 2>/dev/null
sudo xattr -dr com.apple.quarantine "$SYS_CEP" 2>/dev/null

echo ""
echo "======================================================================"
echo "   SUCCESS! PIXELSQUAD AFTER EFFECTS SUITE INSTALLED ON macOS!"
echo "   Open After Effects > Window > Extensions > PixelSquad Panels"
echo "======================================================================"
echo ""
read -p "Press Enter to exit..."