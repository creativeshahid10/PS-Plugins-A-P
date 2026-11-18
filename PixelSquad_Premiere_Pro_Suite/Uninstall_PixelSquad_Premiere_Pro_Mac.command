#!/bin/bash
clear
echo "======================================================================"
echo "    PIXELSQUAD PREMIERE PRO SUITE - 1-CLICK CLEAN UNINSTALLER"
echo "======================================================================"
echo ""

USER_CEP="$HOME/Library/Application Support/Adobe/CEP/extensions"
SYS_CEP="/Library/Application Support/Adobe/CEP/extensions"

echo "Removing PixelSquad Premiere Pro panels..."
rm -rf "$USER_CEP/PixelSquad-Studio" 2>/dev/null
rm -rf "$USER_CEP/PixelSquad-Captions" 2>/dev/null
sudo rm -rf "$SYS_CEP/PixelSquad-Studio" 2>/dev/null
sudo rm -rf "$SYS_CEP/PixelSquad-Captions" 2>/dev/null

echo ""
echo "SUCCESS: PixelSquad Premiere Pro Suite completely removed!"
echo ""
read -p "Press Enter to exit..."