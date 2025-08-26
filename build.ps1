<#
.SYNOPSIS
    Build script for Auto Scrape Windows application
.DESCRIPTION
    This script automates the entire build process:
    - Checks prerequisites
    - Creates virtual environment
    - Installs dependencies
    - Builds executable with PyInstaller
    - Creates installer with Inno Setup
.PARAMETER Clean
    Clean build directories before building
.PARAMETER SkipInstaller
    Skip creating the installer (only build executable)
.PARAMETER Debug
    Build in debug mode with console output
#>

param(
    [switch]$Clean,
    [switch]$SkipInstaller,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Configuration
$ProjectName = "AutoScrape"
$ProjectVersion = "1.0.0"
$PythonVersion = "3.11"
$BuildDir = "build"
$DistDir = "dist"
$ResourcesDir = "resources"
$VenvDir = "venv_build"

# Colors for output
function Write-Step { param($msg) Write-Host "`n===> $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check prerequisites
function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $majorVersion = [int]$matches[1]
            $minorVersion = [int]$matches[2]
            if ($majorVersion -eq 3 -and $minorVersion -ge 11) {
                Write-Success "Python $majorVersion.$minorVersion found"
            } else {
                throw "Python 3.11+ required (found $majorVersion.$minorVersion)"
            }
        }
    } catch {
        Write-Error "Python 3.11+ is not installed or not in PATH"
        exit 1
    }
    
    # Check Inno Setup (optional)
    $innoSetupPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $innoSetupPath)) {
        $innoSetupPath = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    }
    
    if (Test-Path $innoSetupPath) {
        Write-Success "Inno Setup found"
        $script:InnoSetupCompiler = $innoSetupPath
    } else {
        if (-not $SkipInstaller) {
            Write-Warning "Inno Setup not found. Installer will not be created."
            Write-Warning "Download from: https://jrsoftware.org/isdl.php"
            $script:SkipInstaller = $true
        }
    }
}

# Clean build directories
function Clear-BuildDirectories {
    if ($Clean) {
        Write-Step "Cleaning build directories..."
        @($BuildDir, $DistDir, "__pycache__", "*.egg-info", $VenvDir) | ForEach-Object {
            if (Test-Path $_) {
                Remove-Item -Path $_ -Recurse -Force
                Write-Success "Removed $_"
            }
        }
    }
}

# Create virtual environment
function New-BuildEnvironment {
    Write-Step "Creating virtual environment..."
    
    if (-not (Test-Path $VenvDir)) {
        python -m venv $VenvDir
        Write-Success "Virtual environment created"
    } else {
        Write-Success "Virtual environment already exists"
    }
    
    # Activate virtual environment
    $script:ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    if (Test-Path $script:ActivateScript) {
        & $script:ActivateScript
        Write-Success "Virtual environment activated"
    } else {
        Write-Error "Failed to activate virtual environment"
        exit 1
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Step "Installing dependencies..."
    
    # Upgrade pip
    python -m pip install --upgrade pip setuptools wheel | Out-Null
    Write-Success "Updated pip, setuptools, and wheel"
    
    # Install PyInstaller
    pip install pyinstaller | Out-Null
    Write-Success "Installed PyInstaller"
    
    # Install project dependencies
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt | Out-Null
        Write-Success "Installed project dependencies"
    }
    
    # Install Playwright browsers
    Write-Step "Installing Playwright browsers..."
    playwright install chromium | Out-Null
    Write-Success "Installed Chromium browser"
}

# Create resources
function New-Resources {
    Write-Step "Creating resource files..."
    
    if (-not (Test-Path $ResourcesDir)) {
        New-Item -ItemType Directory -Path $ResourcesDir -Force | Out-Null
    }
    
    # Create dummy icon if not exists
    $iconPath = Join-Path $ResourcesDir "app_icon.ico"
    if (-not (Test-Path $iconPath)) {
        Write-Warning "Icon file not found. Creating placeholder..."
        # You can replace this with actual icon generation or download
        "placeholder" | Out-File -FilePath $iconPath
    }
    
    # Create version info file
    $versionFile = Join-Path $BuildDir "file_version_info.txt"
    if (-not (Test-Path $BuildDir)) {
        New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
    }
    
    @"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'Auto Scrape Team'),
           StringStruct(u'FileDescription', u'Auto Scrape - Web Scraping Automation'),
           StringStruct(u'FileVersion', u'1.0.0.0'),
           StringStruct(u'InternalName', u'AutoScrape'),
           StringStruct(u'LegalCopyright', u'Copyright (c) 2024 Auto Scrape Team'),
           StringStruct(u'OriginalFilename', u'AutoScrape.exe'),
           StringStruct(u'ProductName', u'Auto Scrape'),
           StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"@ | Out-File -FilePath $versionFile -Encoding UTF8
    
    Write-Success "Resource files created"
}

# Create LICENSE file if not exists
function New-LicenseFile {
    $licensePath = "LICENSE.txt"
    if (-not (Test-Path $licensePath)) {
        Write-Step "Creating LICENSE file..."
        @"
MIT License

Copyright (c) 2024 Auto Scrape Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@ | Out-File -FilePath $licensePath -Encoding UTF8
        Write-Success "LICENSE file created"
    }
}

# Create dummy file for Inno Setup
function New-DummyFile {
    $dummyPath = Join-Path $BuildDir "dummy.txt"
    if (-not (Test-Path $dummyPath)) {
        "This file is used during installation and will be deleted." | Out-File -FilePath $dummyPath
    }
}

# Build executable with PyInstaller
function Build-Executable {
    Write-Step "Building executable with PyInstaller..."
    
    $specFile = Join-Path $BuildDir "auto_scrape.spec"
    
    if (Test-Path $specFile) {
        # Build using spec file
        $buildCmd = "pyinstaller --clean --noconfirm"
        if (-not $Debug) {
            $buildCmd += " --windowed"
        }
        $buildCmd += " `"$specFile`""
        
        Write-Host "Running: $buildCmd"
        Invoke-Expression $buildCmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Executable built successfully"
        } else {
            Write-Error "Failed to build executable"
            exit 1
        }
    } else {
        Write-Error "Spec file not found: $specFile"
        exit 1
    }
}

# Create installer with Inno Setup
function Build-Installer {
    if ($SkipInstaller) {
        Write-Warning "Skipping installer creation"
        return
    }
    
    Write-Step "Creating installer with Inno Setup..."
    
    $issFile = Join-Path $BuildDir "installer.iss"
    
    if (-not (Test-Path $issFile)) {
        Write-Error "Installer script not found: $issFile"
        return
    }
    
    if ($script:InnoSetupCompiler) {
        & $script:InnoSetupCompiler $issFile /Q
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Installer created successfully"
            $installerPath = Join-Path $DistDir "AutoScrape-Setup-$ProjectVersion.exe"
            if (Test-Path $installerPath) {
                Write-Success "Installer location: $installerPath"
                Write-Success "Size: $([math]::Round((Get-Item $installerPath).Length / 1MB, 2)) MB"
            }
        } else {
            Write-Error "Failed to create installer"
        }
    }
}

# Main build process
function Start-Build {
    Write-Host @"
╔════════════════════════════════════════════════════════╗
║          Auto Scrape Build Script v1.0                ║
║          Building version: $ProjectVersion                     ║
╚════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta
    
    $startTime = Get-Date
    
    try {
        Test-Prerequisites
        Clear-BuildDirectories
        New-BuildEnvironment
        Install-Dependencies
        New-Resources
        New-LicenseFile
        New-DummyFile
        Build-Executable
        Build-Installer
        
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-Host "`n" -NoNewline
        Write-Success "Build completed successfully!"
        Write-Success "Total time: $([math]::Round($duration.TotalSeconds, 2)) seconds"
        
        if (-not $SkipInstaller -and $script:InnoSetupCompiler) {
            Write-Host "`nInstaller is ready for distribution:" -ForegroundColor Green
            Write-Host "  $DistDir\AutoScrape-Setup-$ProjectVersion.exe" -ForegroundColor White
        } else {
            Write-Host "`nExecutable is ready:" -ForegroundColor Green
            Write-Host "  $DistDir\AutoScrape\AutoScrape.exe" -ForegroundColor White
        }
        
    } catch {
        Write-Error "Build failed: $_"
        exit 1
    } finally {
        # Deactivate virtual environment
        if (Get-Command deactivate -ErrorAction SilentlyContinue) {
            deactivate
        }
    }
}

# Run the build
Start-Build
