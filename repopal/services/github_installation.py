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
    
    # Extract installation data
    installation = payload.get('installation', {})
    installation_id = installation.get('id')
    account = installation.get('account', {})
    
    if not installation_id:
        return None
        
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
    
    db.add(connection)
    db.commit()
    
    return connection
