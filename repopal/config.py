"""Configuration management for RepoPal"""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """Base configuration."""
    # Core settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key-change-me")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///repopal.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Authentication
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_APP_ID: str = os.getenv("GITHUB_APP_ID")
    GITHUB_APP_PRIVATE_KEY: str = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "True").lower() == "true"

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
