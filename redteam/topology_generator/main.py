# ============================================================
# Generator Service — FastAPI Main
# ============================================================
import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from uuid import uuid4

# pyrefly: ignore [missing-import]
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# ─── Robust Path Resolution ───────────────────────────────
# Ensures shared 'streaming' and 'configs' are visible in both Docker and IDE
current_dir = os.path.dirname(os.path.abspath(__file__))
redteam_root = os.path.dirname(current_dir)
if redteam_root not in sys.path:
    sys.path.insert(0, redteam_root)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from account_pool import AccountPool
from topology_patterns import FraudPatternGenerator
from schemas import (
    GenerateRequest,
    SimulationConfig,
    SimulationStartResponse,
    SimulationStatus,
    TransactionEvent,
)

# Streaming imports
from streaming.producer import RedTeamProducer
from streaming.topics import Topics

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = structlog.get_logger()

# ─── State ────────────────────────────────────────────────
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
DEFAULT_POOL_SIZE = int(os.getenv("DEFAULT_ACCOUNT_POOL_SIZE", "1000"))

_producer: Optional[RedTeamProducer] = None
_account_pool: Optional[AccountPool] = None
_pattern_gen: Optional[FraudPatternGenerator] = None
_active_simulations: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _producer, _account_pool, _pattern_gen
    log.info("Topology Generator starting...")
    _account_pool = AccountPool(size=DEFAULT_POOL_SIZE)
    _pattern_gen = FraudPatternGenerator(_account_pool)
    _producer = RedTeamProducer(KAFKA_SERVERS)
    log.info("Topology Generator ready", node_pool_size=DEFAULT_POOL_SIZE)
    yield
    if _producer:
        _producer.close()
    log.info("Generator service shut down")


app = FastAPI(
    title="BLING — Topology Generator",
    description="Generates synthetic laundering graph topologies (7 structural patterns) for adversarial robustness testing. Research/Sandbox use only.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routes ───────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "generator",
        "accounts_in_pool": len(_account_pool.accounts) if _account_pool else 0,
        "active_simulations": len(_active_simulations),
        "_simulation": True,
    }


@app.get("/patterns")
async def list_patterns():
    """List all available fraud patterns."""
    patterns = [
        "layering_chain", "round_trip", "mule_network",
        "structuring", "dormant_activation", "velocity_attack", "fan_in_fan_out",
    ]
    return {"patterns": patterns, "count": len(patterns)}


@app.post("/generate", response_model=List[dict])
async def generate_attack(req: GenerateRequest):
    """Generate a single attack scenario (no streaming, returns transactions)."""
    sim_id = req.simulation_id or f"sim_{uuid4().hex[:10]}"
    txns = _pattern_gen.generate(
        attack_type=req.attack_type,
        simulation_id=sim_id,
        depth=req.attack_depth,
        mutation_generation=req.mutation_generation,
    )
    log.info("Attack generated", attack_type=req.attack_type, count=len(txns))
    return txns


@app.post("/simulate", response_model=SimulationStartResponse)
async def start_simulation(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Start a continuous streaming simulation."""
    sim_id = config.simulation_id or f"sim_{uuid4().hex[:10]}"
    _active_simulations[sim_id] = {
        "simulation_id": sim_id,
        "status": "running",
        "transactions_generated": 0,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "attack_type": config.attack_type,
        "config": config.model_dump(),
    }

    background_tasks.add_task(
        _stream_simulation,
        sim_id=sim_id,
        config=config,
    )

    log.info("Simulation started", simulation_id=sim_id, attack_type=config.attack_type)
    return SimulationStartResponse(
        simulation_id=sim_id,
        attack_type=config.attack_type,
        status="started",
        config=config,
        started_at=_active_simulations[sim_id]["started_at"],
    )


@app.get("/simulate/{simulation_id}", response_model=SimulationStatus)
async def get_simulation_status(simulation_id: str):
    sim = _active_simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return SimulationStatus(**{k: v for k, v in sim.items() if k != "config"})


@app.delete("/simulate/{simulation_id}")
async def stop_simulation(simulation_id: str):
    sim = _active_simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    sim["status"] = "stopped"
    log.info("Simulation stopped", simulation_id=simulation_id)
    return {"simulation_id": simulation_id, "status": "stopped"}


@app.get("/simulate")
async def list_simulations():
    return {
        "simulations": list(_active_simulations.values()),
        "count": len(_active_simulations),
    }


# ─── Background streaming task ────────────────────────────

async def _stream_simulation(sim_id: str, config: SimulationConfig):
    """
    Background task: continuously generate and stream transactions.
    Interval = 1/tps seconds between each transaction batch.
    """
    interval = 1.0 / max(config.tps, 0.1)
    iteration = 0
    sim = _active_simulations[sim_id]

    while sim.get("status") == "running":
        try:
            txns = _pattern_gen.generate(
                attack_type=config.attack_type,
                simulation_id=sim_id,
                depth=config.attack_depth,
                mutation_generation=config.mutation_generation,
            )

            for txn in txns:
                _producer.publish(
                    topic=Topics.TRANSACTIONS,
                    payload=txn,
                    key=txn.get("sender_account"),
                )
                sim["transactions_generated"] += 1

            _producer.flush(timeout=2.0)
            iteration += 1

            log.debug(
                "Batch streamed",
                simulation_id=sim_id,
                iteration=iteration,
                batch_size=len(txns),
            )

        except Exception as e:
            log.error("Stream error", simulation_id=sim_id, error=str(e))

        await asyncio.sleep(interval)

    log.info("Simulation loop ended", simulation_id=sim_id)
