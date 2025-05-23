#!/bin/bash
# Telos Requirements System - Launch Script

# ANSI color codes for terminal output
BLUE="\033[94m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${BLUE}${BOLD}Starting Telos Requirements System...${RESET}"

# Find Tekton root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ "$SCRIPT_DIR" == *"/utils" ]]; then
    # Script is running from a symlink in utils
    TEKTON_ROOT=$(cd "$SCRIPT_DIR" && cd "$(readlink "${BASH_SOURCE[0]}" | xargs dirname | xargs dirname)" && pwd)
else
    # Script is running from Telos directory
    TEKTON_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

# Ensure we're in the correct directory
cd "$SCRIPT_DIR"

# Set environment variables
export TELOS_PORT=8008
export PYTHONPATH="$SCRIPT_DIR:$TEKTON_ROOT:$PYTHONPATH"

# Create log directories
mkdir -p "$HOME/.tekton/logs"
mkdir -p "$HOME/.tekton/data/telos"

# Error handling function
handle_error() {
    echo -e "${RED}Error: $1${RESET}" >&2
    ${TEKTON_ROOT}/scripts/tekton-register unregister --component telos
    exit 1
}

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Register with Hermes using tekton-register
echo -e "${YELLOW}Registering Telos with Hermes...${RESET}"
${TEKTON_ROOT}/scripts/tekton-register register --component telos --config ${TEKTON_ROOT}/config/components/telos.yaml &
REGISTER_PID=$!

# Give registration a moment to complete
sleep 2

# Start the Telos service
echo -e "${YELLOW}Starting Telos API server...${RESET}"
python -m telos.api.app > "$HOME/.tekton/logs/telos.log" 2>&1 &
TELOS_PID=$!

# Trap signals for graceful shutdown
trap "${TEKTON_ROOT}/scripts/tekton-register unregister --component telos; kill $TELOS_PID 2>/dev/null; exit" EXIT SIGINT SIGTERM

# Wait for the server to start
echo -e "${YELLOW}Waiting for Telos to start...${RESET}"
for i in {1..30}; do
    if curl -s http://localhost:$TELOS_PORT/health >/dev/null; then
        echo -e "${GREEN}Telos started successfully on port $TELOS_PORT${RESET}"
        echo -e "${GREEN}API available at: http://localhost:$TELOS_PORT/api${RESET}"
        break
    fi
    
    # Check if the process is still running
    if ! kill -0 $TELOS_PID 2>/dev/null; then
        echo -e "${RED}Telos process terminated unexpectedly${RESET}"
        cat "$HOME/.tekton/logs/telos.log"
        handle_error "Telos failed to start"
    fi
    
    echo -n "."
    sleep 1
done

# Keep the script running to maintain registration
echo -e "${BLUE}Telos is running. Press Ctrl+C to stop.${RESET}"
wait $TELOS_PID