#!/usr/bin/env python3
"""
Quick build script for Auto Scrape executable
This creates a standalone Windows executable without requiring Inno Setup
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned {dir_name}")

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], capture_output=True)
    
    # Install project dependencies
    if os.path.exists("requirements.txt"):
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Installed project dependencies")
        else:
            print("⚠ Warning: Some dependencies may not have installed correctly")

def create_resources():
    """Create resource files"""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    # Create placeholder icon if not exists
    icon_path = resources_dir / "app_icon.ico"
    if not icon_path.exists():
        icon_path.write_text("placeholder")
        print("✓ Created placeholder icon")
    
    # Create LICENSE.txt if not exists
    if not Path("LICENSE.txt").exists():
        license_text = """MIT License

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
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT."""
        Path("LICENSE.txt").write_text(license_text)
        print("✓ Created LICENSE file")

def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable with PyInstaller...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AutoScrape",
        "--onefile",  # Create single executable
        "--console",  # Console application
        "--clean",
        "--noconfirm",
        "--add-data", "config;config",
        "--add-data", "templates;templates",
        "--add-data", "README.md;.",
        "--add-data", "LICENSE.txt;.",
        "--hidden-import", "playwright",
        "--hidden-import", "pydantic",
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--hidden-import", "xlsxwriter",
        "--hidden-import", "yaml",
        "--hidden-import", "jinja2",
        "--collect-all", "playwright",
        "main.py"
    ]
    
    # Add icon if exists
    icon_path = Path("resources/app_icon.ico")
    if icon_path.exists() and icon_path.stat().st_size > 20:  # Not placeholder
        cmd.extend(["--icon", str(icon_path)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Executable built successfully!")
        
        # Check output
        exe_path = Path("dist/AutoScrape.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✓ Output: {exe_path}")
            print(f"✓ Size: {size_mb:.2f} MB")
            return True
    else:
        print("✗ Build failed!")
        print("Error output:")
        print(result.stderr)
        return False
    
    return False

def main():
    """Main build process"""
    print("="*60)
    print("     Auto Scrape Quick Build Script")
    print("="*60)
    
    try:
        # Clean previous builds
        clean_build_dirs()
        
        # Install dependencies
        install_dependencies()
        
        # Create resources
        create_resources()
        
        # Build executable
        if build_executable():
            print("\n" + "="*60)
            print("✓ BUILD COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nExecutable location: dist\\AutoScrape.exe")
            print("\nYou can now:")
            print("1. Run the executable: dist\\AutoScrape.exe")
            print("2. Distribute the file to other Windows machines")
            print("3. Upload to GitHub as a release")
            return 0
        else:
            print("\n✗ Build failed. Check the errors above.")
            return 1
            
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
