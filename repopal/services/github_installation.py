"""GitHub installation service"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from repopal.models.service_connection import (
    ServiceConnection,
    ServiceType,
    ConnectionStatus
)

def handle_installation_event(db: Session, payload: Dict[str, Any]) -> Optional[ServiceConnection]:
    """Handle GitHub App installation event"""
    from flask import current_app
    
    # Extract installation data
    installation = payload.get('installation', {})
    installation_id = installation.get('id')
    account = installation.get('account', {})
    action = payload.get('action')
    repositories = payload.get('repositories', [])
    
    current_app.logger.info(
        "Handling installation event",
        extra={
            'installation_id': installation_id,
            'account': account,
            'action': action,
            'repository_count': len(repositories),
            'repository_names': [repo.get('full_name') for repo in repositories],
            'permissions': installation.get('permissions'),
            'events': installation.get('events')
        }
    )
    
    if not installation_id:
        current_app.logger.error("No installation ID in payload")
        return None
        
    try:
        # Create service connection
        connection = ServiceConnection(
            organization_id=None,  # TODO: Link to org once we have org management
            service_type=ServiceType.GITHUB_APP,
            status=ConnectionStatus.ACTIVE,
            settings={
                'installation_id': installation_id,
                'account_id': account.get('id'),
                'account_login': account.get('login'),
                'account_type': account.get('type'),
                'repository_selection': installation.get('repository_selection'),
                'app_id': payload.get('app_id')
            }
        )
        
        current_app.logger.info(
            "Creating service connection",
            extra={
                'installation_id': installation_id,
                'account_login': account.get('login'),
                'service_type': ServiceType.GITHUB_APP.value
            }
        )
        
        db.add(connection)
        db.commit()
        
        current_app.logger.info(
            "Service connection created successfully",
            extra={'connection_id': str(connection.id)}
        )
        
    except Exception as e:
        current_app.logger.error(
            "Failed to create service connection",
            extra={
                'error': str(e),
                'installation_id': installation_id,
                'account_login': account.get('login')
            }
        )
        db.rollback()
        raise
    
    return connection
