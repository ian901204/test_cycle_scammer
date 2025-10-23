@echo off
echo ================================================
echo Test Cycle Analyzer - Windows Build Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Installing required packages...
pip install pyinstaller pywebview matplotlib numpy

echo.
echo Building executable...
pyinstaller TestCycleAnalyzer.spec

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo Build completed successfully!
    echo Executable location: dist\TestCycleAnalyzer.exe
    echo ================================================
) else (
    echo.
    echo ================================================
    echo Build failed! Please check the error messages above.
    echo ================================================
)

echo.
pause
