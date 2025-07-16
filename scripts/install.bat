@echo off
REM Universal Text Extractor - Installation Script for Windows

echo 🚀 Universal Text Extractor - Installation Script
echo =================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3.11+ is required but not found in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip not found. Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip found

REM Create virtual environment
echo 🐍 Creating Python virtual environment...
if exist "venv" (
    echo ⚠️  Virtual environment already exists. Removing...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created

REM Activate virtual environment
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo 📦 Installing Python dependencies...
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Python dependencies installed

REM Create necessary directories
echo 📁 Creating application directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo ✅ Directories created

REM Check for Tesseract OCR
echo 🔍 Checking for Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Tesseract OCR not found in PATH
    echo For full OCR functionality, please install Tesseract:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Install and add to PATH
    echo 3. Restart this script
    echo.
    echo You can continue without OCR, but image text extraction will be limited.
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "%CONTINUE%"=="y" (
        echo Installation cancelled
        pause
        exit /b 1
    )
) else (
    echo ✅ Tesseract OCR found
)

REM Run health check
echo 🏥 Running health check...
python health_check.py
if errorlevel 1 (
    echo ⚠️  Health check failed. Check the output above.
) else (
    echo ✅ Health check passed
)

echo.
echo ✅ Installation completed successfully!
echo.
echo 🎉 Universal Text Extractor is ready to use!
echo.
echo To start the application:
echo   1. Open Command Prompt or PowerShell
echo   2. Navigate to this directory
echo   3. Run: venv\Scripts\activate.bat
echo   4. Run: streamlit run app.py --server.port=5000 --server.address=0.0.0.0
echo.
echo Or simply run: start.bat
echo.
echo Access the application at: http://localhost:5000
echo Default login: admin / admin123
echo.
echo ⚠️  Remember to change the default password immediately!
echo.
echo For more information, see:
echo - README.md for comprehensive documentation
echo - QUICK_START.md for quick setup guide
echo - deployment_guide.md for production deployment

pause