"""Core API routes for RepoPal"""

from flask import Blueprint, jsonify, current_app, render_template, session, request
from typing import Dict, Any
from github import Github
from sqlalchemy.orm import Session

from repopal.core.types.pipeline import PipelineState
from repopal.core.pipeline import PipelineStateManager
from repopal.api.routes.auth import login_required
from repopal.utils.crypto import CredentialEncryption
from repopal.models.service import ServiceConnection, Repository

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
@login_required
def install():
    """Render the GitHub app installation page"""
    return render_template('install.html', 
                         username=session['username'],
                         app_id=current_app.config['GITHUB_APP_ID'])

@core_bp.route('/install/callback', methods=['GET'])
@login_required
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

    try:
        # Create service connection
        connection = ServiceConnection(
            user_id=session['user_id'],
            service_type='github_app',
            settings={
                'installation_id': installation.id
            }
        )
        
        # Encrypt and store access token
        encryption = CredentialEncryption(current_app.config['MASTER_KEY'])
        connection.credentials = encryption.encrypt(access_token)
        
        # Store connection
        db = current_app.db.session
        db.add(connection)
        
        # Store repository info
        for repo in installation.repositories:
            repository = Repository(
                service_connection_id=connection.id,
                github_id=repo.id,
                name=repo.full_name,
                settings={
                    'default_branch': repo.default_branch,
                    'visibility': repo.visibility
                }
            )
            db.add(repository)
        
        db.commit()
        
        # Log audit event
        current_app.logger.info(
            "GitHub app installed",
            extra={
                'user_id': session['user_id'],
                'installation_id': installation.id,
                'repository_count': len(installation.repositories)
            }
        )

        return jsonify({
            "message": "GitHub app installed successfully",
            "connection_id": connection.id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            "GitHub app installation failed",
            extra={
                'user_id': session['user_id'],
                'error': str(e)
            }
        )
        return jsonify({
            "error": "Failed to install GitHub app",
            "details": str(e)
        }), 500

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
