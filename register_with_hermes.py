#!/usr/bin/env python3
"""
Register Telos with Hermes Service Registry

This script registers the Telos requirements management component with the Hermes service registry,
allowing other components to discover and use its capabilities.

Usage:
    python register_with_hermes.py [options]

Environment Variables:
    HERMES_PORT: Port of the Hermes API (default: 8001)
    TELOS_PORT: Port of the Telos API (default: 8008)
    STARTUP_INSTRUCTIONS_FILE: Path to JSON file with startup instructions

Options:
    --hermes-url: URL of the Hermes API (overrides HERMES_PORT env var)
    --instructions-file: Path to startup instructions JSON file
    --endpoint: API endpoint for Telos (overrides TELOS_PORT env var)
    --help: Show this help message
"""

import os
import sys
import json
import asyncio
import signal
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("telos.registration")

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# Add parent directories to path
component_dir = str(script_dir)
tekton_dir = os.path.abspath(os.path.join(component_dir, ".."))
tekton_core_dir = os.path.join(tekton_dir, "tekton-core")

# Add to Python path
sys.path.insert(0, component_dir)
sys.path.insert(0, tekton_dir)
sys.path.insert(0, tekton_core_dir)

# Check if we're in a virtual environment
in_venv = sys.prefix != sys.base_prefix
if not in_venv:
    venv_dir = os.path.join(component_dir, "venv")
    if os.path.exists(venv_dir):
        logger.warning(f"Not running in the Telos virtual environment.")
        logger.warning(f"Consider activating it with: source {venv_dir}/bin/activate")
        print(f"Please run this script within the Telos virtual environment:")
        print(f"source {venv_dir}/bin/activate")
        print(f"python {os.path.basename(__file__)}")
        sys.exit(1)

# Import registration utilities
try:
    # Try to import from tekton-core first (preferred)
    from tekton.utils.hermes_registration import (
        HermesRegistrationClient,
        register_component,
        load_startup_instructions
    )
    REGISTRATION_UTILS_AVAILABLE = True
    logger.info("Successfully imported Tekton registration utilities")
except ImportError:
    logger.warning("Could not import Tekton registration utilities.")
    logger.warning("Falling back to Telos's built-in helper.")
    REGISTRATION_UTILS_AVAILABLE = False

# Import Telos-specific modules
try:
    from telos.utils.hermes_helper import register_with_hermes as telos_register
    from telos.core.requirements_manager import RequirementsManager
    logger.info("Successfully imported Telos modules")
except ImportError as e:
    logger.error(f"Error importing Telos modules: {e}")
    logger.error(f"Make sure Telos is properly installed and accessible")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Register Telos with Hermes Service Registry"
    )
    parser.add_argument(
        "--hermes-url",
        help="URL of the Hermes API",
        default=None
    )
    parser.add_argument(
        "--instructions-file",
        help="Path to startup instructions JSON file",
        default=os.environ.get("STARTUP_INSTRUCTIONS_FILE")
    )
    parser.add_argument(
        "--endpoint",
        help="API endpoint for Telos",
        default=None
    )
    
    return parser.parse_args()

async def register_telos_with_hermes(
    hermes_url: Optional[str] = None,
    instructions_file: Optional[str] = None,
    endpoint: Optional[str] = None
) -> bool:
    """
    Register Telos with Hermes service registry.
    
    Args:
        hermes_url: URL of the Hermes API
        instructions_file: Path to JSON file with startup instructions
        endpoint: API endpoint for Telos
        
    Returns:
        True if registration was successful
    """
    # If hermes_url is not provided, construct it from environment variables
    if not hermes_url:
        hermes_port = os.environ.get("HERMES_PORT", "8001")
        hermes_url = f"http://localhost:{hermes_port}/api"
    
    # If endpoint is not provided, construct it from environment variables
    if not endpoint:
        telos_port = os.environ.get("TELOS_PORT", "8008")
        endpoint = f"http://localhost:{telos_port}/api"
    
    # Check for startup instructions file
    if instructions_file and os.path.isfile(instructions_file):
        logger.info(f"Loading startup instructions from {instructions_file}")
        instructions = load_startup_instructions(instructions_file) if REGISTRATION_UTILS_AVAILABLE else {}
    else:
        instructions = {}
    
    # Define component information
    component_id = instructions.get("component_id", "telos.requirements")
    component_name = instructions.get("name", "Telos Requirements Manager")
    component_type = instructions.get("type", "requirements_management")
    component_version = instructions.get("version", "0.1.0")
    
    # Define capabilities specific to Telos
    capabilities = [
        {
            "name": "create_project",
            "description": "Create a new project",
            "parameters": {
                "name": "string",
                "description": "string (optional)",
                "metadata": "object (optional)"
            }
        },
        {
            "name": "create_requirement",
            "description": "Create a new requirement",
            "parameters": {
                "project_id": "string",
                "title": "string",
                "description": "string",
                "priority": "string (optional)",
                "type": "string (optional)",
                "metadata": "object (optional)"
            }
        },
        {
            "name": "get_project",
            "description": "Get project details",
            "parameters": {
                "project_id": "string"
            }
        },
        {
            "name": "get_requirements",
            "description": "Get requirements for a project",
            "parameters": {
                "project_id": "string",
                "filter": "object (optional)"
            }
        },
        {
            "name": "analyze_requirements",
            "description": "Analyze requirements for issues",
            "parameters": {
                "project_id": "string",
                "analysis_type": "string (optional)"
            }
        },
        {
            "name": "refine_requirement",
            "description": "Interactively refine a requirement",
            "parameters": {
                "requirement_id": "string",
                "feedback": "string (optional)"
            }
        }
    ]
    
    # Define capabilities specific to Telos UI
    ui_capabilities = [
        {
            "name": "interactive_refine",
            "description": "Interactive refinement of requirements",
            "parameters": {
                "project_id": "string",
                "requirement_id": "string (optional)"
            }
        },
        {
            "name": "visualize_project",
            "description": "Visualize project requirements",
            "parameters": {
                "project_id": "string",
                "visualization_type": "string (optional)"
            }
        }
    ]
    
    # Define dependencies
    dependencies = instructions.get("dependencies", ["prometheus.planning"])
    
    # Define additional metadata
    metadata = {
        "description": "Requirements management and refinement for Tekton",
        "ui_available": True,
        "cli_available": True,
        "prometheus_integration": True,
        "single_port_architecture": True,
        "port": os.environ.get("TELOS_PORT", "8008")
    }
    if instructions.get("metadata"):
        metadata.update(instructions["metadata"])
    
    try:
        # Use standardized registration utility if available
        if REGISTRATION_UTILS_AVAILABLE:
            # Register Requirements Manager
            logger.info(f"Registering Telos Requirements Manager with Hermes at {hermes_url}")
            req_client = await register_component(
                component_id=component_id,
                component_name=component_name,
                component_type=component_type,
                component_version=component_version,
                capabilities=[cap["name"] for cap in capabilities],
                hermes_url=hermes_url,
                dependencies=dependencies,
                endpoint=endpoint,
                additional_metadata=metadata
            )
            
            # Register UI component
            ui_metadata = {
                "description": "Telos user interface for requirements management",
                "parent_component": component_id,
                "single_port_architecture": True,
                "port": os.environ.get("TELOS_PORT", "8008")
            }
            
            logger.info(f"Registering Telos UI with Hermes at {hermes_url}")
            ui_client = await register_component(
                component_id="telos.ui",
                component_name="Telos UI",
                component_type="user_interface",
                component_version=component_version,
                capabilities=[cap["name"] for cap in ui_capabilities],
                hermes_url=hermes_url,
                dependencies=[component_id],
                endpoint=f"{endpoint}/ui",
                additional_metadata=ui_metadata
            )
            
            if req_client and ui_client:
                logger.info(f"Successfully registered Telos components with Hermes")
                
                # Set up signal handlers
                loop = asyncio.get_event_loop()
                req_client.setup_signal_handlers(loop)
                
                # Keep the registration active until interrupted
                stop_event = asyncio.Event()
                
                def handle_signal(sig):
                    logger.info(f"Received signal {sig.name}, shutting down")
                    asyncio.create_task(shutdown(req_client, ui_client, stop_event))
                
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))
                
                logger.info("Registration active. Press Ctrl+C to unregister and exit...")
                try:
                    await stop_event.wait()
                except Exception as e:
                    logger.error(f"Error during registration: {e}")
                    await shutdown(req_client, ui_client, stop_event)
                
                return True
            else:
                logger.error(f"Failed to register one or more Telos components with Hermes")
                if req_client:
                    await req_client.close()
                if ui_client:
                    await ui_client.close()
                return False
        else:
            # Fall back to Telos's built-in registration helper
            # Register requirements service
            requirements_success = await telos_register(
                service_id=component_id,
                name=component_name,
                capabilities=[cap["name"] for cap in capabilities],
                metadata=metadata,
                version=component_version,
                endpoint=endpoint
            )
            
            # Register UI service
            ui_success = await telos_register(
                service_id="telos.ui",
                name="Telos User Interface",
                capabilities=[cap["name"] for cap in ui_capabilities],
                metadata={
                    "component_type": "user_interface",
                    "description": "User interaction and visualization",
                    "parent_component": component_id,
                    "single_port_architecture": True,
                    "port": os.environ.get("TELOS_PORT", "8008")
                },
                version=component_version,
                endpoint=f"{endpoint}/ui"
            )
            
            # Display results
            if requirements_success and ui_success:
                logger.info("Successfully registered all Telos services with Hermes")
                logger.info("Press Ctrl+C to exit")
                
                # Keep script running until interrupted
                try:
                    # Wait for interrupt
                    while True:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    pass
                except KeyboardInterrupt:
                    pass
                
                return True
            elif requirements_success:
                logger.warning("Successfully registered requirements service, but failed to register UI service")
                return False
            elif ui_success:
                logger.warning("Successfully registered UI service, but failed to register requirements service")
                return False
            else:
                logger.error("Failed to register any Telos services with Hermes")
                return False
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return False

async def shutdown(req_client, ui_client, stop_event):
    """
    Perform graceful shutdown.
    
    Args:
        req_client: HermesRegistrationClient instance for requirements component
        ui_client: HermesRegistrationClient instance for UI component
        stop_event: Asyncio event to signal shutdown
    """
    logger.info("Shutting down Telos components...")
    
    # Unregister from Hermes
    if req_client:
        await req_client.close()
        logger.info("Unregistered requirements component from Hermes")
    
    if ui_client:
        await ui_client.close()
        logger.info("Unregistered UI component from Hermes")
    
    # Signal to stop the main loop
    stop_event.set()
    logger.info("Shutdown complete")

async def main():
    """Main entry point."""
    args = parse_arguments()
    
    logger.info("Registering Telos with Hermes service registry...")
    
    # If hermes-url is not specified, construct it from HERMES_PORT
    hermes_url = args.hermes_url
    if not hermes_url:
        hermes_port = os.environ.get("HERMES_PORT", "8001")
        hermes_url = f"http://localhost:{hermes_port}/api"
    
    # If endpoint is not specified, construct it from TELOS_PORT
    endpoint = args.endpoint
    if not endpoint:
        telos_port = os.environ.get("TELOS_PORT", "8008")
        endpoint = f"http://localhost:{telos_port}/api"
    
    success = await register_telos_with_hermes(
        hermes_url=hermes_url,
        instructions_file=args.instructions_file,
        endpoint=endpoint
    )
    
    if success:
        logger.info("Telos registration process complete")
    else:
        logger.error("Failed to register Telos with Hermes")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())