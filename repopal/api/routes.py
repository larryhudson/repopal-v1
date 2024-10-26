"""Main API routes for RepoPal"""

from . import api

# Import route modules to register their endpoints
from .routes import webhooks, auth, core
