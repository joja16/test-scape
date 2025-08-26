@echo off
:: ============================================================
:: Auto Scrape - Quick Deploy Script
:: One-click build and deployment for Windows 11
:: ============================================================

setlocal enabledelayedexpansion
color 0A

echo ============================================================
echo        Auto Scrape Quick Deploy - Windows 11
echo ============================================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires Administrator privileges.
    echo Requesting elevation...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Set working directory
cd /d "%~dp0"

echo [1/3] Building application...
echo ----------------------------------------
powershell -ExecutionPolicy Bypass -File build.ps1 -Clean
if %errorlevel% neq 0 (
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [2/3] Deploying application...
echo ----------------------------------------
powershell -ExecutionPolicy Bypass -File deploy.ps1 -Silent
if %errorlevel% neq 0 (
    echo Deployment failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [3/3] Installation complete!
echo ============================================================
echo.
echo Auto Scrape has been successfully installed!
echo.
echo You can find the application in:
echo - Start Menu: Auto Scrape
echo - Desktop: Auto Scrape shortcut
echo - Installation folder: %ProgramFiles%\Auto Scrape
echo.
echo To uninstall, run: deploy.ps1 -Uninstall
echo.
pause
