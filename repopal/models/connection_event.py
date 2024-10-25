"""Connection event logging model"""

from datetime import datetime
import uuid
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from repopal.models.base import Base

class ConnectionEventType(str, Enum):
    """Types of connection events"""
    CREATED = "created"
    UPDATED = "updated"
    HEALTH_CHECK = "health_check"
    CREDENTIAL_ROTATION = "credential_rotation"
    ERROR = "error"

class ConnectionEvent(Base):
    """Log of connection lifecycle events"""
    __tablename__ = "connection_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_connection_id = Column(UUID(as_uuid=True), ForeignKey("service_connections.id"), nullable=False)
    event_type = Column(SQLEnum(ConnectionEventType), nullable=False)
    details = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    service_connection = relationship("ServiceConnection", back_populates="events")

    def __repr__(self):
        return f"<ConnectionEvent {self.event_type} {self.service_connection_id}>"
