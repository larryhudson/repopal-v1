"""Organization and membership models"""

from datetime import datetime
import uuid
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import JSON

from repopal.models.base import Base

class OrganizationRole(str, Enum):
    """Organization member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class Organization(Base):
    """Organization model for team management"""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    github_org_id = Column(String, unique=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization")
    service_connections = relationship("ServiceConnection", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"

class OrganizationMember(Base):
    """Organization membership model"""
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(OrganizationRole), nullable=False, default=OrganizationRole.MEMBER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")

    def __repr__(self):
        return f"<OrganizationMember {self.user_id} {self.organization_id} {self.role}>"
