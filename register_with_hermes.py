#!/usr/bin/env python3
"""Register Telos with Hermes service registry.

This script registers all Telos services with the Hermes service registry.
"""

import os
import sys
import logging
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("telos_registration")

# Add Telos to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Find the parent directory (Tekton root)
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import registration helper
try:
    from telos.utils.hermes_helper import register_with_hermes
except ImportError as e:
    logger.error(f"Could not import registration helper: {e}")
    logger.error("Make sure to run setup.sh first")
    sys.exit(1)

async def register_telos_services():
    """Register all Telos services with Hermes."""
    
    # Register requirements service
    requirements_success = await register_with_hermes(
        service_id="telos-requirements",
        name="Telos Requirements Management",
        capabilities=["requirements_management", "project_management", "goal_tracking"],
        metadata={
            "component_type": "core",
            "description": "User requirements and goals management"
        }
    )
    
    # Register UI service
    ui_success = await register_with_hermes(
        service_id="telos-ui",
        name="Telos User Interface",
        capabilities=["user_interface", "visualization", "interaction"],
        metadata={
            "component_type": "core",
            "description": "User interaction and visualization"
        }
    )
    
    # Display results
    if requirements_success and ui_success:
        logger.info("Successfully registered all Telos services with Hermes")
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

if __name__ == "__main__":
    # Run in the virtual environment if available
    venv_dir = os.path.join(script_dir, "venv")
    if os.path.exists(venv_dir):
        # Activate the virtual environment if not already activated
        if not os.environ.get("VIRTUAL_ENV"):
            print(f"Please run this script within the Telos virtual environment:")
            print(f"source {venv_dir}/bin/activate")
            print(f"python {os.path.basename(__file__)}")
            sys.exit(1)
    
    success = asyncio.run(register_telos_services())
    sys.exit(0 if success else 1)
