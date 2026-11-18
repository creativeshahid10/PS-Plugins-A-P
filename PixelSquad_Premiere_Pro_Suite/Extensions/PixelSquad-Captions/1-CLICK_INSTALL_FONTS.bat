:: ====================================================================
:: PixelSquad Creative Suite
:: Copyright (C) 2026 PixelSquad. All Rights Reserved.
:: Author: Mohammed Shahid <hello@pixelsquad.in>
:: ====================================================================
@echo off
title Pixel Squad - PSCaptions Fonts Installer
color 0E
cls

echo ==============================================================================
echo           PSCAPTIONS - AUTOMATIC FONTS INSTALLER (10 BOLD FONTS)
echo ==============================================================================
echo.
echo Installing viral caption fonts into Windows...
powershell -NoProfile -ExecutionPolicy Bypass -Command " = '%~dp0fonts';  = [System.Environment]::ExpandEnvironmentVariables('%%LOCALAPPDATA%%\Microsoft\Windows\Fonts'); if (-not (Test-Path )) { New-Item -ItemType Directory -Path  -Force | Out-Null };  = Get-ChildItem -Path  -Recurse | Where-Object { .Extension -eq '.ttf' -or .Extension -eq '.otf' }; foreach ( in ) { try {  = Join-Path  .Name; Copy-Item .FullName -Destination  -Force -ErrorAction SilentlyContinue;  = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts';  = .BaseName + ' [TrueType]'; Set-ItemProperty -Path  -Name  -Value  -Force -ErrorAction SilentlyContinue; Write-Host ('[OK] Installed: ' + .Name) } catch {} }"
echo.
echo ==============================================================================
echo [SUCCESS] ALL FONTS INSTALLED SUCCESSFULLY!
echo ==============================================================================
echo.
pause