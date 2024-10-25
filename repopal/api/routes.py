"""Main API routes for RepoPal"""

from . import api

# Import and register blueprints
from .routes.webhooks import webhooks_bp
from .routes.auth import auth_bp
from .routes.core import core_bp

api.register_blueprint(webhooks_bp)
api.register_blueprint(auth_bp)
api.register_blueprint(core_bp)
