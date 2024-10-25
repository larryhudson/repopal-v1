"""Webhook-specific exceptions"""

class WebhookError(Exception):
    """Base class for webhook errors"""
    status_code = 500
    
class InvalidSignatureError(WebhookError):
    """Invalid webhook signature"""
    status_code = 401

class RateLimitError(WebhookError):
    """Rate limit exceeded"""
    status_code = 429

class UnsupportedEventError(WebhookError):
    """Unsupported event type"""
    status_code = 400
