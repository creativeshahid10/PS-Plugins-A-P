@echo off
setlocal EnableDelayedExpansion
title PixelSquad After Effects Suite - 1-Click Installer

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator Privileges...
    powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c ""%~dpnx0""' -Verb RunAs"
    exit /b
)

color 0B
echo ======================================================================
echo       PIXELSQUAD AFTER EFFECTS SUITE - 1-CLICK ALL-IN-ONE SETUP
echo             PixelSquad GUI Pro + PixelSquad Wheel + Motion Studio
echo ======================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXT_SRC=%SCRIPT_DIR%Extensions"
set "MC_SRC=%SCRIPT_DIR%MediaCore_Plugins"

set "USER_CEP=%APPDATA%\Adobe\CEP\extensions"
set "GLOBAL_CEP=%CommonProgramFiles(x86)%\Adobe\CEP\extensions"
set "MEDIACORE_DIR=%CommonProgramFiles%\Adobe\Common\Plug-ins\7.0\MediaCore\PixelSquad"

echo [1/3] Enabling Adobe Registry Debug Mode (CSXS 7 to 30)...
for /L %%i in (7,1,30) do (
    reg add "HKCU\Software\Adobe\CSXS.%%i" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
    reg add "HKLM\SOFTWARE\Adobe\CSXS.%%i" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
    reg add "HKLM\SOFTWARE\WOW6432Node\Adobe\CSXS.%%i" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
)
echo      -> Adobe Debug Mode enabled successfully.

echo.
echo [2/3] Installing After Effects Extensions into CEP...
if not exist "%USER_CEP%" mkdir "%USER_CEP%"
if not exist "%GLOBAL_CEP%" mkdir "%GLOBAL_CEP%"

REM Remove any old conflicting folder names
if exist "%USER_CEP%\PixelSquad-GUI-Pro" rd /s /q "%USER_CEP%\PixelSquad-GUI-Pro" >nul 2>&1
if exist "%GLOBAL_CEP%\PixelSquad-GUI-Pro" rd /s /q "%GLOBAL_CEP%\PixelSquad-GUI-Pro" >nul 2>&1
if exist "%USER_CEP%\PixelSquad-Wheel" rd /s /q "%USER_CEP%\PixelSquad-Wheel" >nul 2>&1
if exist "%GLOBAL_CEP%\PixelSquad-Wheel" rd /s /q "%GLOBAL_CEP%\PixelSquad-Wheel" >nul 2>&1

for /d %%D in ("%EXT_SRC%\*") do (
    echo      -> Installing Panel: %%~nxD
    robocopy "%%D" "%USER_CEP%\%%~nxD" /E /R:1 /W:1 /NP /NFL /NDL >nul
    robocopy "%%D" "%GLOBAL_CEP%\%%~nxD" /E /R:1 /W:1 /NP /NFL /NDL >nul
)
echo      -> All After Effects Extensions installed into CEP.

echo.
echo [3/3] Installing MediaCore Plugins (.aex)...
if exist "%MC_SRC%" (
    if not exist "%MEDIACORE_DIR%" mkdir "%MEDIACORE_DIR%"
    copy /Y "%MC_SRC%\*.aex" "%MEDIACORE_DIR%\" >nul 2>&1
    echo      -> MediaCore Plugins installed: FlexGrid, LiquidGlass, Masker, MosaicMAX.
)

echo.
echo ======================================================================
echo    SUCCESS! PIXELSQUAD AFTER EFFECTS SUITE IS INSTALLED!
echo.
echo    How to use in After Effects:
echo    1. Open Adobe After Effects.
echo    2. Go to top menu: Window ^> Extensions
echo    3. Panels Available:
echo       - PixelSquad GUI Pro
echo       - PixelSquad Wheel
echo       - PixelSquad Motion Studio
echo       - PixelSquad Text
echo       - PixelSquad Tools
echo       - Bodymovin
echo ======================================================================
echo.
pause
