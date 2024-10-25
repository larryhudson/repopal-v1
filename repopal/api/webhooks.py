"""Webhook handlers for service events"""

from abc import ABC, abstractmethod
from flask import request, jsonify, current_app
from typing import Dict, Any, Optional, Type
import hmac
import hashlib
from datetime import datetime

from . import api
from .exceptions import (
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

@api.route('/webhooks/github', methods=['POST'])
def github_webhook() -> Dict[str, Any]:
    """Handle GitHub webhook events"""
    try:
        # Check rate limits
        if not current_app.limiter.check():
            raise RateLimitError("Rate limit exceeded")
            
        # Process webhook
        handler = GitHubWebhookHandler(request.headers, request.json)
        handler.validate_signature(request.data)
        event_type = handler.validate_event_type()
        
        if event_type == 'ping':
            return jsonify({"status": "ok", "message": "Webhook configured successfully"})
            
        # Convert to standardized event
        event = handler.standardize_event()
        
        # Queue for processing
        process_webhook_event.delay(event=event)
        
        # Log success
        current_app.logger.info(
            "Webhook processed successfully",
            extra={
                'event_id': event.event_id,
                'event_type': event_type,
                'repository': f"{event.repository.owner}/{event.repository.name}"
            }
        )
        
        return jsonify({
            "status": "accepted",
            "event_id": event.event_id,
            "event_type": event_type
        })
        
    except WebhookError as e:
        current_app.logger.warning(
            "Webhook error",
            extra={
                'error': str(e),
                'status_code': e.status_code
            }
        )
        return jsonify({"error": str(e)}), e.status_code
        
    except Exception as e:
        current_app.logger.error(
            "Webhook processing failed",
            extra={'error': str(e)}
        )
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
