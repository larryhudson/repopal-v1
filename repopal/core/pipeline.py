"""Pipeline state management for RepoPal"""

from typing import Optional, Dict, Any
from datetime import datetime

from redis import Redis
import json

from repopal.core.types.pipeline import Pipeline, PipelineState
from repopal.core.exceptions import PipelineNotFoundError

class PipelineStateManager:
    """Manages pipeline state persistence and transitions"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.key_prefix = "pipeline:"

    def _get_key(self, pipeline_id: str) -> str:
        """Get Redis key for pipeline"""
        return f"{self.key_prefix}{pipeline_id}"

    async def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Retrieve pipeline state from Redis"""
        data = await self.redis.get(self._get_key(pipeline_id))
        if not data:
            return None
            
        pipeline_dict = json.loads(data)
        return Pipeline(
            pipeline_id=pipeline_dict["pipeline_id"],
            current_state=PipelineState(pipeline_dict["current_state"]),
            current_task_id=pipeline_dict["current_task_id"],
            service=pipeline_dict["service"],
            repository=pipeline_dict["repository"],
            created_at=datetime.fromisoformat(pipeline_dict["created_at"]),
            updated_at=datetime.fromisoformat(pipeline_dict["updated_at"]),
            error=pipeline_dict.get("error"),
            metadata=pipeline_dict.get("metadata", {})
        )

    async def save_pipeline(self, pipeline: Pipeline) -> None:
        """Save pipeline state to Redis"""
        pipeline_dict = {
            "pipeline_id": pipeline.pipeline_id,
            "current_state": pipeline.current_state.value,
            "current_task_id": pipeline.current_task_id,
            "service": pipeline.service,
            "repository": pipeline.repository,
            "created_at": pipeline.created_at.isoformat(),
            "updated_at": pipeline.updated_at.isoformat(),
            "error": pipeline.error,
            "metadata": pipeline.metadata or {}
        }
        await self.redis.set(
            self._get_key(pipeline.pipeline_id),
            json.dumps(pipeline_dict)
        )

    async def update_pipeline_state(
        self,
        pipeline_id: str,
        new_state: PipelineState,
        task_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Pipeline:
        """Update pipeline state with new information"""
        pipeline = await self.get_pipeline(pipeline_id)
        if not pipeline:
            raise PipelineNotFoundError(pipeline_id)
        
        pipeline.current_state = new_state
        pipeline.current_task_id = task_id
        pipeline.updated_at = datetime.utcnow()
        
        if error:
            pipeline.error = error
        if metadata:
            pipeline.metadata.update(metadata)
        
        await self.save_pipeline(pipeline)
        return pipeline
