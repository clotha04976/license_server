#!/bin/bash

echo "Starting License Server..."

# Define the path to the activation script
VENV_ACTIVATE_SCRIPT="C:/Users/YCL/.virtualenvs/pythonAPI/Scripts/activate"

# Check if the activation script exists
if [ -f "$VENV_ACTIVATE_SCRIPT" ]; then
    echo "Activating virtual environment..."
    # Use 'source' to activate the venv in the current shell
    source "$VENV_ACTIVATE_SCRIPT"
else
    echo "Virtual environment activation script not found at $VENV_ACTIVATE_SCRIPT"
    echo "Please check the path."
    exit 1
fi

echo "Launching Uvicorn..."
# Now that the venv is active, uvicorn should be in the PATH
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --workers 1