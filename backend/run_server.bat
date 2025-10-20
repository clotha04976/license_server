@echo off
call C:\Users\YCL\.virtualenvs\license_server\Scripts\activate.bat
cd C:\Users\YCL\SynologyDrive\ducky\license_server\backend
echo Starting License Server...

REM Activate virtual environment if it exists
IF EXIST venv\Scripts\activate (
    echo Activating virtual environment...
    call venv\Scripts\activate
) ELSE (
    echo Virtual environment not found. Running with system Python.
)

echo Launching Uvicorn...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000