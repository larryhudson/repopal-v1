"""Webhook routes for RepoPal"""

import time
from flask import Blueprint, jsonify, request, current_app
from typing import Dict, Any
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from repopal.webhooks.handlers import WebhookHandlerFactory, GitHubWebhookHandler, SlackWebhookHandler
from ..exceptions import WebhookError, RateLimitError
from repopal.core.tasks import process_webhook_event
from repopal.services.github_installation import handle_installation_event

def init_webhook_handlers(app):
    """Initialize webhook handlers"""
    app.logger.info("Registering webhook handlers")
    WebhookHandlerFactory.register('github', GitHubWebhookHandler)
    WebhookHandlerFactory.register('slack', SlackWebhookHandler)
    app.logger.info("Webhook handlers registered successfully", 
        extra={
            'handlers': list(WebhookHandlerFactory._handlers.keys())
        }
    )

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",
    default_limits=["1000 per hour"],
    strategy="fixed-window"
)

# Create webhook blueprint with monitoring
webhooks_bp = Blueprint('webhooks', __name__)

# Webhook metrics
webhook_metrics = {
    'processed': 0,
    'errors': 0,
    'processing_time': []
}

@webhooks_bp.route('/webhooks/health')
def health():
    """Health check endpoint for webhooks"""
    return jsonify({
        'status': 'healthy',
        'metrics': {
            'processed': webhook_metrics['processed'],
            'errors': webhook_metrics['errors'],
            'avg_processing_time': sum(webhook_metrics['processing_time'][-100:]) / len(webhook_metrics['processing_time'][-100:]) if webhook_metrics['processing_time'] else 0
        }
    })

@webhooks_bp.route('/webhooks/<service>', methods=['POST'])
@limiter.limit("100/minute")
def webhook(service: str) -> Dict[str, Any]:
    """Generic webhook handler for all services"""
    try:
        # Log detailed incoming webhook information
        current_app.logger.info(
            f"Received {service} webhook",
            extra={
                'service': service,
                'event_type': request.headers.get('X-GitHub-Event', 'unknown'),
                'delivery_id': request.headers.get('X-GitHub-Delivery', 'unknown'),
                'sender': request.json.get('sender', {}).get('login', 'unknown'),
                'repository': request.json.get('repository', {}).get('full_name', 'unknown'),
                'action': request.json.get('action', 'unknown'),
                'installation_id': request.json.get('installation', {}).get('id', 'unknown')
            }
        )
        
        # Log raw request data for debugging
        current_app.logger.debug(
            "Webhook raw data",
            extra={
                'headers': dict(request.headers),
                'payload': request.json,
                'method': request.method,
                'content_type': request.content_type,
                'content_length': request.content_length,
                'remote_addr': request.remote_addr
            }
        )
            
        # Create and validate handler
        handler = WebhookHandlerFactory.create(
            service=service,
            headers=dict(request.headers),
            payload=request.json
        )
        
        # Validate webhook
        handler.validate_signature(request.data)
        event_type = handler.validate_event_type()
        
        if event_type == 'ping':
            return jsonify({
                "status": "ok",
                "message": "Webhook configured successfully"
            })
            
        # Convert to standardized event
        event = handler.standardize_event()
        
        # Handle installation events specially
        if event_type == 'installation':
            current_app.logger.info(
                "Processing installation event",
                extra={
                    'action': request.json.get('action'),
                    'installation_id': request.json.get('installation', {}).get('id'),
                    'account': request.json.get('installation', {}).get('account', {}).get('login')
                }
            )
            connection = handle_installation_event(
                db=current_app.db.session,
                payload=request.json
            )
            if connection:
                current_app.logger.info(
                    "Created service connection for installation",
                    extra={
                        'connection_id': str(connection.id),
                        'service_type': connection.service_type.value,
                        'status': connection.status.value,
                        'settings': connection.settings
                    }
                )
            else:
                current_app.logger.warning(
                    "Failed to create service connection for installation",
                    extra={'payload': request.json}
                )
        
        # Record start time
        start_time = time.time()
        
        # Queue for processing
        process_webhook_event.delay(event=event)
        
        # Update metrics
        webhook_metrics['processed'] += 1
        webhook_metrics['processing_time'].append(time.time() - start_time)
        
        # Trim processing time history
        if len(webhook_metrics['processing_time']) > 1000:
            webhook_metrics['processing_time'] = webhook_metrics['processing_time'][-1000:]
        
        # Log success
        current_app.logger.info(
            "Webhook processed successfully",
            extra={
                'service': service,
                'event_id': event.event_id,
                'event_type': event_type
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
        # Update error metrics
        webhook_metrics['errors'] += 1
        
        current_app.logger.error(
            "Webhook processing failed",
            extra={
                'error': str(e),
                'error_type': type(e).__name__,
                'service': service,
                'headers': dict(request.headers),
                'payload': request.json,
                'traceback': current_app.logger.exception(e)
            }
        )
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
