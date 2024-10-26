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

# Import routes after blueprint creation to avoid circular imports
from . import routes
