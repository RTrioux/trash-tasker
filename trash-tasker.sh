#!/bin/bash

export TRASH_TASKER_ENV="RELEASE"

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to the script directory
pushd "$SCRIPT_DIR" > /dev/null

# Path to the virtual environment
VENV_PATH="$SCRIPT_DIR/venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Path to the Python script
PYTHON_SCRIPT="$SCRIPT_DIR/trash-tasker.py"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    deactivate
    exit 1
fi

# Start the Python script
python "$PYTHON_SCRIPT" send next

# Deactivate the virtual environment after the script ends
deactivate


# Return to the original directory
popd > /dev/null