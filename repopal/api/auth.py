"""Authentication endpoints for RepoPal"""

from flask import jsonify, request, current_app, url_for
from typing import Dict, Any
import requests

from . import api

@api.route('/auth/github', methods=['GET'])
def github_login():
    """Initiate GitHub OAuth flow"""
    github_url = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": current_app.config["GITHUB_CLIENT_ID"],
        "redirect_uri": url_for('api.github_callback', _external=True),
        "scope": "repo user"
    }
    return jsonify({
        "auth_url": f"{github_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}"
    })

@api.route('/auth/github/callback', methods=['GET'])
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400

    # Exchange code for access token
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": current_app.config["GITHUB_CLIENT_ID"],
            "client_secret": current_app.config["GITHUB_CLIENT_SECRET"],
            "code": code
        }
    )
    
    return jsonify(response.json())
