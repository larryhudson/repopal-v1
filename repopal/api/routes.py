"""Main API routes for RepoPal"""

from flask import jsonify, current_app
from typing import Dict, Any

from . import api
from repopal.core.types.pipeline import PipelineState
from repopal.core.pipeline import PipelineStateManager

# Import and register blueprints
from .routes.webhooks import webhooks_bp
from .routes.auth import auth_bp

api.register_blueprint(webhooks_bp)
api.register_blueprint(auth_bp)

@api.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "0.1.0"
    })

@api.route('/pipelines/<pipeline_id>', methods=['GET'])
async def get_pipeline_status(pipeline_id: str) -> Dict[str, Any]:
    """Get current status of a pipeline"""
    state_manager = PipelineStateManager(current_app.redis)
    pipeline = await state_manager.get_pipeline(pipeline_id)
    
    if not pipeline:
        return jsonify({
            "error": "Pipeline not found"
        }), 404
        
    return jsonify({
        "pipeline_id": pipeline_id,
        "state": pipeline.current_state.value,
        "updated_at": pipeline.updated_at.isoformat(),
        "metadata": pipeline.metadata
    })
