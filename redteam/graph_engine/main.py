# ============================================================
# Graph Engine — FastAPI Main + Kafka Consumer
# ============================================================
import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/streaming")

from topology_graph import TransactionGraph

try:
    from streaming.consumer import RedTeamConsumer
    from streaming.producer import RedTeamProducer
    from streaming.topics import Topics
except ImportError:
    from consumer import RedTeamConsumer
    from producer import RedTeamProducer
    from topics import Topics

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = structlog.get_logger()

# ─── State ────────────────────────────────────────────────
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
GRAPH_MAX_NODES = int(os.getenv("GRAPH_MAX_NODES", "50000"))
CYCLE_DEPTH = int(os.getenv("CYCLE_DETECTION_DEPTH", "10"))
TOP_N = int(os.getenv("CENTRALITY_TOP_N", "20"))

_graph: Optional[TransactionGraph] = None
_consumer: Optional[RedTeamConsumer] = None
_producer: Optional[RedTeamProducer] = None


def _on_transaction(txn: Dict[str, Any]) -> None:
    """Handle incoming transaction from Kafka."""
    global _graph, _producer
    try:
        _graph.add_transaction(txn)

        # Publish graph update event
        graph_update = {
            "event_type": "edge_added",
            "node_from": txn["sender_account"],
            "node_to": txn["receiver_account"],
            "edge_weight": txn.get("amount", 0),
            "attack_type": txn.get("attack_type"),
            "timestamp": txn.get("timestamp"),
            "simulation_id": txn.get("simulation_id"),
            "transaction_id": txn.get("transaction_id"),
            "_simulation": True,
        }
        _producer.publish(
            topic=Topics.GRAPH_UPDATES,
            payload=graph_update,
            key=txn.get("sender_account"),
        )
    except Exception as e:
        log.error("Transaction processing failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph, _consumer, _producer
    log.info("Topology Graph Engine starting...")
    _graph = TransactionGraph(max_nodes=GRAPH_MAX_NODES)
    _producer = RedTeamProducer(KAFKA_SERVERS)
    _consumer = RedTeamConsumer(
        bootstrap_servers=KAFKA_SERVERS,
        group_id=os.getenv("KAFKA_GROUP_ID_GRAPH", "graph-engine-group"),
        topics=[Topics.TRANSACTIONS],
        handler=_on_transaction,
    )
    _consumer.start()
    log.info("Topology Graph Engine ready — consuming sandbox topology stream")
    yield
    _consumer.stop()
    _producer.close()
    log.info("Topology Graph Engine shut down")


app = FastAPI(
    title="BLING — Topology Graph Engine",
    description="Live NetworkX graph of synthetic account flow topology. Exposes structural signals: cycles, centrality, layering chains, velocity. Research/Sandbox use only. Future: Neo4j migration.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Endpoints ────────────────────────────────────────────

@app.get("/health")
async def health():
    stats = _graph.get_stats() if _graph else {}
    return {"status": "healthy", "service": "graph-engine", **stats, "_simulation": True}


@app.get("/graph/stats")
async def graph_stats():
    """Current graph size and density."""
    return _graph.get_stats()


@app.get("/graph/cycles")
async def get_cycles():
    """Detect cyclic flows — round-trip laundering indicator."""
    cycles = _graph.detect_cycles(max_cycles=50)
    return {
        "cycles_detected": len(cycles),
        "cycles": cycles[:20],
        "sample_size": min(20, len(cycles)),
    }


@app.get("/graph/centrality")
async def get_centrality():
    """Top-N high-centrality nodes — mule hub indicators."""
    nodes = _graph.get_degree_centrality(top_n=TOP_N)
    return {
        "top_n": TOP_N,
        "nodes": nodes,
        "high_risk_count": sum(1 for n in nodes if n["centrality"] > 0.5),
    }


@app.get("/graph/chains")
async def get_chains():
    """Detect linear layering chains."""
    chains = _graph.get_layering_chains(min_depth=3)
    return {
        "chains_detected": len(chains),
        "chains": chains[:20],
    }


@app.post("/graph/analyze/{account_id}")
async def analyze_account(account_id: str):
    """Deep analysis of a specific account."""
    result = _graph.analyze_account(account_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/graph/velocity/{account_id}")
async def get_velocity(account_id: str, window_seconds: int = 300):
    """Transaction velocity for an account within time window."""
    return _graph.get_velocity(account_id, window_seconds)


@app.get("/graph/paths/{account_id}")
async def get_paths(account_id: str, max_depth: int = 5):
    """Trace suspicious fund flow paths from account."""
    paths = _graph.trace_suspicious_paths(account_id, max_depth=max_depth)
    return {
        "account_id": account_id,
        "paths_found": len(paths),
        "paths": paths[:30],
    }


@app.delete("/graph/reset")
async def reset_graph():
    """Clear the graph (for testing)."""
    _graph.clear()
    return {"status": "graph cleared"}
