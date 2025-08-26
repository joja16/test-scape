# Auto Scrape - Windows 11 Deployment Guide

## 📦 Overview

This guide provides complete instructions for building and deploying the Auto Scrape application as a Windows 11 installer package. The deployment system includes automated build scripts, professional installer creation, and one-click deployment capabilities.

## 🚀 Quick Start (One-Click Deployment)

### Fastest Method:
1. **Right-click** on `QUICK_DEPLOY.bat`
2. Select **"Run as administrator"**
3. Wait for the automatic build and installation to complete
4. The application will be installed and ready to use!

## 📋 Prerequisites

Before building the installer, ensure you have:

- ✅ **Windows 11** (64-bit)
- ✅ **Python 3.11+** installed and in PATH
- ✅ **PowerShell 5.1+** (comes with Windows)
- ✅ **Inno Setup 6** (optional, for creating installer)
  - Download from: https://jrsoftware.org/isdl.php
- ✅ **Administrator privileges** for deployment

## 🛠️ Build System Components

### 1. **build.ps1** - Build Script
Automates the entire build process:
- Creates virtual environment
- Installs dependencies
- Builds executable with PyInstaller
- Creates Windows installer with Inno Setup

### 2. **deploy.ps1** - Deployment Script
Handles automated installation:
- Silent installation with admin privileges
- Configuration deployment
- Scheduled task creation
- Desktop shortcut creation

### 3. **QUICK_DEPLOY.bat** - One-Click Solution
Combines building and deployment in a single command

## 📖 Detailed Instructions

### Method 1: Full Build & Deploy (Recommended)

```powershell
# Open PowerShell as Administrator
cd D:\code\BOT\auto-scrape

# Build the application
.\build.ps1 -Clean

# Deploy the installer
.\deploy.ps1
```

### Method 2: Build Only (For Distribution)

```powershell
# Build the installer package
.\build.ps1 -Clean -SkipInstaller

# The executable will be in: dist\AutoScrape\
# The installer (if created) will be in: dist\AutoScrape-Setup-1.0.0.exe
```

### Method 3: Deploy Existing Installer

```powershell
# Deploy from local installer
.\deploy.ps1 -InstallerPath "path\to\AutoScrape-Setup-1.0.0.exe"

# Deploy from network share
.\deploy.ps1 -InstallerPath "\\server\share\AutoScrape-Setup-1.0.0.exe"

# Deploy from URL
.\deploy.ps1 -InstallerPath "https://example.com/AutoScrape-Setup-1.0.0.exe"
```

## ⚙️ Advanced Options

### Build Script Options

```powershell
# Clean build (removes old files)
.\build.ps1 -Clean

# Build without installer (executable only)
.\build.ps1 -SkipInstaller

# Debug build (with console window)
.\build.ps1 -Debug
```

### Deployment Script Options

```powershell
# Silent installation (no prompts)
.\deploy.ps1 -Silent

# Custom installation directory
.\deploy.ps1 -InstallDir "C:\MyApps\AutoScrape"

# Deploy with custom configuration
.\deploy.ps1 -ConfigFile "path\to\custom_config.yaml"

# Create scheduled task for daily runs
.\deploy.ps1 -CreateScheduledTask

# Uninstall the application
.\deploy.ps1 -Uninstall
```

## 📁 Directory Structure

```
auto-scrape/
├── build.ps1              # Build automation script
├── deploy.ps1             # Deployment automation script
├── QUICK_DEPLOY.bat       # One-click build & deploy
├── build/
│   ├── auto_scrape.spec   # PyInstaller specification
│   └── installer.iss      # Inno Setup script
├── dist/
│   ├── AutoScrape/        # Compiled application files
│   └── AutoScrape-Setup-1.0.0.exe  # Installer package
└── resources/
    ├── app_icon.ico       # Application icon
    └── LICENSE.txt        # License file
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Python Not Found
```
Error: Python 3.11+ is not installed or not in PATH
```
**Solution:** Install Python from https://python.org and add to PATH

#### 2. Inno Setup Not Found
```
Warning: Inno Setup not found. Installer will not be created.
```
**Solution:** Install Inno Setup 6 from https://jrsoftware.org/isdl.php

#### 3. Access Denied
```
Error: Access is denied
```
**Solution:** Run scripts as Administrator

#### 4. Build Fails
```
Error: Failed to build executable
```
**Solution:** 
- Check Python dependencies: `pip list`
- Clear build cache: `.\build.ps1 -Clean`
- Check antivirus isn't blocking PyInstaller

## 🔐 Security Considerations

- The installer requires **Administrator privileges** for system-wide installation
- Windows Defender may flag the unsigned executable - this is normal for custom applications
- To avoid security warnings, consider code-signing the executable and installer

## 📊 Post-Installation

After successful installation:

1. **Application Location:** `C:\Program Files\Auto Scrape\`
2. **Start Menu:** Auto Scrape shortcut created
3. **Desktop:** Optional shortcut created
4. **Configuration:** Located in `config\` subdirectory
5. **Logs:** Stored in `logs\` subdirectory

## 🔄 Updates and Maintenance

### Updating the Application

1. Increment version in `setup.py` and build scripts
2. Run build process: `.\build.ps1 -Clean`
3. Deploy update: `.\deploy.ps1`

### Uninstalling

```powershell
# Via script
.\deploy.ps1 -Uninstall

# Via Windows Settings
# Settings → Apps → Auto Scrape → Uninstall
```

## 🎯 Deployment Scenarios

### Single Machine
Use `QUICK_DEPLOY.bat` for fastest deployment

### Multiple Machines (Network)
1. Build once: `.\build.ps1`
2. Share installer on network
3. On each machine: `.\deploy.ps1 -InstallerPath "\\server\share\installer.exe"`

### Silent Mass Deployment
```powershell
# For IT administrators
.\deploy.ps1 -Silent -InstallerPath "\\server\share\installer.exe" -CreateScheduledTask
```

## 📝 Customization

### Modify Installation Behavior
Edit `build\installer.iss` to customize:
- Installation directory
- Start menu entries
- File associations
- Registry entries

### Modify Build Process
Edit `build\auto_scrape.spec` to:
- Include/exclude files
- Change executable properties
- Add version information

## 💡 Tips

1. **Always test** the installer on a clean Windows 11 VM before distribution
2. **Keep logs** of deployments for troubleshooting
3. **Document** any custom configurations used
4. **Version control** your build and deployment scripts

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review application logs in `logs\` directory
3. Run build/deploy scripts with verbose output

## 📄 License

This deployment system is part of the Auto Scrape project and follows the same MIT License.

---

**Last Updated:** December 2024
**Version:** 1.0.0
