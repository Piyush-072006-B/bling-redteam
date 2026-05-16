import json
from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LifecycleState(str, Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EXPORTING = "EXPORTING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class SandboxStatus(BaseModel):
    state: LifecycleState = LifecycleState.IDLE
    current_attack_type: Optional[str] = None
    simulation_id: Optional[str] = None
    started_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None

class StatusEngine:
    def __init__(self):
        self._status = SandboxStatus()
    
    def get_status(self) -> SandboxStatus:
        return self._status

    def transition(self, new_state: LifecycleState, **kwargs) -> SandboxStatus:
        self._status.state = new_state
        for k, v in kwargs.items():
            if hasattr(self._status, k):
                setattr(self._status, k, v)
        if new_state == LifecycleState.STARTING:
            self._status.started_at = datetime.utcnow()
        return self._status
