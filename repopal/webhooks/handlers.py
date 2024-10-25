"""Webhook handlers for service events"""

from abc import ABC, abstractmethod
from flask import request, jsonify, current_app
from typing import Dict, Any, Optional, Type
import hmac
import hashlib
from datetime import datetime
import json

from repopal.api.exceptions import (
    WebhookError,
    InvalidSignatureError,
    RateLimitError,
    UnsupportedEventError
)
from repopal.core.tasks import process_webhook_event
from repopal.core.types.events import StandardizedEvent, RepositoryContext

class WebhookHandler(ABC):
    """Base class for webhook handlers"""
    
    @abstractmethod
    def validate_signature(self, request_data: bytes) -> None:
        """Validate webhook signature"""
        pass
        
    @abstractmethod
    def validate_event_type(self) -> str:
        """Validate and return event type"""
        pass
        
    @abstractmethod
    def standardize_event(self) -> StandardizedEvent:
        """Convert to standardized event format"""
        pass

class WebhookHandlerFactory:
    """Factory for creating webhook handlers"""
    
    _handlers: Dict[str, Type[WebhookHandler]] = {}
    
    @classmethod
    def register(cls, service: str, handler_class: Type[WebhookHandler]) -> None:
        """Register a handler for a service"""
        cls._handlers[service] = handler_class
    
    @classmethod
    def create(cls, service: str, headers: Dict[str, str], 
               payload: Dict[str, Any]) -> WebhookHandler:
        """Create a handler instance for a service"""
        if service not in cls._handlers:
            raise UnsupportedEventError(f"No handler for service: {service}")
        return cls._handlers[service](headers, payload)

class SlackWebhookHandler(WebhookHandler):
    """Handles Slack webhook events"""
    
    SUPPORTED_EVENTS = {
        'url_verification',
        'event_callback',
    }
    
    def __init__(self, headers: Dict[str, str], payload: Dict[str, Any]):
        self.headers = headers
        self.payload = payload
        
    def validate_signature(self, request_data: bytes) -> None:
        """Validate Slack webhook signature"""
        timestamp = self.headers.get('X-Slack-Request-Timestamp')
        signature = self.headers.get('X-Slack-Signature')
        
        if not timestamp or not signature:
            raise InvalidSignatureError("Missing signature headers")
            
        # Verify timestamp to prevent replay attacks
        msg = f"v0:{timestamp}:{request_data.decode('utf-8')}"
        secret = current_app.config['SLACK_SIGNING_SECRET'].encode()
        
        # Generate expected signature
        expected = 'v0=' + hmac.new(
            secret,
            msg.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected):
            raise InvalidSignatureError("Invalid signature")
            
    def validate_event_type(self) -> str:
        """Validate and return event type"""
        if self.payload.get('type') == 'url_verification':
            return 'url_verification'
            
        event = self.payload.get('event', {})
        event_type = event.get('type')
        
        if not event_type or event_type not in self.SUPPORTED_EVENTS:
            raise UnsupportedEventError(f"Unsupported event type: {event_type}")
            
        return event_type
        
    def standardize_event(self) -> StandardizedEvent:
        """Convert to standardized event format"""
        event = self.payload.get('event', {})
        
        return StandardizedEvent(
            event_id=self.payload['event_id'],
            service='slack',
            event_type=event.get('type', 'url_verification'),
            repository=self._extract_repository_context(),
            user_request=self._extract_user_request(),
            created_at=datetime.fromtimestamp(float(self.headers['X-Slack-Request-Timestamp'])),
            metadata=self._extract_metadata(),
            raw_headers=self.headers,
            raw_payload=self.payload
        )
        
    def _extract_repository_context(self) -> Optional[RepositoryContext]:
        """Extract repository information if present"""
        # Repository info would need to be parsed from the message text
        # or configured per Slack channel
        return None
        
    def _extract_user_request(self) -> Optional[str]:
        """Extract user request from message"""
        event = self.payload.get('event', {})
        return event.get('text')
        
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract relevant metadata"""
        event = self.payload.get('event', {})
        return {
            'team_id': self.payload.get('team_id'),
            'channel': event.get('channel'),
            'user': event.get('user'),
            'event_time': self.payload.get('event_time')
        }

class GitHubWebhookHandler(WebhookHandler):
    """Handles GitHub webhook events"""
    
    SUPPORTED_EVENTS = {
        'issue_comment',
        'pull_request',
        'push',
    }
    
    def __init__(self, headers: Dict[str, str], payload: Dict[str, Any]):
        self.headers = headers
        self.payload = payload
        
    def validate_signature(self, request_data: bytes) -> None:
        """Validate webhook signature"""
        signature = self.headers.get('X-Hub-Signature-256')
        if not signature:
            raise InvalidSignatureError("No signature provided")

        secret = current_app.config['GITHUB_WEBHOOK_SECRET'].encode()
        expected = 'sha256=' + hmac.new(
            secret,
            request_data,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise InvalidSignatureError("Invalid signature")
            
    def validate_event_type(self) -> str:
        """Validate and return event type"""
        event_type = self.headers.get('X-GitHub-Event', 'ping')
        if event_type not in self.SUPPORTED_EVENTS and event_type != 'ping':
            raise UnsupportedEventError(f"Unsupported event type: {event_type}")
        return event_type
        
    def standardize_event(self) -> StandardizedEvent:
        """Convert to standardized event format"""
        return StandardizedEvent(
            event_id=self.headers['X-GitHub-Delivery'],
            service='github',
            event_type=self.headers['X-GitHub-Event'],
            repository=self._extract_repository_context(),
            user_request=self._extract_user_request(),
            created_at=datetime.utcnow(),
            metadata=self._extract_metadata(),
            raw_headers=self.headers,
            raw_payload=self.payload
        )
        
    def _extract_repository_context(self) -> RepositoryContext:
        """Extract repository information"""
        repo = self.payload['repository']
        return RepositoryContext(
            name=repo['name'],
            owner=repo['owner']['login'],
            default_branch=repo['default_branch'],
            installation_id=self.payload.get('installation', {}).get('id'),
            can_write=True  # Determined by installation permissions
        )
        
    def _extract_user_request(self) -> Optional[str]:
        """Extract user request if present"""
        if 'comment' in self.payload:
            return self.payload['comment']['body']
        elif 'pull_request' in self.payload:
            return self.payload['pull_request']['body']
        return None
        
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract relevant metadata"""
        return {
            'sender': self.payload['sender']['login'],
            'action': self.payload.get('action'),
            'event_timestamp': self.payload['repository']['updated_at']
        }
