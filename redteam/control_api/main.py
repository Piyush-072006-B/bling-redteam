import asyncio
import logging
import os
import sys
import httpx
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import structlog 
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Robust Path Resolution ───────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
redteam_root = os.path.dirname(current_dir)
if redteam_root not in sys.path:
    sys.path.insert(0, redteam_root)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from streaming.consumer import RedTeamConsumer
from streaming.topics import Topics

from state_cache import GraphStateCache
from sandbox_state import StatusEngine, LifecycleState
from evidence_bundle import EvidenceBundler

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = structlog.get_logger()

# Config
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
GENERATOR_URL = os.getenv("GENERATOR_URL", "http://topology-generator:8001")
MUTATOR_URL = os.getenv("MUTATOR_URL", "http://topology-mutator:8004")

# ─── State ────────────────────────────────────────────────────────────────────
_cache = GraphStateCache()
_status_engine = StatusEngine()
_consumer: Optional[RedTeamConsumer] = None
_active_connections: List[WebSocket] = []

# THE KEY FIX: store the main event loop reference so the Kafka
# background thread can safely schedule coroutines onto it.
_main_loop: Optional[asyncio.AbstractEventLoop] = None


# ─── Connection Manager ───────────────────────────────────────────────────────
class ConnectionManager:
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        _active_connections.append(websocket)
        log.info("WebSocket client connected", total_connections=len(_active_connections))
        # Immediately push full graph state snapshot + status on connect/reconnect
        await websocket.send_json({"type": "FULL_STATE", "data": _cache.get_full_state()})
        await websocket.send_json({"type": "STATUS_UPDATE", "data": _status_engine.get_status().model_dump(mode="json")})

    def disconnect(self, websocket: WebSocket):
        if websocket in _active_connections:
            _active_connections.remove(websocket)
            log.info("WebSocket client disconnected", remaining_connections=len(_active_connections))

    async def broadcast(self, message: dict):
        if not _active_connections:
            return
        log.debug("Broadcasting to WebSocket clients", msg_type=message.get("type"), clients=len(_active_connections))
        dead = []
        for ws in list(_active_connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

manager = ConnectionManager()


def _thread_safe_broadcast(message: dict):
    """
    Schedule a WebSocket broadcast onto the main async event loop
    from a background Kafka consumer thread.
    This is the CORRECT way to bridge sync threads → async coroutines.
    """
    if _main_loop is None:
        return
    asyncio.run_coroutine_threadsafe(manager.broadcast(message), _main_loop)


async def broadcast_status():
    await manager.broadcast({
        "type": "STATUS_UPDATE",
        "data": _status_engine.get_status().model_dump(mode="json")
    })


# ─── Kafka Event Handler ──────────────────────────────────────────────────────
def _on_kafka_event(event: Dict[str, Any]):
    """
    Handle incoming Kafka events from the background consumer thread.
    Updates the state cache, then bridges to the async event loop
    for WebSocket broadcasting using run_coroutine_threadsafe.
    """
    event_type = event.get("event_type", "")

    log.debug("Kafka event received", event_type=event_type)

    if event_type == "edge_added":
        node_from = event.get("node_from", "")
        node_to = event.get("node_to", "")
        attack_type = event.get("attack_type")

        node_color = "suspicious" if attack_type else "normal"
        _cache.update_node(node_from, {"id": node_from, "type": node_color})
        _cache.update_node(node_to,   {"id": node_to,   "type": node_color})

        link_id = f"{node_from}_{node_to}_{event.get('transaction_id', '')}"
        _cache.update_link(link_id, {
            "id": link_id,
            "source": node_from,
            "target": node_to,
            "weight": event.get("edge_weight", 0),
            "attack_type": attack_type,
        })

        # Thread-safe broadcast to all WebSocket clients
        _thread_safe_broadcast({
            "type": "GRAPH_UPDATE",
            "data": {
                "node_from": node_from,
                "node_to": node_to,
                "attack_type": attack_type,
                "edge_weight": event.get("edge_weight", 0),
                "simulation_id": event.get("simulation_id"),
                "transaction_id": event.get("transaction_id"),
            }
        })

    elif event.get("evades_heuristics") is not None:
        # Evasion alert from fraud.alerts.sandbox
        sim_id = event.get("simulation_id", "unknown")
        log.info("Evasion event ingested", simulation_id=sim_id)
        _cache.add_lineage(event)
        _thread_safe_broadcast({"type": "EVASION_EVENT", "data": event})

    elif event_type == "mutation_signal":
        sim_id = event.get("simulation_id", "unknown")
        log.info("Mutation signal ingested", simulation_id=sim_id)
        _cache.add_lineage(event)
        _thread_safe_broadcast({"type": "MUTATION_EVENT", "data": event})


# ─── Application Lifecycle ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer, _main_loop

    # Capture the running event loop so the Kafka thread can use it
    _main_loop = asyncio.get_running_loop()
    log.info("Control API starting...", loop_id=id(_main_loop))

    _consumer = RedTeamConsumer(
        bootstrap_servers=KAFKA_SERVERS,
        group_id=os.getenv("KAFKA_GROUP_ID_CONTROL", "control-api-group"),
        topics=[Topics.GRAPH_UPDATES, Topics.ALERTS, Topics.METRICS],
        handler=_on_kafka_event
    )
    _consumer.start()
    _status_engine.transition(LifecycleState.IDLE)
    log.info("Control API ready — Kafka consumer active, WebSocket endpoint live")

    yield

    log.info("Control API shutting down...")
    if _consumer:
        _consumer.stop()
    _main_loop = None
    log.info("Control API shut down")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="BLING — Sandbox Control API",
    description="Orchestration bridge, WebSocket stream, and evidence bundler for the BLING sandbox.",
    version="2.1.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "sandbox-control-api",
        "ws_clients": len(_active_connections),
        "sandbox_state": _status_engine.get_status().state,
    }


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Ping/pong keep-alive — also allows client to send control messages later
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        log.warning("WebSocket error", error=str(e))
        manager.disconnect(websocket)


# ─── Sandbox Control Endpoints ────────────────────────────────────────────────
class StartRequest(BaseModel):
    attack_type: str = "layering_chain"
    attack_depth: int = 6
    tps: float = 3.0
    mutation_generation: int = 0
    demo_safe_mode: bool = False


@app.post("/api/sandbox/start")
async def start_sandbox(req: StartRequest):
    _status_engine.transition(LifecycleState.STARTING, current_attack_type=req.attack_type)
    await broadcast_status()

    pool_size = 50 if req.demo_safe_mode else 300
    tps = min(req.tps, 2.0) if req.demo_safe_mode else req.tps

    payload = {
        "attack_type": req.attack_type,
        "account_pool_size": pool_size,
        "attack_depth": req.attack_depth,
        "tps": tps,
        "mutation_rate": 0.3,
        "mutation_generation": req.mutation_generation,
    }

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{GENERATOR_URL}/simulate", json=payload, timeout=10.0)
            r.raise_for_status()
            sim_id = r.json()["simulation_id"]
            _status_engine.transition(LifecycleState.RUNNING, simulation_id=sim_id)
            await broadcast_status()
            log.info("Sandbox started", simulation_id=sim_id, attack_type=req.attack_type)
            return {"status": "started", "simulation_id": sim_id}
        except Exception as e:
            _status_engine.transition(LifecycleState.ERROR, error_message=str(e))
            await broadcast_status()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sandbox/stop")
async def stop_sandbox():
    status = _status_engine.get_status()
    if status.simulation_id:
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(f"{GENERATOR_URL}/simulate/{status.simulation_id}", timeout=5.0)
            except Exception:
                pass
    _status_engine.transition(LifecycleState.PAUSED)
    await broadcast_status()
    return {"status": "stopped"}


@app.post("/api/sandbox/bundle")
async def create_bundle():
    _status_engine.transition(LifecycleState.EXPORTING)
    await broadcast_status()
    path = EvidenceBundler.create_bundle()
    _status_engine.transition(LifecycleState.COMPLETED)
    await broadcast_status()
    return {"status": "bundled", "path": path}


@app.post("/api/sandbox/clear")
async def clear_cache():
    _cache.clear()
    _status_engine.transition(LifecycleState.IDLE, simulation_id=None, current_attack_type=None)
    await broadcast_status()
    await manager.broadcast({"type": "FULL_STATE", "data": _cache.get_full_state()})
    return {"status": "cleared"}

@app.post("/api/sandbox/metrics")
async def update_metrics_endpoint(payload: Dict[str, Any]):
    _cache.update_metrics(payload)
    await manager.broadcast({"type": "METRICS_UPDATE", "data": payload})
    return {"status": "updated"}
