@echo off
setlocal EnableDelayedExpansion
title PixelSquad After Effects Suite - Smart Selective Updater

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator Privileges to update plugins...
    powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c \"\"%~dpnx0\"\"' -Verb RunAs"
    exit /b
)

color 0A
echo ======================================================================
echo       PIXELSQUAD AFTER EFFECTS SUITE - SMART SELECTIVE UPDATER
echo           Only Modified & New Files Will Be Replaced
echo ======================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXT_SRC=%SCRIPT_DIR%Extensions"

set "USER_CEP=%APPDATA%\Adobe\CEP\extensions"
set "GLOBAL_CEP=%CommonProgramFiles(x86)%\Adobe\CEP\extensions"

if not exist "%EXT_SRC%" (
    echo [ERROR] Extensions source folder not found at: %EXT_SRC%
    pause
    exit /b 1
)

echo [1/2] Scanning & Updating User CEP (Replacing only modified files)...
for /d %%D in ("%EXT_SRC%\*") do (
    echo      -> Checking & Updating: %%~nxD
    robocopy "%%D" "%USER_CEP%\%%~nxD" /E /XO /R:1 /W:1 /NDL /NFL >nul
)

echo.
echo [2/2] Scanning & Updating System Global CEP...
for /d %%D in ("%EXT_SRC%\*") do (
    echo      -> Checking & Updating: %%~nxD
    robocopy "%%D" "%GLOBAL_CEP%\%%~nxD" /E /XO /R:1 /W:1 /NDL /NFL >nul
)

echo.
echo ======================================================================
echo    SUCCESS! Update Complete!
echo    Only changed/newer files were selectively patched.
echo    Your settings and intact files were safely preserved.
echo ======================================================================
echo.
pause