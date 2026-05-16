import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, "/app")

from fingerprinting import TopologyFingerprinter
from similarity import SimilarityEngine
from exploration import TopologyExplorationGraph
from lineage import LineageTracker

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = structlog.get_logger()

_exploration_graph: Optional[TopologyExplorationGraph] = None
_lineage_tracker: Optional[LineageTracker] = None
_history: List[Dict[str, Any]] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _exploration_graph, _lineage_tracker
    log.info("Topology Diversity Manager starting...")
    _exploration_graph = TopologyExplorationGraph()
    _lineage_tracker = LineageTracker(registry_base_path="/app/evidence/runs")
    log.info("Topology Diversity Manager ready")
    yield
    log.info("Topology Diversity Manager shut down")

app = FastAPI(
    title="BLING — Topology Diversity Manager",
    description="Structural graph morphology intelligence, fingerprinting, and novelty evaluation.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class EvaluateRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    simulation_id: str
    parent_simulation_id: Optional[str] = None
    mutation_sequence: List[str] = []

class EvaluateResponse(BaseModel):
    simulation_id: str
    topology_family: str
    novelty_score: float
    structural_divergence: float
    branch_id: str
    fingerprint: Dict[str, Any]
    is_novel: bool
    suggested_next_family: str

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "topology-diversity",
        "history_size": len(_history),
        "_simulation": True
    }

@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_topology(req: EvaluateRequest):
    if not req.transactions:
        raise HTTPException(status_code=400, detail="No transactions provided")

    # 1. Advanced Structural Signatures
    fingerprint = TopologyFingerprinter.generate_fingerprint(req.transactions)

    # 2. Topology Family Embeddings
    family = _exploration_graph.classify_family(fingerprint)

    # 3. Motif-Based Similarity & Novelty Scoring
    max_similarity = 0.0
    structural_divergence = 1.0

    if _history:
        # Compare against history (in a real system, limit to recent/relevant)
        similarities = [SimilarityEngine.calculate_similarity(fingerprint, h["fingerprint"]) for h in _history[-50:]]
        max_similarity = max(similarities) if similarities else 0.0
        structural_divergence = 1.0 - max_similarity

    # Novelty is basically divergence + some family transition bonus
    novelty_score = structural_divergence

    # Update Exploration Graph
    if req.parent_simulation_id:
        parent_record = _lineage_tracker.get_lineage(req.parent_simulation_id)
        if parent_record:
            _exploration_graph.record_transition(parent_record["topology_family"], family, novelty_score)

    # 4. Immutable Lineage Tracking
    branch_id = _lineage_tracker.record_lineage(
        simulation_id=req.simulation_id,
        parent_id=req.parent_simulation_id,
        topology_family=family,
        mutation_sequence=req.mutation_sequence,
        novelty_score=novelty_score,
        fingerprint=fingerprint
    )

    # Save to history
    _history.append({
        "simulation_id": req.simulation_id,
        "family": family,
        "fingerprint": fingerprint
    })

    # Novelty pressure informs next exploration
    novelty_pressure = 1.0 - novelty_score
    suggested_next = _exploration_graph.suggest_next_family(family, novelty_pressure)

    log.info(
        "Topology Evaluated",
        simulation_id=req.simulation_id,
        family=family,
        novelty_score=round(novelty_score, 3),
        divergence=round(structural_divergence, 3)
    )

    return EvaluateResponse(
        simulation_id=req.simulation_id,
        topology_family=family,
        novelty_score=novelty_score,
        structural_divergence=structural_divergence,
        branch_id=branch_id,
        fingerprint=fingerprint,
        is_novel=(novelty_score > 0.4), # Threshold
        suggested_next_family=suggested_next
    )

class ExportCheckRequest(BaseModel):
    simulation_id: str

@app.post("/check_export")
async def check_export(req: ExportCheckRequest):
    """Lineage-aware export filtering"""
    is_worthy = _lineage_tracker.is_export_worthy(req.simulation_id, min_novelty=0.4)
    if is_worthy:
        _lineage_tracker.mark_exported(req.simulation_id)
    return {"simulation_id": req.simulation_id, "is_export_worthy": is_worthy}

class RegisterRunRequest(BaseModel):
    simulation_id: str
    payload: Dict[str, Any]

@app.post("/register_run")
async def register_run(req: RegisterRunRequest):
    """Write to unified run registry"""
    _lineage_tracker.write_to_registry(req.simulation_id, req.payload)
    return {"status": "registered", "simulation_id": req.simulation_id}
