@echo off
setlocal EnableDelayedExpansion
title PixelSquad Premiere Pro Suite - Clean Uninstaller

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c \"\"%~dpnx0\"\"' -Verb RunAs"
    exit /b
)

color 0C
echo Removing PixelSquad Premiere Pro components...
for %%P in (com.flexultimate.ext in.captureflex.flexwheel PixelSquad-ULTIMATE PixelSquad-Wheel PixelSquad-Captions PixelSquad-Studio) do (
    rmdir /S /Q "%APPDATA%\\Adobe\\CEP\\extensions\\%%P" >nul 2>&1
    rmdir /S /Q "%CommonProgramFiles(x86)%\\Adobe\\CEP\\extensions\\%%P" >nul 2>&1
)
rmdir /S /Q "%CommonProgramFiles%\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore\\PixelSquad" >nul 2>&1

echo SUCCESS: Uninstalled all PixelSquad Premiere Pro panels and plugins!
pause
