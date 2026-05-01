@echo off
REM GYM AI - Fitness Trainer Launcher
REM This script activates the virtual environment and runs the GUI application

echo.
echo ========================================
echo   GYM AI - Fitness Trainer Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if Main.py exists
if not exist "Main.py" (
    echo [ERROR] Main.py not found!
    pause
    exit /b 1
)

echo [INFO] Starting GYM AI...
echo.

REM Run the application
python Main.py

REM If the user closes the window, show a message
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code: %errorlevel%
)

echo.
echo Application closed.
pause
