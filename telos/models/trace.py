"""
Trace data models for Telos requirements management.

This module provides Pydantic models for requirement tracing.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TraceBase(BaseModel):
    """Base model for trace data."""
    source_id: str
    target_id: str
    trace_type: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TraceCreate(TraceBase):
    """Model for trace creation."""
    pass

class TraceUpdate(BaseModel):
    """Model for trace updates."""
    trace_type: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TraceModel(TraceBase):
    """Model for trace data."""
    trace_id: str
    created_at: float
    updated_at: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class TraceListItem(BaseModel):
    """Model for trace list item."""
    trace_id: str
    source_id: str
    target_id: str
    trace_type: str
    description: Optional[str] = None
    created_at: float

class TraceList(BaseModel):
    """Model for trace list."""
    traces: List[TraceListItem]
    count: int

class TraceQueryResult(BaseModel):
    """Model for trace query result."""
    source: Dict[str, Any]
    target: Dict[str, Any]
    trace: TraceModel