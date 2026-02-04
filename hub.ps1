# Hub CLI Wrapper for Windows (PowerShell)
# Standardizes case management without breaking legacy flows.

$PythonCmd = "python"
if (!(Get-Command $PythonCmd -ErrorAction SilentlyContinue)) {
    $PythonCmd = "python3"
}

if (!(Get-Command $PythonCmd -ErrorAction SilentlyContinue)) {
    Write-Error "Error: Python is required to run the Hub CLI."
    exit 1
}

& $PythonCmd hub.py $args
