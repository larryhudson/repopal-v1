"""Celery tasks for core pipeline operations"""

from datetime import datetime
from celery import shared_task
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from repopal.core.pipeline import PipelineStateManager, redis_client
from repopal.core.service_manager import ServiceConnectionManager
from repopal.core.types.pipeline import PipelineState
from repopal.core.exceptions import PipelineStateError
from repopal.utils.crypto import CredentialEncryption
from repopal.extensions import db_session, credential_encryption

from repopal.core.pipeline import PipelineStateManager
from repopal.core.service_manager import ServiceConnectionManager
from repopal.core.types.pipeline import PipelineState
from repopal.core.exceptions import PipelineStateError

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    name="core.cleanup_expired_pipelines"
)
async def cleanup_expired_pipelines(self) -> Dict[str, Any]:
    """Periodic task to clean up expired pipelines"""
    state_manager = PipelineStateManager(redis_client)
    try:
        expired_ids = await state_manager.cleanup_expired_pipelines()
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
async def check_connection_health(
    self,
    connection_id: str
) -> Dict[str, Any]:
    """Check health of a service connection"""
    service_manager = ServiceConnectionManager(db_session, credential_encryption)
    try:
        result = await service_manager.check_connection_health(connection_id)
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
async def update_pipeline_state(
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
        pipeline = await state_manager.update_pipeline_state(
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
async def collect_pipeline_metrics(self) -> Dict[str, Any]:
    """Collect metrics about pipeline states"""
    state_manager = PipelineStateManager(redis_client)
    try:
        metrics = await state_manager.get_pipeline_metrics()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        self.retry(exc=e)
