"""Entry point for python -m telos"""
from telos.api.app import app
import uvicorn
import os

if __name__ == "__main__":
    # Port must be set via environment variable
    port = int(os.environ.get("TELOS_PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)