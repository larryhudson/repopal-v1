"""Core API routes for RepoPal"""

from flask import Blueprint, jsonify, current_app
from typing import Dict, Any

from repopal.core.types.pipeline import PipelineState
from repopal.core.pipeline import PipelineStateManager

# Create core blueprint
core_bp = Blueprint('core', __name__)

@core_bp.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "0.1.0"
    })

@core_bp.route('/pipelines/<pipeline_id>', methods=['GET'])
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
