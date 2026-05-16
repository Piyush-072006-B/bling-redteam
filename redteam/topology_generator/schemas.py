# ============================================================
# Generator Service — Pydantic Schemas
# ============================================================
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class TransactionEvent(BaseModel):
    """Core transaction payload published to transactions.sandbox"""
    transaction_id: str = Field(default_factory=lambda: f"txn_{uuid4().hex[:12]}")
    sender_account: str
    receiver_account: str
    amount: float
    timestamp: str
    device_id: str
    ip_address: str
    geo_location: str
    transaction_type: str
    attack_type: str
    simulation_id: str
    mutation_generation: int = 0
    _simulation: bool = True

    class Config:
        populate_by_name = True


class SimulationConfig(BaseModel):
    """Configuration for a simulation run"""
    attack_type: str = "layering_chain"
    account_pool_size: int = Field(default=200, ge=10, le=10000)
    attack_depth: int = Field(default=6, ge=2, le=20)
    tps: float = Field(default=2.0, ge=0.1, le=100.0)
    mutation_rate: float = Field(default=0.3, ge=0.0, le=1.0)
    duration_seconds: Optional[int] = Field(default=None)
    mutation_generation: int = 0
    simulation_id: Optional[str] = None


class SimulationStartResponse(BaseModel):
    simulation_id: str
    attack_type: str
    status: str = "started"
    config: SimulationConfig
    started_at: str


class SimulationStatus(BaseModel):
    simulation_id: str
    status: str
    transactions_generated: int
    started_at: str
    attack_type: str


class GenerateRequest(BaseModel):
    attack_type: str = "layering_chain"
    account_pool_size: int = 50
    attack_depth: int = 4
    mutation_generation: int = 0
    simulation_id: Optional[str] = None
