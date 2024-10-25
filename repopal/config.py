"""Configuration management for RepoPal"""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """Base configuration."""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key-change-me")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///repopal.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG: bool = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG: bool = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING: bool = True
    DATABASE_URL: str = "sqlite:///:memory:"
