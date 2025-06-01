#!/bin/bash
# Telos Requirements System - Launch Script

# Default port (can be overridden by environment variable)
export TELOS_PORT=${TELOS_PORT:-8008}

# Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Add Tekton root to Python path
TEKTON_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$TEKTON_ROOT:$PYTHONPATH"

# Check if port is already in use
if nc -z localhost $TELOS_PORT 2>/dev/null; then
    echo "Telos is already running on port $TELOS_PORT"
    exit 0
fi

echo "Starting Telos on port $TELOS_PORT..."

# Start the Telos service using custom socket server for proper port reuse
python -c "
from shared.utils.socket_server import run_component_server
run_component_server('telos', 'telos.api.app', 8008)
"