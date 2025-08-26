<#
.SYNOPSIS
    Automated deployment script for Auto Scrape application
.DESCRIPTION
    This script automates the deployment of Auto Scrape:
    - Downloads or uses local installer
    - Runs silent installation with admin privileges
    - Configures the application
    - Creates scheduled tasks (optional)
    - Verifies installation
.PARAMETER InstallerPath
    Path to the installer file (local or network)
.PARAMETER InstallDir
    Custom installation directory
.PARAMETER ConfigFile
    Path to configuration file to deploy
.PARAMETER Silent
    Run in silent mode without prompts
.PARAMETER CreateScheduledTask
    Create a scheduled task to run the application
.PARAMETER Uninstall
    Uninstall the application
#>

param(
    [string]$InstallerPath = ".\dist\AutoScrape-Setup-1.0.0.exe",
    [string]$InstallDir = "$env:ProgramFiles\Auto Scrape",
    [string]$ConfigFile,
    [switch]$Silent,
    [switch]$CreateScheduledTask,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "Auto Scrape"
$AppExecutable = "AutoScrape.exe"
$UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{E7F8A1B5-4C3D-4E2A-9F6B-8D7C6B5A4E3F}_is1"
$ScheduledTaskName = "AutoScrapeDaily"

# Output formatting
function Write-Step { param($msg) Write-Host "`n===> $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "ℹ $msg" -ForegroundColor Blue }

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Elevate to administrator if needed
function Request-AdminPrivileges {
    if (-not (Test-Administrator)) {
        Write-Warning "This script requires administrator privileges. Elevating..."
        
        $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
        
        # Add original parameters
        $PSBoundParameters.GetEnumerator() | ForEach-Object {
            if ($_.Value -is [switch]) {
                if ($_.Value) { $arguments += " -$($_.Key)" }
            } else {
                $arguments += " -$($_.Key) `"$($_.Value)`""
            }
        }
        
        Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -Verb RunAs
        exit
    }
}

# Check if application is installed
function Test-AppInstalled {
    if (Test-Path $UninstallKey) {
        $uninstallInfo = Get-ItemProperty -Path $UninstallKey -ErrorAction SilentlyContinue
        if ($uninstallInfo) {
            return @{
                Installed = $true
                Version = $uninstallInfo.DisplayVersion
                InstallLocation = $uninstallInfo.InstallLocation
                UninstallString = $uninstallInfo.UninstallString
            }
        }
    }
    return @{ Installed = $false }
}

# Uninstall application
function Uninstall-App {
    Write-Step "Uninstalling $AppName..."
    
    $appInfo = Test-AppInstalled
    if (-not $appInfo.Installed) {
        Write-Warning "$AppName is not installed"
        return
    }
    
    Write-Info "Found version $($appInfo.Version) at $($appInfo.InstallLocation)"
    
    # Stop running instances
    Get-Process | Where-Object { $_.Name -like "*AutoScrape*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Run uninstaller
    if ($appInfo.UninstallString) {
        $uninstallExe = $appInfo.UninstallString -replace '"', ''
        $uninstallArgs = "/SILENT", "/NORESTART"
        
        Write-Info "Running uninstaller..."
        $process = Start-Process -FilePath $uninstallExe -ArgumentList $uninstallArgs -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Success "$AppName uninstalled successfully"
            
            # Remove scheduled task if exists
            if (Get-ScheduledTask -TaskName $ScheduledTaskName -ErrorAction SilentlyContinue) {
                Unregister-ScheduledTask -TaskName $ScheduledTaskName -Confirm:$false
                Write-Success "Scheduled task removed"
            }
        } else {
            Write-Error "Uninstall failed with exit code: $($process.ExitCode)"
        }
    }
}

# Download installer if needed
function Get-Installer {
    param([string]$Path)
    
    if ($Path -match "^https?://") {
        Write-Step "Downloading installer..."
        $localPath = Join-Path $env:TEMP "AutoScrape-Setup.exe"
        
        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $Path -OutFile $localPath -UseBasicParsing
            Write-Success "Installer downloaded to $localPath"
            return $localPath
        } catch {
            Write-Error "Failed to download installer: $_"
            exit 1
        }
    } elseif (Test-Path $Path) {
        return (Resolve-Path $Path).Path
    } else {
        Write-Error "Installer not found: $Path"
        exit 1
    }
}

# Install application
function Install-App {
    param(
        [string]$InstallerFile,
        [string]$TargetDir
    )
    
    Write-Step "Installing $AppName..."
    
    # Check if already installed
    $appInfo = Test-AppInstalled
    if ($appInfo.Installed) {
        if (-not $Silent) {
            $response = Read-Host "$AppName version $($appInfo.Version) is already installed. Reinstall? (Y/N)"
            if ($response -ne 'Y') {
                Write-Warning "Installation cancelled"
                return $false
            }
        }
        Uninstall-App
    }
    
    # Prepare installation arguments
    $installArgs = @(
        "/SILENT",
        "/NORESTART",
        "/SUPPRESSMSGBOXES",
        "/SP-"
    )
    
    if ($TargetDir) {
        $installArgs += "/DIR=`"$TargetDir`""
    }
    
    Write-Info "Running installer..."
    $process = Start-Process -FilePath $InstallerFile -ArgumentList $installArgs -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Success "$AppName installed successfully"
        return $true
    } else {
        Write-Error "Installation failed with exit code: $($process.ExitCode)"
        return $false
    }
}

# Configure application
function Set-AppConfiguration {
    param([string]$ConfigPath)
    
    if (-not $ConfigPath) { return }
    
    Write-Step "Configuring application..."
    
    $appInfo = Test-AppInstalled
    if (-not $appInfo.Installed) {
        Write-Error "Application is not installed"
        return
    }
    
    $targetConfigDir = Join-Path $appInfo.InstallLocation "config"
    
    if (Test-Path $ConfigPath) {
        if (-not (Test-Path $targetConfigDir)) {
            New-Item -ItemType Directory -Path $targetConfigDir -Force | Out-Null
        }
        
        Copy-Item -Path $ConfigPath -Destination $targetConfigDir -Force
        Write-Success "Configuration deployed"
    } else {
        Write-Warning "Configuration file not found: $ConfigPath"
    }
}

# Create scheduled task
function New-AppScheduledTask {
    Write-Step "Creating scheduled task..."
    
    $appInfo = Test-AppInstalled
    if (-not $appInfo.Installed) {
        Write-Error "Application is not installed"
        return
    }
    
    $exePath = Join-Path $appInfo.InstallLocation $AppExecutable
    
    # Remove existing task if present
    if (Get-ScheduledTask -TaskName $ScheduledTaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $ScheduledTaskName -Confirm:$false
    }
    
    # Create new task
    $action = New-ScheduledTaskAction -Execute $exePath -WorkingDirectory $appInfo.InstallLocation
    $trigger = New-ScheduledTaskTrigger -Daily -At 9am
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Register-ScheduledTask -TaskName $ScheduledTaskName `
                          -Action $action `
                          -Trigger $trigger `
                          -Settings $settings `
                          -Principal $principal `
                          -Description "Automated web scraping with Auto Scrape" | Out-Null
    
    Write-Success "Scheduled task created: $ScheduledTaskName"
}

# Verify installation
function Test-Installation {
    Write-Step "Verifying installation..."
    
    $appInfo = Test-AppInstalled
    if (-not $appInfo.Installed) {
        Write-Error "Installation verification failed"
        return $false
    }
    
    $exePath = Join-Path $appInfo.InstallLocation $AppExecutable
    if (-not (Test-Path $exePath)) {
        Write-Error "Executable not found: $exePath"
        return $false
    }
    
    Write-Success "Installation verified"
    Write-Info "Version: $($appInfo.Version)"
    Write-Info "Location: $($appInfo.InstallLocation)"
    
    # Check if added to PATH
    $pathEnv = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($pathEnv -like "*$($appInfo.InstallLocation)*") {
        Write-Success "Application is in system PATH"
    }
    
    return $true
}

# Create desktop shortcut
function New-DesktopShortcut {
    $appInfo = Test-AppInstalled
    if ($appInfo.Installed) {
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "$AppName.lnk"
        
        if (-not (Test-Path $shortcutPath)) {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = Join-Path $appInfo.InstallLocation $AppExecutable
            $shortcut.WorkingDirectory = $appInfo.InstallLocation
            $shortcut.Description = "Web Scraping Automation Tool"
            $shortcut.Save()
            
            Write-Success "Desktop shortcut created"
        }
    }
}

# Main deployment process
function Start-Deployment {
    Write-Host @"
╔════════════════════════════════════════════════════════╗
║        Auto Scrape Deployment Script v1.0             ║
╚════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta
    
    # Check for admin privileges
    Request-AdminPrivileges
    
    try {
        if ($Uninstall) {
            # Uninstall mode
            Uninstall-App
        } else {
            # Install mode
            Write-Step "Starting deployment..."
            
            # Get installer
            $installer = Get-Installer -Path $InstallerPath
            
            # Install application
            $installed = Install-App -InstallerFile $installer -TargetDir $InstallDir
            
            if ($installed) {
                # Configure application
                if ($ConfigFile) {
                    Set-AppConfiguration -ConfigPath $ConfigFile
                }
                
                # Create scheduled task
                if ($CreateScheduledTask) {
                    New-AppScheduledTask
                }
                
                # Create desktop shortcut
                New-DesktopShortcut
                
                # Verify installation
                if (Test-Installation) {
                    Write-Host "`n" -NoNewline
                    Write-Success "Deployment completed successfully!"
                    
                    if (-not $Silent) {
                        $response = Read-Host "`nDo you want to run the application now? (Y/N)"
                        if ($response -eq 'Y') {
                            $appInfo = Test-AppInstalled
                            $exePath = Join-Path $appInfo.InstallLocation $AppExecutable
                            Start-Process -FilePath $exePath
                            Write-Success "Application started"
                        }
                    }
                }
            }
            
            # Cleanup temporary files
            if ($installer -like "$env:TEMP\*") {
                Remove-Item -Path $installer -Force -ErrorAction SilentlyContinue
            }
        }
        
    } catch {
        Write-Error "Deployment failed: $_"
        exit 1
    }
}

# Run deployment
Start-Deployment
