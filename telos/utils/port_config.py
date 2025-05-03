"""
Port configuration utilities for Telos component.

This module provides functions to standardize port configuration
according to the Tekton Single Port Architecture pattern.
"""

import os
import logging
import socket
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Standard port assignments based on Tekton Single Port Architecture
PORT_ASSIGNMENTS = {
    "hephaestus": 8080,
    "engram": 8000,
    "hermes": 8001,
    "ergon": 8002,
    "rhetor": 8003,
    "terma": 8004,
    "athena": 8005,
    "prometheus": 8006,
    "harmonia": 8007,
    "telos": 8008,
    "synthesis": 8009,
    "tekton_core": 8010,
    "llm_adapter": 8300,
}

# Environment variable names for each component
ENV_VAR_NAMES = {
    "hephaestus": "HEPHAESTUS_PORT",
    "engram": "ENGRAM_PORT",
    "hermes": "HERMES_PORT",
    "ergon": "ERGON_PORT",
    "rhetor": "RHETOR_PORT",
    "terma": "TERMA_PORT",
    "athena": "ATHENA_PORT",
    "prometheus": "PROMETHEUS_PORT",
    "harmonia": "HARMONIA_PORT",
    "telos": "TELOS_PORT",
    "synthesis": "SYNTHESIS_PORT", 
    "tekton_core": "TEKTON_CORE_PORT",
    "llm_adapter": "LLM_ADAPTER_HTTP_PORT",
}

def get_component_port(component_id: str) -> int:
    """
    Get the port for a specific component based on Tekton port standards.
    
    Args:
        component_id (str): The component identifier (e.g., "telos", "hermes")
        
    Returns:
        int: The port number for the component
    """
    if component_id not in ENV_VAR_NAMES:
        logger.warning(f"Unknown component ID: {component_id}, using default port 8000")
        return 8000
        
    env_var = ENV_VAR_NAMES[component_id]
    default_port = PORT_ASSIGNMENTS[component_id]
    
    try:
        return int(os.environ.get(env_var, default_port))
    except (ValueError, TypeError):
        logger.warning(f"Invalid port value in {env_var}, using default: {default_port}")
        return default_port

def get_telos_port() -> int:
    """
    Get the configured port for the Telos component.
    
    Returns:
        int: The port number for Telos (default 8008)
    """
    return get_component_port("telos")

def get_prometheus_port() -> int:
    """
    Get the configured port for the Prometheus component.
    
    Returns:
        int: The port number for Prometheus (default 8006)
    """
    return get_component_port("prometheus")

def get_hermes_port() -> int:
    """
    Get the configured port for the Hermes component.
    
    Returns:
        int: The port number for Hermes (default 8001)
    """
    return get_component_port("hermes")

def get_component_url(component_id: str, protocol: str = "http", path: str = "") -> str:
    """
    Get the full URL for a component endpoint.
    
    Args:
        component_id (str): The component identifier
        protocol (str): The protocol (http or ws)
        path (str): The path part of the URL (should start with /)
        
    Returns:
        str: The full URL for the component endpoint
    """
    host = os.environ.get(f"{component_id.upper()}_HOST", "localhost")
    port = get_component_port(component_id)
    
    if not path.startswith("/") and path:
        path = f"/{path}"
        
    return f"{protocol}://{host}:{port}{path}"

def get_api_url(component_id: str, path: str = "") -> str:
    """
    Get the API URL for a component.
    
    Args:
        component_id (str): The component identifier
        path (str): The API path (without /api prefix)
        
    Returns:
        str: The full API URL
    """
    api_path = f"/api{path}" if path else "/api"
    return get_component_url(component_id, protocol="http", path=api_path)

def get_ws_url(component_id: str, path: str = "") -> str:
    """
    Get the WebSocket URL for a component.
    
    Args:
        component_id (str): The component identifier
        path (str): The WebSocket path (without /ws prefix)
        
    Returns:
        str: The full WebSocket URL
    """
    ws_path = f"/ws{path}" if path else "/ws"
    return get_component_url(component_id, protocol="ws", path=ws_path)

def get_prometheus_url() -> str:
    """
    Get the URL for the Prometheus API.
    
    Returns:
        str: The Prometheus API URL
    """
    # First check for the specific environment variable
    prometheus_url = os.environ.get("PROMETHEUS_URL", None)
    if prometheus_url:
        return prometheus_url
    
    # Otherwise, build the URL using the standard pattern
    return get_api_url("prometheus")

def get_hermes_url() -> str:
    """
    Get the URL for the Hermes API.
    
    Returns:
        str: The Hermes API URL
    """
    # First check for the specific environment variable
    hermes_url = os.environ.get("HERMES_URL", None)
    if hermes_url:
        return hermes_url
    
    # Otherwise, build the URL using the standard pattern
    return get_api_url("hermes")

def check_port_availability(port: int) -> Tuple[bool, str]:
    """
    Check if a port is available to use.
    
    Args:
        port (int): The port number to check
        
    Returns:
        Tuple[bool, str]: (is_available, message)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            # Port is in use
            return False, f"Port {port} is already in use by another application"
        else:
            # Port is available
            return True, f"Port {port} is available"
    except Exception as e:
        return False, f"Error checking port {port}: {str(e)}"

def verify_component_port(component_id: str) -> Tuple[bool, str]:
    """
    Verify that the component's configured port is available.
    
    Args:
        component_id (str): The component identifier (e.g., "telos", "hermes")
        
    Returns:
        Tuple[bool, str]: (is_available, message)
    """
    port = get_component_port(component_id)
    return check_port_availability(port)