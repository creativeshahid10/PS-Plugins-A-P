:: ====================================================================
:: PixelSquad Creative Suite
:: Copyright (C) 2026 PixelSquad. All Rights Reserved.
:: Author: Mohammed Shahid <hello@pixelsquad.in>
:: ====================================================================
@echo off
title Pixel Squad - Uninstall PSCaptions Extension
color 0C
cls

echo ==============================================================================
echo               UNINSTALL PSCAPTIONS EXTENSION FROM PREMIERE PRO
echo ==============================================================================
echo.
set /p confirm="Kya aap sach me PSCaptions ko uninstall karna chahte hain? (Y/N): "
if /I not "%confirm%"=="Y" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

set "TARGET_DIR=%APPDATA%\Adobe\CEP\extensions\PixelSquad-PSCaptions"
if exist "%TARGET_DIR%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item -Path [System.Environment]::ExpandEnvironmentVariables('%%TARGET_DIR%%') -Recurse -Force -ErrorAction SilentlyContinue"
    echo.
    echo [SUCCESS] PSCaptions has been uninstalled from your system.
) else (
    echo.
    echo [INFO] PSCaptions was not found installed in %TARGET_DIR%.
)
echo.
pause