"""RepoPal API Module

Provides HTTP endpoints for:
- Webhook event reception
- Authentication
- Repository management
- Service integration
"""

from flask import Blueprint

# Create API blueprint
api = Blueprint('api', __name__)

# Import and register blueprints
from .routes.webhooks import webhooks_bp
from .routes.auth import auth_bp
from .routes.core import core_bp

api.register_blueprint(webhooks_bp)
api.register_blueprint(auth_bp)
api.register_blueprint(core_bp)

# Import routes after blueprint creation to avoid circular imports
from . import routes
