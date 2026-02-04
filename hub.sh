#!/bin/bash
# Hub CLI Wrapper for Linux/macOS
# Standardizes case management without breaking legacy flows.

PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: Python is required to run the Hub CLI."
    exit 1
fi

$PYTHON_CMD hub.py "$@"
