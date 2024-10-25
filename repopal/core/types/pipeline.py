from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any
import uuid

class PipelineState(Enum):
    """Pipeline processing states"""
    RECEIVED = "received"
    PROCESSING = "processing" 
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    PROCESSING_RESULTS = "processing_results"
    COMPLETED = "completed"
    FAILED = "failed"
    CLEANED = "cleaned"
    EXPIRED = "expired"

    def can_transition_to(self, new_state: 'PipelineState') -> bool:
        """Check if transition to new state is valid"""
        valid_transitions = {
            PipelineState.RECEIVED: {PipelineState.PROCESSING, PipelineState.FAILED},
            PipelineState.PROCESSING: {PipelineState.DISPATCHING, PipelineState.FAILED},
            PipelineState.DISPATCHING: {PipelineState.EXECUTING, PipelineState.FAILED},
            PipelineState.EXECUTING: {PipelineState.PROCESSING_RESULTS, PipelineState.FAILED},
            PipelineState.PROCESSING_RESULTS: {PipelineState.COMPLETED, PipelineState.FAILED},
            PipelineState.COMPLETED: {PipelineState.CLEANED},
            PipelineState.FAILED: {PipelineState.CLEANED},
            PipelineState.CLEANED: {PipelineState.EXPIRED},
            PipelineState.EXPIRED: set()
        }
        return new_state in valid_transitions.get(self, set())

@dataclass
class Pipeline:
    """Represents a processing pipeline instance"""
    pipeline_id: str
    current_state: PipelineState
    current_task_id: Optional[str]
    service: str
    repository: str
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    @classmethod
    def create(cls, service: str, repository: str) -> "Pipeline":
        """Create a new pipeline instance"""
        now = datetime.utcnow()
        return cls(
            pipeline_id=str(uuid.uuid4()),
            current_state=PipelineState.RECEIVED,
            current_task_id=None,
            service=service,
            repository=repository,
            created_at=now,
            updated_at=now,
            metadata={}
        )
