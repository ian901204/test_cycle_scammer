"""
Build script for creating Windows executable
Run this script on Windows or use PyInstaller directly
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    packages = [
        'pyinstaller',
        'pywebview',
        'matplotlib',
        'numpy'
    ]
    
    for package in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    print("All packages installed successfully!")

def build_exe():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=TestCycleAnalyzer',
        '--onefile',  # Single executable file
        '--windowed',  # No console window
        '--icon=NONE',  # You can add an icon file later
        '--add-data=templates:templates',  # Not needed for app.py but keeping for compatibility
        '--hidden-import=matplotlib',
        '--hidden-import=numpy',
        '--hidden-import=webview',
        '--hidden-import=PIL._tkinter_finder',
        '--collect-all=matplotlib',
        'app.py'
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ Build completed successfully!")
        print("📦 Executable location: dist/TestCycleAnalyzer.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 60)
    print("Test Cycle Analyzer - Windows Build Script")
    print("=" * 60)
    
    # Check if running on Windows
    if sys.platform != 'win32':
        print("\n⚠️  Warning: This script should be run on Windows")
        print("However, you can still build for Windows from other platforms")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Install requirements
    install_requirements()
    
    # Build executable
    build_exe()
    
    print("\n" + "=" * 60)
    print("Build process completed!")
    print("=" * 60)
