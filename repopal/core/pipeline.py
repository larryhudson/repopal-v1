"""Pipeline state management for RepoPal"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from redis import Redis, from_url
import json
from prometheus_client import Counter, Histogram

from repopal.core.exceptions import PipelineStateError

from repopal.core.types.pipeline import Pipeline, PipelineState
from repopal.core.exceptions import PipelineNotFoundError

# Redis client singleton
redis_client = from_url("redis://localhost:6379/0")  # TODO: Get from config

# Metrics
PIPELINE_TRANSITIONS = Counter(
    'pipeline_state_transitions_total',
    'Total number of pipeline state transitions',
    ['from_state', 'to_state']
)

PIPELINE_DURATION = Histogram(
    'pipeline_duration_seconds',
    'Time taken for pipeline execution',
    ['final_state']
)

class PipelineStateManager:
    """Manages pipeline state persistence and transitions"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.key_prefix = "pipeline:"
        self.ttl = timedelta(days=7)  # Default TTL for completed pipelines

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

        # Validate state transition
        if not pipeline.current_state.can_transition_to(new_state):
            raise PipelineStateError(
                f"Invalid state transition from {pipeline.current_state} to {new_state}"
            )
        
        # Record metrics
        PIPELINE_TRANSITIONS.labels(
            from_state=pipeline.current_state.value,
            to_state=new_state.value
        ).inc()
        
        # Update pipeline
        old_state = pipeline.current_state
        pipeline.current_state = new_state
        pipeline.current_task_id = task_id
        pipeline.updated_at = datetime.utcnow()
        
        if error:
            pipeline.error = error
        if metadata:
            pipeline.metadata.update(metadata)
        
        # Record duration for terminal states
        if new_state in {PipelineState.COMPLETED, PipelineState.FAILED}:
            duration = (pipeline.updated_at - pipeline.created_at).total_seconds()
            PIPELINE_DURATION.labels(final_state=new_state.value).observe(duration)
        
        # Set TTL for completed/failed pipelines
        if new_state in {PipelineState.COMPLETED, PipelineState.FAILED}:
            await self.redis.expire(
                self._get_key(pipeline_id),
                int(self.ttl.total_seconds())
            )
        
        await self.save_pipeline(pipeline)
        return pipeline
    async def cleanup_expired_pipelines(self) -> List[str]:
        """Clean up expired pipeline data"""
        pattern = f"{self.key_prefix}*"
        expired_ids = []
        
        # Scan for expired pipelines
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            for key in keys:
                pipeline_id = key.replace(self.key_prefix, "")
                pipeline = await self.get_pipeline(pipeline_id)
                
                if pipeline and pipeline.current_state in {
                    PipelineState.COMPLETED,
                    PipelineState.FAILED
                }:
                    # Check if TTL has expired
                    ttl = await self.redis.ttl(key)
                    if ttl <= 0:
                        await self.update_pipeline_state(
                            pipeline_id,
                            PipelineState.EXPIRED
                        )
                        await self.redis.delete(key)
                        expired_ids.append(pipeline_id)
            
            if cursor == 0:
                break
                
        return expired_ids

    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get metrics about pipeline states"""
        metrics = {state.value: 0 for state in PipelineState}
        pattern = f"{self.key_prefix}*"
        
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            for key in keys:
                pipeline = await self.get_pipeline(
                    key.replace(self.key_prefix, "")
                )
                if pipeline:
                    metrics[pipeline.current_state.value] += 1
            
            if cursor == 0:
                break
                
        return metrics
