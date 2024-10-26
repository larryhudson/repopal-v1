"""Webhook routes for RepoPal"""

import time
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from repopal.core.service_manager import ServiceConnectionManager
from repopal.core.tasks import process_webhook_event
from repopal.utils.crypto import CredentialEncryption
from repopal.webhooks.handlers import (
    GitHubWebhookHandler,
    SlackWebhookHandler,
    WebhookHandlerFactory,
)

from ..exceptions import WebhookError


def init_webhook_handlers(app):
    """Initialize webhook handlers"""
    app.logger.info("Starting webhook handler registration")

    # Register GitHub handler
    app.logger.info("Registering GitHub webhook handler")
    WebhookHandlerFactory.register("github", GitHubWebhookHandler)
    app.logger.debug(
        "GitHub handler registered",
        extra={
            "handler_class": GitHubWebhookHandler.__name__,
            "supported_events": list(GitHubWebhookHandler.SUPPORTED_EVENTS),
        },
    )

    # Register Slack handler
    app.logger.info("Registering Slack webhook handler")
    WebhookHandlerFactory.register("slack", SlackWebhookHandler)
    app.logger.debug(
        "Slack handler registered",
        extra={
            "handler_class": SlackWebhookHandler.__name__,
            "supported_events": list(SlackWebhookHandler.SUPPORTED_EVENTS),
        },
    )

    app.logger.info(
        "Webhook handlers registered successfully",
        extra={
            "registered_handlers": list(WebhookHandlerFactory._handlers.keys()),
            "handler_classes": {
                service: handler.__name__
                for service, handler in WebhookHandlerFactory._handlers.items()
            },
        },
    )


import logging

class SafeFormatter(logging.Formatter):
    """Custom formatter that safely handles missing extras"""
    def format(self, record):
        # Get extras if they exist
        extras = getattr(record, 'extra', {})
        # Add formatted extras to the record if present
        if extras:
            record.extras_str = ' - ' + ' - '.join(f'{k}={v}' for k, v in extras.items())
        else:
            record.extras_str = ''
        return super().format(record)

# Configure root logger
logging.basicConfig(level=logging.DEBUG)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",
    default_limits=["1000 per hour"],
    strategy="fixed-window",
)

# Configure webhook logger
logger = logging.getLogger('repopal.webhooks')
logger.setLevel(logging.DEBUG)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create a formatter that safely includes extra fields
formatter = SafeFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s%(extras_str)s'
)

# Add console handler with safe formatter
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Create webhook blueprint with monitoring
webhooks_bp = Blueprint("webhooks", __name__)

# Webhook metrics
webhook_metrics = {"processed": 0, "errors": 0, "processing_time": []}


@webhooks_bp.route("/webhooks/health")
def health():
    """Health check endpoint for webhooks"""
    return jsonify(
        {
            "status": "healthy",
            "metrics": {
                "processed": webhook_metrics["processed"],
                "errors": webhook_metrics["errors"],
                "avg_processing_time": sum(webhook_metrics["processing_time"][-100:])
                / len(webhook_metrics["processing_time"][-100:])
                if webhook_metrics["processing_time"]
                else 0,
            },
        }
    )


@webhooks_bp.route("/webhooks/<service>", methods=["POST"])
@limiter.limit("100/minute")
def webhook(service: str) -> Dict[str, Any]:
    """Generic webhook handler for all services"""
    try:
        # Log detailed incoming webhook information
        current_app.logger.info(
            f"Received {service} webhook",
            extra={
                "service": service,
                "event_type": request.headers.get("X-GitHub-Event", "unknown"),
                "delivery_id": request.headers.get("X-GitHub-Delivery", "unknown"),
                "sender": request.json.get("sender", {}).get("login", "unknown"),
                "repository": request.json.get("repository", {}).get(
                    "full_name", "unknown"
                ),
                "action": request.json.get("action", "unknown"),
                "installation_id": request.json.get("installation", {}).get(
                    "id", "unknown"
                ),
            },
        )

        # Special handling for installation events
        event_type = request.headers.get("X-GitHub-Event")
        if event_type == "installation":
            current_app.logger.info(
                "Processing GitHub App installation event",
                extra={
                    "action": request.json.get("action"),
                    "installation_id": request.json.get("installation", {}).get("id"),
                    "account": request.json.get("installation", {})
                    .get("account", {})
                    .get("login"),
                    "repositories": [
                        repo.get("full_name")
                        for repo in request.json.get("repositories", [])
                    ],
                },
            )

        # Log raw request data for debugging
        current_app.logger.debug(
            "Webhook raw data",
            extra={
                "headers": dict(request.headers),
                "payload": request.json,
                "method": request.method,
                "content_type": request.content_type,
                "content_length": request.content_length,
                "remote_addr": request.remote_addr,
            },
        )

        # Create and validate handler
        current_app.logger.info(
            f"Creating webhook handler for {service}",
            extra={
                "service": service,
                "available_handlers": list(WebhookHandlerFactory._handlers.keys()),
                "event_type": request.headers.get("X-GitHub-Event", "unknown"),
                "content_type": request.content_type,
            },
        )

        # Convert headers while preserving exact header names
        headers = {k: v for k, v in request.headers.items()}
        
        current_app.logger.debug(
            "Processing webhook headers",
            extra={
                'raw_headers': dict(request.headers),
                'processed_headers': headers,
                'github_event': headers.get('X-GitHub-Event'),
                'content_type': headers.get('Content-Type')
            }
        )
        
        handler = WebhookHandlerFactory.create(
            service=service, headers=headers, payload=request.json
        )

        current_app.logger.info(
            "Webhook handler created successfully",
            extra={"handler_class": handler.__class__.__name__, "service": service},
        )

        # Validate webhook
        handler.validate_signature(request.data)
        event_type = handler.validate_event_type()

        current_app.logger.info(
            f"event_type = {event_type}",
        )

        if event_type == "ping":
            return jsonify(
                {"status": "ok", "message": "Webhook configured successfully"}
            )

        # Convert to standardized event
        event = handler.standardize_event()

        # Handle installation events specially
        if event_type == "installation":
            installation_data = request.json.get("installation", {})
            current_app.logger.info(
                "Processing installation event",
                extra={
                    "action": request.json.get("action"),
                    "installation_id": installation_data.get("id"),
                    "account": installation_data.get("account", {}).get("login"),
                    "account_type": installation_data.get("account", {}).get("type"),
                    "repository_selection": installation_data.get(
                        "repository_selection"
                    ),
                    "app_id": request.json.get("app_id"),
                    "permissions": installation_data.get("permissions"),
                    "events": installation_data.get("events"),
                    "repositories_count": len(request.json.get("repositories", [])),
                    "handler_class": handler.__class__.__name__,
                },
            )

            current_app.logger.info("Initializing service manager for installation")
            try:
                # Initialize service connection manager
                current_app.logger.info("Creating encryption instance")
                encryption = CredentialEncryption(current_app.config["SECRET_KEY"])

                current_app.logger.info("Creating service manager instance")
                service_manager = ServiceConnectionManager(
                    current_app.db.session, encryption
                )

                current_app.logger.info("Calling handle_installation_event")
                connection = handler.handle_installation_event(
                    db=current_app.db.session, service_manager=service_manager
                )

                current_app.logger.info(
                    "Installation handler completed",
                    extra={"connection_created": connection is not None},
                )

                current_app.logger.info(
                    "Installation event handled successfully",
                    extra={
                        "connection_id": str(connection.id) if connection else None,
                        "installation_id": request.json.get("installation", {}).get(
                            "id"
                        ),
                        "action": request.json.get("action"),
                    },
                )
            except Exception as e:
                current_app.logger.error(
                    "Failed to handle installation event",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "installation_id": request.json.get("installation", {}).get(
                            "id"
                        ),
                        "action": request.json.get("action"),
                    },
                    exc_info=True,
                )
                raise
            if connection:
                current_app.logger.info(
                    "Created service connection for installation",
                    extra={
                        "connection_id": str(connection.id),
                        "service_type": connection.service_type.value,
                        "status": connection.status.value,
                        "settings": connection.settings,
                    },
                )
            else:
                current_app.logger.warning(
                    "Failed to create service connection for installation",
                    extra={"payload": request.json},
                )

        # Record start time
        start_time = time.time()

        # Queue for processing
        process_webhook_event.delay(event=event)

        # Update metrics
        webhook_metrics["processed"] += 1
        webhook_metrics["processing_time"].append(time.time() - start_time)

        # Trim processing time history
        if len(webhook_metrics["processing_time"]) > 1000:
            webhook_metrics["processing_time"] = webhook_metrics["processing_time"][
                -1000:
            ]

        # Log success
        current_app.logger.info(
            "Webhook processed successfully",
            extra={
                "service": service,
                "event_id": event.event_id,
                "event_type": event_type,
            },
        )

        return jsonify(
            {"status": "accepted", "event_id": event.event_id, "event_type": event_type}
        )

    except WebhookError as e:
        current_app.logger.warning(
            "Webhook error", extra={"error": str(e), "status_code": e.status_code}
        )
        return jsonify({"error": str(e)}), e.status_code

    except Exception as e:
        # Update error metrics
        webhook_metrics["errors"] += 1

        current_app.logger.error(
            "Webhook processing failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "service": service,
                "headers": dict(request.headers),
                "payload": request.json,
                "traceback": current_app.logger.exception(e),
            },
        )
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
