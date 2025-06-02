"""Main entry point for running Telos API server."""
import uvicorn
import os
from telos.api.app import app

if __name__ == "__main__":
    port = int(os.environ.get("TELOS_PORT", "8008"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )