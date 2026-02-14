@echo off
setlocal enabledelayedexpansion

echo [1/4] Checking Virtual Environment...
if not exist "venv" (
    echo Creating virtual environment 'venv'...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Venv exists.
)

echo.
echo [2/4] Installing dependencies into venv...

REM --- Bypass SSL issues caused by PostgreSQL OpenSSL ---
.\venv\Scripts\pip install -r requirements.txt ^
    --trusted-host pypi.org ^
    --trusted-host files.pythonhosted.org ^
    --trusted-host pypi.python.org ^
    --disable-pip-version-check ^
    --no-cache-dir

if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [3/4] Initializing Database...
set PYTHONPATH=.
.\venv\Scripts\python scripts\init_db.py

if errorlevel 1 (
    echo Database initialization failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Starting Server...
echo ========================================================
echo API Documentation: http://127.0.0.1:8000/docs
echo ========================================================

.\venv\Scripts\uvicorn app.main:app --reload

endlocal
pause
