"""Celery tasks for core pipeline operations"""

from datetime import datetime
from celery import shared_task
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from repopal.core.pipeline import PipelineStateManager, redis_client
from repopal.core.types.events import StandardizedEvent
from repopal.core.service_manager import ServiceConnectionManager
from repopal.core.types.pipeline import PipelineState
from repopal.core.exceptions import PipelineStateError
from repopal.utils.crypto import CredentialEncryption
from repopal.extensions import db, credential_encryption

from repopal.core.pipeline import PipelineStateManager
from repopal.core.service_manager import ServiceConnectionManager
from repopal.core.types.pipeline import PipelineState

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,  # 30 seconds
    autoretry_for=(Exception,),
    name="core.process_webhook_event"
)
def process_webhook_event(
    self,
    event: StandardizedEvent
) -> Dict[str, Any]:
    """Process a webhook event and initialize pipeline"""
    state_manager = PipelineStateManager(redis_client)
    try:
        # Create new pipeline for event
        pipeline = state_manager.create_pipeline(event)

        # Update state to processing
        state_manager.update_pipeline_state(
            pipeline_id=pipeline.pipeline_id,
            new_state=PipelineState.PROCESSING,
            task_id=self.request.id,
            metadata={
                'event_id': event.event_id,
                'event_type': event.event_type,
                'repository': f"{event.repository.owner}/{event.repository.name}"
            }
        )

        return {
            "status": "success",
            "pipeline_id": pipeline.pipeline_id,
            "event_id": event.event_id,
            "event_type": event.event_type
        }
    except Exception as e:
        self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    name="core.cleanup_expired_pipelines"
)
def cleanup_expired_pipelines(self) -> Dict[str, Any]:
    """Periodic task to clean up expired pipelines"""
    state_manager = PipelineStateManager(redis_client)
    try:
        expired_ids = state_manager.cleanup_expired_pipelines()
        return {
            "status": "success",
            "expired_count": len(expired_ids),
            "expired_ids": expired_ids
        }
    except Exception as e:
        self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    name="core.check_connection_health"
)
def check_connection_health(
    self,
    connection_id: str
) -> Dict[str, Any]:
    """Check health of a service connection"""
    service_manager = ServiceConnectionManager(db.session, credential_encryption)
    try:
        result = service_manager.check_connection_health(connection_id)
        return {
            "status": "success",
            "connection_id": connection_id,
            "health_status": result.status.value,
            "details": result.details
        }
    except Exception as e:
        self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,  # 30 seconds
    autoretry_for=(PipelineStateError,),
    name="core.update_pipeline_state"
)
def update_pipeline_state(
    self,
    pipeline_id: str,
    new_state: str,
    task_id: str = None,
    error: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Update pipeline state with retries"""
    state_manager = PipelineStateManager(redis_client)
    try:
        pipeline = state_manager.update_pipeline_state(
            pipeline_id=pipeline_id,
            new_state=PipelineState(new_state),
            task_id=task_id,
            error=error,
            metadata=metadata
        )
        return {
            "status": "success",
            "pipeline_id": pipeline_id,
            "new_state": new_state,
            "task_id": task_id
        }
    except Exception as e:
        self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    name="core.collect_pipeline_metrics"
)
def collect_pipeline_metrics(self) -> Dict[str, Any]:
    """Collect metrics about pipeline states"""
    state_manager = PipelineStateManager(redis_client)
    try:
        metrics = state_manager.get_pipeline_metrics()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        self.retry(exc=e)
