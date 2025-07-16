@echo off
REM Universal Text Extractor - Start Script for Windows

echo 🚀 Starting Universal Text Extractor...

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ⚠️  Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

echo 🐍 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if required files exist
if not exist "app.py" (
    echo ❌ app.py not found
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Create data directory if it doesn't exist
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Set default port if not specified
if "%PORT%"=="" set PORT=5000
if "%HOST%"=="" set HOST=0.0.0.0

echo 🌐 Starting application on http://%HOST%:%PORT%
echo 📊 Data directory: %CD%\data
echo 📝 Logs directory: %CD%\logs
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the application
streamlit run app.py --server.port=%PORT% --server.address=%HOST%

pause