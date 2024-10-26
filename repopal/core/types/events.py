"""Standardized event types for RepoPal"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class RepositoryContext:
    """Repository information for the event"""
    name: str
    owner: str
    default_branch: str
    installation_id: int
    can_write: bool

@dataclass
class StandardizedEvent:
    """Unified event format for all services"""
    event_id: str
    service: str
    event_type: str
    repository: RepositoryContext
    user_request: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any]
    raw_headers: Dict[str, str]
    raw_payload: Dict[str, Any]
