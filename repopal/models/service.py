from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from repopal.models.base import Base

class ServiceConnection(Base):
    """Service connection model"""
    __tablename__ = 'service_connections'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    service_type = Column(String, nullable=False)  # 'github_app' or 'slack'
    credentials = Column(String)  # Encrypted credentials
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    repositories = relationship("Repository", back_populates="service_connection")

class Repository(Base):
    """Repository model"""
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    service_connection_id = Column(Integer, ForeignKey('service_connections.id'))
    github_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    service_connection = relationship("ServiceConnection", back_populates="repositories")
