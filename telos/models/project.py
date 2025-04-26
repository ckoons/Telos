"""
Project data models for Telos requirements management.

This module provides Pydantic models for project data.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ProjectBase(BaseModel):
    """Base model for project data."""
    name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    """Model for project creation."""
    pass

class ProjectUpdate(BaseModel):
    """Model for project updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RequirementSummary(BaseModel):
    """Model for requirement summary in project context."""
    requirement_id: str
    title: str
    status: str
    priority: str
    requirement_type: str

class ProjectHierarchy(BaseModel):
    """Model for project hierarchy data."""
    children: Dict[str, List[str]] = Field(default_factory=dict)

class ProjectModel(ProjectBase):
    """Model for project data."""
    project_id: str
    created_at: float
    updated_at: float
    requirements: Dict[str, RequirementSummary] = Field(default_factory=dict)
    hierarchy: Optional[ProjectHierarchy] = None
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True

class ProjectListItem(BaseModel):
    """Model for project list item."""
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: float
    updated_at: float
    requirement_count: int = 0

class ProjectList(BaseModel):
    """Model for project list."""
    projects: List[ProjectListItem]
    count: int