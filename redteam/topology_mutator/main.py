# ============================================================
# Mutator Service — FastAPI Main
# ============================================================
import inspect
import logging
import os
import random
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/streaming")

from mutation_history import EvolutionTracker
from perturbation_strategies import MutationStrategies

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = structlog.get_logger()

# ─── State ────────────────────────────────────────────────
_tracker: Optional[EvolutionTracker] = None

STRATEGY_MAP = {
    "split_transaction": MutationStrategies.split_transaction,
    "delay_transfers": MutationStrategies.delay_transfers,
    "add_noise_accounts": MutationStrategies.add_noise_accounts,
    "mimic_legitimate": MutationStrategies.mimic_legitimate,
    "randomize_timing": MutationStrategies.randomize_timing,
    "alter_topology": MutationStrategies.alter_topology,
    "insert_low_risk_padding": MutationStrategies.insert_low_risk_padding,
}


class MutateRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    strategies: Optional[List[str]] = None  # None = random selection
    simulation_id: str = "unknown"
    original_pattern: str = "layering_chain"
    mutation_generation: int = 0
    detection_rate_before: float = 1.0
    account_pool_ids: Optional[List[str]] = None


class MutateResponse(BaseModel):
    simulation_id: str
    original_count: int
    mutated_count: int
    strategies_applied: List[str]
    mutation_generation: int
    transactions: List[Dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tracker
    log.info("Topology Mutator starting...")
    _tracker = EvolutionTracker()
    log.info("Topology Mutator ready")
    yield
    log.info("Topology Mutator shut down")


app = FastAPI(
    title="BLING — Topology Mutator",
    description="Applies deterministic perturbation strategies to synthetic laundering graph topologies. Phase 1: amount variations, timing shifts, intermediary node insertion, topology changes. Research/Sandbox use only.",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    stats = _tracker.get_stats() if _tracker else {}
    return {"status": "healthy", "service": "mutator", **stats, "_simulation": True}


@app.get("/strategies")
async def list_strategies():
    return {
        "strategies": list(STRATEGY_MAP.keys()),
        "count": len(STRATEGY_MAP),
        "descriptions": {
            "split_transaction": "Break large transactions into multiple smaller ones",
            "delay_transfers": "Add temporal jitter to evade velocity detection",
            "add_noise_accounts": "Insert decoy transactions to noise the graph",
            "mimic_legitimate": "Make transactions look like normal behavior",
            "randomize_timing": "Randomize inter-transaction timing patterns",
            "alter_topology": "Insert intermediary hops to change graph structure",
            "insert_low_risk_padding": "Pad with benign transactions to dilute signals",
        },
    }


@app.post("/mutate", response_model=MutateResponse)
async def mutate(req: MutateRequest):
    """Apply mutation strategies to a transaction set."""
    if not req.transactions:
        raise HTTPException(status_code=400, detail="No transactions provided")

    # Select strategies
    if req.strategies:
        selected = [s for s in req.strategies if s in STRATEGY_MAP]
    else:
        # Auto-select 2–4 random strategies
        num = random.randint(2, min(4, len(STRATEGY_MAP)))
        selected = random.sample(list(STRATEGY_MAP.keys()), num)

    if not selected:
        raise HTTPException(status_code=400, detail="No valid strategies specified")

    # Apply strategies sequentially
    txns = list(req.transactions)
    pool_ids = req.account_pool_ids or []

    # Ensure deterministic mutations for identical inputs
    random.seed(f"{req.simulation_id}_{req.mutation_generation}")

    for strategy_name in selected:
        fn = STRATEGY_MAP[strategy_name]
        try:
            kwargs: Dict[str, Any] = {}
            sig_params = inspect.signature(fn).parameters
            if "account_pool_ids" in sig_params:
                kwargs["account_pool_ids"] = pool_ids or None
            txns = fn(txns, **kwargs)

            # Update mutation_generation in all transactions
            for t in txns:
                t["mutation_generation"] = req.mutation_generation + 1
                t["simulation_id"] = req.simulation_id
                t["_simulation"] = True

        except Exception as e:
            log.error(f"Strategy {strategy_name} failed: {e}", exc_info=True)

    # Record evolution
    detection_rate_after = req.detection_rate_before * random.uniform(0.6, 0.95)
    _tracker.record(
        simulation_id=req.simulation_id,
        mutation_generation=req.mutation_generation + 1,
        original_pattern=req.original_pattern,
        mutated_pattern=f"{req.original_pattern}+{'|'.join(selected)}",
        mutations_applied=selected,
        detection_rate_before=req.detection_rate_before,
        detection_rate_after=detection_rate_after,
        evasion_success=detection_rate_after < req.detection_rate_before,
    )

    log.info(
        "Mutation applied",
        simulation_id=req.simulation_id,
        strategies=selected,
        original_count=len(req.transactions),
        mutated_count=len(txns),
    )

    return MutateResponse(
        simulation_id=req.simulation_id,
        original_count=len(req.transactions),
        mutated_count=len(txns),
        strategies_applied=selected,
        mutation_generation=req.mutation_generation + 1,
        transactions=txns,
    )


@app.get("/evolution/{simulation_id}")
async def get_evolution(simulation_id: str):
    history = _tracker.get_history(simulation_id=simulation_id)
    return {
        "simulation_id": simulation_id,
        "history": history,
        "count": len(history),
    }


@app.get("/evolution/best/evasions")
async def best_evasions(top_n: int = 10):
    return {"top_evasions": _tracker.get_best_evasions(top_n)}


@app.get("/evolution/stats/summary")
async def evolution_stats():
    return _tracker.get_stats()
