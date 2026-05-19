# ============================================================
# BLING — Escape Analyzer & Graph Pattern Exporter
# ============================================================
# PURPOSE:
#   Consumes evasion events from the Topology Evaluation Harness.
#   Tracks which synthetic graph topologies evaded existing
#   heuristic detection. Exports "previously unseen synthetic graph
#   variations" as candidate patterns for Blue Team rule development.
#
#   IMPORTANT: This service does NOT trigger autonomous Blue Team
#   model updates. All exported patterns require human investigator
#   validation before operational usage.
#
# ARCHITECTURE POSITION:
#   Topology Evaluation Harness → Escape Analyzer
#   → [THIS SERVICE] Graph Pattern Exporter
# ============================================================
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import structlog
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Robust Path Resolution ───────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
redteam_root = os.path.dirname(current_dir)
if redteam_root not in sys.path:
    sys.path.insert(0, redteam_root)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from evasion_tracker import EscapeAnalyzer

from streaming.consumer import RedTeamConsumer
from streaming.producer import RedTeamProducer
from streaming.topics import Topics

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = structlog.get_logger()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
MUTATION_THRESHOLD = float(os.getenv("MUTATION_TRIGGER_THRESHOLD", "0.5"))
DIVERSITY_URL = os.getenv("DIVERSITY_URL", "http://topology-diversity:8082")

_analyzer: Optional[EscapeAnalyzer] = None
_consumer_evasions: Optional[RedTeamConsumer] = None
_producer: Optional[RedTeamProducer] = None


def _on_evasion_event(event: Dict[str, Any]) -> None:
    """
    Process an incoming evasion event from the Topology Evaluation Harness.
    Records the topology that evaded heuristics and retains it for export.
    """
    try:
        sim_id = event.get("simulation_id", "unknown")
        topology_type = event.get("topology_type", event.get("attack_type", "unknown"))
        mutation_gen = event.get("mutation_generation", 0)
        latency = event.get("evaluation_latency_ms", 0.0)
        evaded = event.get("evades_heuristics", True)  # messages on ALERTS topic = evasions

        _analyzer.record_topology_event(
            simulation_id=sim_id,
            topology_type=topology_type,
            mutation_generation=mutation_gen,
            evaded_heuristics=evaded,
            evaluation_latency_ms=latency,
            topology_payload=event if evaded else None,
        )

        # Check if the topology mutator should be signalled for a new variation
        if _analyzer.should_trigger_mutation(sim_id, MUTATION_THRESHOLD):
            session = _analyzer.get_session_analysis(sim_id)
            mutation_signal = {
                "event_type": "mutation_signal",
                "simulation_id": sim_id,
                "topology_type": topology_type,
                "mutation_generation": mutation_gen,
                "detection_rate": session.get("detection_rate", 0),
                "total_evaluated": session.get("total_evaluated", 0),
                "evasion_count": session.get("evaded", 0),
                # Clarification: this signals the deterministic Mutator,
                # NOT an autonomous model update.
                "signal_target": "topology_mutator",
                "_simulation": True,
            }
            _producer.publish(
                topic=Topics.METRICS,
                payload=mutation_signal,
                key=sim_id,
            )
            log.info(
                "Mutation signal published to Topology Mutator",
                simulation_id=sim_id,
                detection_rate=session.get("detection_rate"),
                note="Deterministic perturbation — not autonomous learning",
            )

    except Exception as e:
        log.error("Evasion event processing failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _analyzer, _consumer_evasions, _producer
    log.info("Escape Analyzer & Graph Pattern Exporter starting...")
    _analyzer = EscapeAnalyzer()
    _producer = RedTeamProducer(KAFKA_SERVERS)
    _consumer_evasions = RedTeamConsumer(
        bootstrap_servers=KAFKA_SERVERS,
        group_id=os.getenv("KAFKA_GROUP_ID_METRICS", "escape-analyzer-group"),
        topics=[Topics.ALERTS],
        handler=_on_evasion_event,
    )
    _consumer_evasions.start()
    log.info(
        "Escape Analyzer ready. Consuming evasion events from Topology Evaluation Harness."
    )
    yield
    _consumer_evasions.stop()
    _producer.close()
    log.info("Escape Analyzer shut down")


app = FastAPI(
    title="BLING — Escape Analyzer & Graph Pattern Exporter",
    description=(
        "Tracks which synthetic laundering graph topologies evade existing detection heuristics. "
        "Exports previously unseen synthetic graph variations as candidate patterns for Blue Team "
        "rule development. All exported patterns require human investigator validation. "
        "This service does NOT trigger autonomous model retraining. Research/Sandbox use only."
    ),
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Endpoints ────────────────────────────────────────────

@app.get("/health")
async def health():
    global_stats = _analyzer.get_global_stats() if _analyzer else {}
    return {
        "status": "healthy",
        "service": "escape-analyzer",
        **global_stats,
        "_simulation": True,
    }


@app.get("/analysis")
async def get_all_analysis():
    """All session evasion analysis results."""
    sessions = _analyzer.get_all_sessions()
    global_stats = _analyzer.get_global_stats()
    return {
        "global": global_stats,
        "sessions": sessions,
        "session_count": len(sessions),
    }


@app.get("/analysis/global")
async def get_global():
    return _analyzer.get_global_stats()


@app.get("/analysis/leaderboard")
async def get_leaderboard(top_n: int = Query(default=10, le=50)):
    """Sessions ranked by highest evasion rate against the evaluation harness."""
    return {"leaderboard": _analyzer.get_evasion_leaderboard(top_n=top_n)}


@app.get("/analysis/{simulation_id}")
async def get_session_analysis(simulation_id: str):
    result = _analyzer.get_session_analysis(simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Simulation session not found")
    return result


@app.get("/export/evasions")
async def export_evasion_topologies(
    topology_type: Optional[str] = None,
    min_mutation_gen: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
):
    """
    Export previously unseen synthetic graph variations that evaded heuristics.

    These are candidate structures for Blue Team rule development.
    IMPORTANT: All exported patterns require human investigator validation
    before operational usage. This export does NOT trigger automatic
    rule updates or model retraining.
    """
    results = _analyzer.get_evasion_topology_export(
        topology_type=topology_type,
        min_mutation_gen=min_mutation_gen,
        limit=limit * 2, # Fetch more to account for filtering
    )

    filtered_results = []
    async with httpx.AsyncClient() as client:
        for res in results:
            if len(filtered_results) >= limit:
                break
            try:
                # Ask Diversity Manager if this branch is novel enough to export
                r = await client.post(
                    f"{DIVERSITY_URL}/check_export", 
                    json={"simulation_id": res["simulation_id"]}, 
                    timeout=2.0
                )
                if r.status_code == 200 and r.json().get("is_export_worthy", True):
                    filtered_results.append(res)
            except Exception as e:
                log.warning(f"Failed to check export worthiness for {res['simulation_id']}: {e}")
                filtered_results.append(res) # Fallback to exporting if service is down

    return {
        "exported_topology_variations": filtered_results,
        "count": len(filtered_results),
        "filter_topology_type": topology_type,
        "filter_min_mutation_generation": min_mutation_gen,
        "validation_required": True,
        "note": (
            "Previously unseen synthetic graph variations. "
            "Requires human investigator validation before operational use. "
            "Blue Team does NOT learn automatically from these exports."
        ),
    }


# Compatibility endpoint for simulation runner
@app.get("/metrics/{simulation_id}")
async def get_metrics_compat(simulation_id: str):
    """Compatibility endpoint for simulation runner detection_rate queries."""
    result = _analyzer.get_session_analysis(simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if this run has evasions that should be automatically exported to evasion_exports
    detection_rate = result.get("detection_rate", 0.0)
    if detection_rate < MUTATION_THRESHOLD:
        # Find the evasion payload in the analyzer
        with _analyzer._lock:
            record = None
            for rec in _analyzer._evasion_topologies:
                if rec["simulation_id"] == simulation_id:
                    record = rec
                    break
        
        if record and record.get("topology_payload"):
            # Export to evasion_exports directory immediately!
            try:
                from redteam.canonical_exporter import export_pattern
            except ImportError:
                from canonical_exporter import export_pattern

            topo_type = record.get("topology_type", "unknown")
            gen = record.get("mutation_generation", 0)
            filename = f"evasion_{topo_type}_gen{gen}_{simulation_id}.json"
            try:
                export_pattern(record["topology_payload"], filename)
                log.info(
                    "Automatically exported evasion pattern to evasion_exports",
                    filename=filename,
                    evasion_count=len(record["topology_payload"])
                )
            except Exception as e:
                log.warning(
                    "Automatic evasion export failed schema validation",
                    error=str(e),
                    filename=filename
                )
                
    return result


class RecordRequest(BaseModel):
    simulation_id: str = "manual"
    topology_type: str = "unknown"
    mutation_generation: int = 0
    evaded_heuristics: bool = False
    evaluation_latency_ms: float = 0.0


@app.post("/analysis/record")
async def record_topology(payload: RecordRequest):
    """Manually record a topology evaluation outcome (for testing)."""
    _analyzer.record_topology_event(
        simulation_id=payload.simulation_id,
        topology_type=payload.topology_type,
        mutation_generation=payload.mutation_generation,
        evaded_heuristics=payload.evaded_heuristics,
        evaluation_latency_ms=payload.evaluation_latency_ms,
    )
    return {"status": "recorded"}
