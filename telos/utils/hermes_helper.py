"""Helper for Hermes integration.

This module provides helper functions for integrating with Hermes.
"""

import os
import sys
import logging
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

async def register_with_hermes(
    service_id: str,
    name: str,
    capabilities: List[str],
    metadata: Optional[Dict[str, Any]] = None,
    version: str = "0.1.0",
    endpoint: Optional[str] = None
) -> bool:
    """Register a service with the Hermes service registry.
    
    Args:
        service_id: Unique identifier for the service
        name: Human-readable name for the service
        capabilities: List of service capabilities
        metadata: Additional metadata for the service
        version: Service version
        endpoint: Service endpoint URL
        
    Returns:
        Success status
    """
    try:
        # Find the Hermes directory by looking in the parent of the current directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        parent_dir = os.path.dirname(current_dir)
        hermes_dir = os.path.join(parent_dir, "Hermes")
        
        if not os.path.exists(hermes_dir):
            logger.error(f"Hermes directory not found at {hermes_dir}")
            return False
        
        # Add Hermes to path if not already there
        if hermes_dir not in sys.path:
            sys.path.insert(0, hermes_dir)
            logger.debug(f"Added Hermes directory to path: {hermes_dir}")
        
        # Import Hermes service registry
        try:
            from hermes.core.service_discovery import ServiceRegistry
        except ImportError as e:
            logger.error(f"Could not import Hermes ServiceRegistry: {e}")
            logger.error("Make sure Hermes is installed and in your Python path")
            return False
        
        # Create service registry client
        registry = ServiceRegistry()
        await registry.start()
        
        # Register the service
        success = await registry.register(
            service_id=service_id,
            name=name,
            version=version,
            endpoint=endpoint,
            capabilities=capabilities,
            metadata=metadata or {}
        )
        
        if success:
            logger.info(f"Successfully registered {name} with Hermes")
        else:
            logger.warning(f"Failed to register {name} with Hermes")
        
        await registry.stop()
        return success
    
    except Exception as e:
        logger.error(f"Error registering with Hermes: {e}")
        return False
