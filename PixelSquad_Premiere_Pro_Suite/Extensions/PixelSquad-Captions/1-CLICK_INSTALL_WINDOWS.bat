:: ====================================================================
:: PixelSquad Creative Suite
:: Copyright (C) 2026 PixelSquad. All Rights Reserved.
:: Author: Mohammed Shahid <hello@pixelsquad.in>
:: ====================================================================
@echo off
title Pixel Squad - PSCaptions Suite 1-Click Installer
color 0B
cls

echo ==============================================================================
echo        PIXEL SQUAD - PSCAPTIONS VIRAL REELS SUITE FOR PREMIERE PRO
echo ==============================================================================
echo.
echo  Adobe Premiere Pro (CC 2020 se CC 2026+) ke liye 1-Click Automated Installer.
echo.

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: 1. LOCATE SOURCE DIRECTORY & VERIFY NOT RUNNING IN CORRUPTED ARCHIVE
if exist "%SCRIPT_DIR%\PixelSquad-PSCaptions\CSXS\manifest.xml" (
    set "SRC_DIR=%SCRIPT_DIR%\PixelSquad-PSCaptions"
    set "FONTS_DIR=%SCRIPT_DIR%\fonts"
) else if exist "%SCRIPT_DIR%\CSXS\manifest.xml" (
    set "SRC_DIR=%SCRIPT_DIR%"
    set "FONTS_DIR=%SCRIPT_DIR%\fonts"
) else (
    color 0C
    echo [ERROR] AAPNE ZIP FILE KO EXTRACT NAHI KIYA HAI!
    echo.
    echo  Kripya in steps ko follow karein:
    echo  1. PSCaptions ZIP file par RIGHT-CLICK karein.
    echo  2. Extract All [Sabhi Extract Karein] par click karein.
    echo  3. Extract hone ke baad naye folder me jayein.
    echo  4. Wahan se 1-CLICK_INSTALL_WINDOWS.bat ko run karein.
    echo.
    echo ==============================================================================
    pause
    exit /b 1
)

:: 2. CHECK IF PREMIERE PRO IS CURRENTLY RUNNING
tasklist /FI "IMAGENAME eq Adobe Premiere Pro.exe" 2>NUL | find /I /N "Adobe Premiere Pro.exe">NUL
if "%ERRORLEVEL%"=="0" (
    color 0E
    echo [WARNING] Adobe Premiere Pro abhi open hai!
    echo           Kripya apna project save karke Premiere Pro ko CLOSE karein,
    echo           fir installation continue karne ke liye koi bhi key dabayein.
    echo.
    pause
    color 0B
    echo.
)

:: 3. ENABLE ADOBE CEP EXTENSION DEBUG MODE (CSXS.8 to CSXS.22)
echo [*] STEP 1/3: Enabling Adobe CEP Extensions in Windows Registry...
for %%v in (8 9 10 11 12 13 14 15 16 17 18 19 20 21 22) do (
    reg add "HKCU\Software\Adobe\CSXS.%%v" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>&1
)
echo      - Registry PlayerDebugMode (CSXS 8-22) successfully enabled!

:: 4. DEPLOY EXTENSION FILES TO APPDATA
echo.
echo [*] STEP 2/3: Deploying PSCaptions extension files...
set "DEST_DIR=%APPDATA%\Adobe\CEP\extensions\PixelSquad-PSCaptions"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$src = '%SRC_DIR%'; $dst = '%DEST_DIR%'; $parent = Split-Path $dst -Parent; if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }; if (Test-Path $dst) { Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue }; Copy-Item -Path $src -Destination $dst -Recurse -Force" >nul 2>&1

if exist "%DEST_DIR%\CSXS\manifest.xml" (
    echo      - Extension files copied successfully!
    echo      - Location: %DEST_DIR%
) else (
    color 0C
    echo [ERROR] Extension files copy nahi ho payi.
    echo         Kripya is file par Right-Click karke "Run as administrator" karein.
    echo.
    pause
    exit /b 1
)

:: 5. INSTALL RECOMMENDED FONTS (SAFE USER-LEVEL INSTALLATION)
echo.
echo [*] STEP 3/3: Installing Required Typography Fonts...
if exist "%FONTS_DIR%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$srcFonts = '%FONTS_DIR%'; $uDir = [System.Environment]::ExpandEnvironmentVariables('%LOCALAPPDATA%\Microsoft\Windows\Fonts'); if (-not (Test-Path $uDir)) { New-Item -ItemType Directory -Path $uDir -Force | Out-Null }; $fonts = Get-ChildItem -Path $srcFonts -Recurse | Where-Object { $_.Extension -eq '.ttf' -or $_.Extension -eq '.otf' }; foreach ($f in $fonts) { try { $target = Join-Path $uDir $f.Name; Copy-Item $f.FullName -Destination $target -Force -ErrorAction SilentlyContinue; $reg = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'; $prop = $f.BaseName + ' [TrueType]'; Set-ItemProperty -Path $reg -Name $prop -Value $target -Force -ErrorAction SilentlyContinue } catch {} }" >nul 2>&1
    echo      - Fonts successfully installed into Windows!
) else (
    echo      - Fonts folder not found, skipping font registration.
)

:: 6. SUCCESS CONFIRMATION & USAGE INSTRUCTIONS
echo.
echo ==============================================================================
echo [SUCCESS] PSCAPTIONS SUITE SUCCESSFULLY INSTALLED!
echo ==============================================================================
echo.
echo  PREMIERE PRO ME KAISE OPEN KAREIN:
echo  1. Adobe Premiere Pro open karein.
echo  2. Kisi bhi project aur sequence ko open karein.
echo  3. Top Menu bar me jayein: Window -^> Extensions -^> PSCaptions
echo  4. PSCaptions Panel open ho jayega aur aapke caption presets ready hain!
echo.
echo  NOTE: Agar Extensions menu me PSCaptions nahi dikhe, toh Premiere Pro ko
echo        ek baar restart (band karke wapas open) karein.
echo.
echo ==============================================================================
echo.
pause