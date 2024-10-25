"""Webhook handlers for service events"""

from flask import request, jsonify
from typing import Dict, Any
import hmac
import hashlib

from . import api
from repopal.core.tasks import process_webhook_event

@api.route('/webhooks/github', methods=['POST'])
def github_webhook() -> Dict[str, Any]:
    """Handle GitHub webhook events"""
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        return jsonify({"error": "No signature provided"}), 400

    # Verify webhook payload
    secret = request.app.config['GITHUB_WEBHOOK_SECRET'].encode()
    expected_signature = 'sha256=' + hmac.new(
        secret,
        request.data,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Process event asynchronously
    event_type = request.headers.get('X-GitHub-Event', 'ping')
    process_webhook_event.delay(
        source="github",
        event_type=event_type,
        payload=request.json
    )

    return jsonify({
        "status": "accepted",
        "event": event_type
    })
