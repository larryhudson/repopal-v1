"""Service connection health checking"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"

class HealthCheckResult:
    """Result of a health check"""
    def __init__(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        last_check: Optional[datetime] = None
    ):
        self.status = status
        self.message = message
        self.details = details or {}
        self.last_check = last_check or datetime.utcnow()

class ServiceHealthCheck(ABC):
    """Base class for service-specific health checks"""
    
    @abstractmethod
    async def check_health(self, connection_id: str) -> HealthCheckResult:
        """Run health check for a service connection"""
        pass

class GitHubHealthCheck(ServiceHealthCheck):
    """Health check for GitHub App connections"""
    
    async def check_health(self, connection_id: str) -> HealthCheckResult:
        # TODO: Implement GitHub-specific checks:
        # - Validate installation access
        # - Check rate limits
        # - Verify webhook configuration
        pass

class SlackHealthCheck(ServiceHealthCheck):
    """Health check for Slack workspace connections"""
    
    async def check_health(self, connection_id: str) -> HealthCheckResult:
        # TODO: Implement Slack-specific checks:
        # - Verify bot token validity
        # - Check required scopes
        # - Test basic API operations
        pass

class HealthCheckFactory:
    """Creates appropriate health checker for service type"""
    
    _checkers = {
        "github_app": GitHubHealthCheck,
        "slack": SlackHealthCheck
    }
    
    @classmethod
    def get_checker(cls, service_type: str) -> ServiceHealthCheck:
        """Get health checker for service type"""
        checker_class = cls._checkers.get(service_type)
        if not checker_class:
            raise ValueError(f"No health checker for service type: {service_type}")
        return checker_class()
