"""Webhook routes for RepoPal"""

from flask import jsonify, request, current_app
from typing import Dict, Any

from .. import api
from ..webhooks import WebhookHandlerFactory, GitHubWebhookHandler, SlackWebhookHandler
from ..exceptions import WebhookError, RateLimitError
from repopal.core.tasks import process_webhook_event

# Register webhook handlers
WebhookHandlerFactory.register('github', GitHubWebhookHandler)
WebhookHandlerFactory.register('slack', SlackWebhookHandler)

@api.route('/webhooks/<service>', methods=['POST'])
def webhook(service: str) -> Dict[str, Any]:
    """Generic webhook handler for all services"""
    try:
        # Check rate limits
        if not current_app.limiter.check():
            raise RateLimitError("Rate limit exceeded")
            
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
        
        # Queue for processing
        process_webhook_event.delay(event=event)
        
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
        current_app.logger.error(
            "Webhook processing failed",
            extra={'error': str(e)}
        )
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
