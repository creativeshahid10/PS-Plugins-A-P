#!/bin/bash
clear
echo "======================================================================"
echo "    PIXELSQUAD PREMIERE PRO SUITE - SMART SELECTIVE UPDATER"
echo "======================================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXT_SRC="$SCRIPT_DIR/Extensions"

USER_CEP="$HOME/Library/Application Support/Adobe/CEP/extensions"
SYS_CEP="/Library/Application Support/Adobe/CEP/extensions"

echo "Selectively syncing modified files..."
for panel in "$EXT_SRC"/*; do
    if [ -d "$panel" ]; then
        panel_name=$(basename "$panel")
        echo "Updating: $panel_name"
        rsync -avu "$panel/" "$USER_CEP/$panel_name/"
        sudo rsync -avu "$panel/" "$SYS_CEP/$panel_name/" 2>/dev/null
    fi
done

echo ""
echo "SUCCESS: Updated only changed files in Premiere Pro suite!"
echo ""
read -p "Press Enter to exit..."