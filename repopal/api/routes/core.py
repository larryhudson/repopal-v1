"""Core API routes for RepoPal"""

from flask import Blueprint, jsonify, current_app, render_template, session, request
from typing import Dict, Any
from github import Github

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

@core_bp.route('/install', methods=['GET'])
def install():
    """Render the GitHub app installation page"""
    return render_template('install.html', 
                         username=session['username'],
                         app_id=current_app.config['GITHUB_APP_ID'])

@core_bp.route('/install/callback', methods=['GET'])
def install_callback():
    """Handle the GitHub app installation callback"""
    installation_id = request.args.get('installation_id')
    if not installation_id:
        return jsonify({"error": "No installation ID provided"}), 400

    # Get the user's access token
    access_token = session['access_token']

    # Use the GitHub API client to get the installation details
    g = Github(access_token)
    installation = g.get_installation(int(installation_id))

    # Store the installation details in the database or session
    # For example:
    # installation_repo = InstallationRepository(
    #     user_id=session['user_id'],
    #     installation_id=installation.id,
    #     repository_id=installation.repository.id,
    #     repository_name=installation.repository.name
    # )
    # db.session.add(installation_repo)
    # db.session.commit()

    return jsonify({"message": "GitHub app installed successfully"})

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
