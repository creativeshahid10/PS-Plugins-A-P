#!/bin/bash
clear
echo "======================================================================"
echo "    PIXELSQUAD AFTER EFFECTS SUITE - 1-CLICK CLEAN UNINSTALLER"
echo "======================================================================"
echo ""

USER_CEP="$HOME/Library/Application Support/Adobe/CEP/extensions"
SYS_CEP="/Library/Application Support/Adobe/CEP/extensions"

echo "Removing PixelSquad After Effects panels..."
for panel in PixelSquad-Motion-Studio PixelSquad-Text PixelSquad-Tools Bodymovin; do
    rm -rf "$USER_CEP/$panel" 2>/dev/null
    sudo rm -rf "$SYS_CEP/$panel" 2>/dev/null
done

echo ""
echo "SUCCESS: PixelSquad After Effects Suite completely removed!"
echo ""
read -p "Press Enter to exit..."