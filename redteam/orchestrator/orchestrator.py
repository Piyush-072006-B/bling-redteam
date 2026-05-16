# ============================================================
# BLING — Topology Robustness Testing Orchestrator
# ============================================================
# PURPOSE:
#   Orchestrates the adversarial graph topology generation and
#   robustness evaluation cycle. Coordinates the Red Team
#   pipeline to systematically generate, mutate, and evaluate
#   synthetic laundering graph topologies.
#
# WHAT THIS IS:
#   A sandboxed research orchestrator for testing detection
#   heuristic robustness against evolving graph structures.
#
# WHAT THIS IS NOT:
#   - NOT an autonomous production AML system
#   - NOT a continuously self-improving AI
#   - NOT a Blue Team model trainer
#
# CYCLE:
#   1. Generate synthetic graph topology (fraud pattern)
#   2. Apply topology mutations (if prior run was detected)
#   3. Stream topology through Kafka sandbox
#   4. Topology Evaluation Harness assesses evasion
#   5. Escape Analyzer measures evasion rate
#   6. If detection rate >= threshold → signal Mutator
#   7. Mutator applies deterministic perturbation strategies
#   8. Repeat with next topology variation
#
# ADVERSARIAL TRAINING APPROACH:
#   Phase 1 (Prototype): Synthetic perturbations — amount
#   variations, timing shifts, intermediary node insertion,
#   topology changes, transaction splitting.
#   Phase 2 (Research): Confirmed historical fraud patterns.
#   All discoveries validated by human investigators.
# ============================================================
import asyncio
import logging
import os
import random
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
import structlog

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = structlog.get_logger()

# --- Robust Path Resolution ---
current_dir = os.path.dirname(os.path.abspath(__file__))
redteam_root = os.path.dirname(current_dir)
if redteam_root not in sys.path:
    sys.path.insert(0, redteam_root)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

# --- Service URLs ---
GENERATOR_URL = os.getenv("GENERATOR_URL", "http://topology-generator:8001")
GRAPH_URL = os.getenv("GRAPH_ENGINE_URL", "http://topology-graph-engine:8002")
HARNESS_URL = os.getenv("DETECTOR_URL", "http://evaluation-harness:8003")
MUTATOR_URL = os.getenv("MUTATOR_URL", "http://topology-mutator:8004")
ESCAPE_ANALYZER_URL = os.getenv("METRICS_URL", "http://escape-analyzer:8005")
DIVERSITY_URL = os.getenv("DIVERSITY_URL", "http://topology-diversity:8082")
CONTROL_API_URL = os.getenv("CONTROL_API_URL", "http://sandbox-control-api:8080")

# ─── Robustness Testing Configuration ─────────────────────
CYCLE_INTERVAL = float(os.getenv("LOOP_INTERVAL_SECONDS", "10"))
MAX_CYCLES = int(os.getenv("MAX_LOOP_ITERATIONS", "100"))

# Detection rate threshold above which a topology mutation is triggered
# This means: if >= 50% of topology events are detected, mutate the topology
MUTATION_TRIGGER_THRESHOLD = float(os.getenv("MUTATION_TRIGGER_THRESHOLD", "0.5"))
MAX_MUTATION_GENERATIONS = int(os.getenv("MAX_MUTATION_GENERATIONS", "20"))

TOPOLOGY_TYPES = [
    "layering_chain",     # Sequential A→B→C→D fund hops
    "round_trip",          # Cyclic A→B→C→A flow
    "mule_network",        # Hub→mule dispersion
    "structuring",         # Sub-threshold smurfing
    "dormant_activation",  # Dormant account burst
    "velocity_attack",     # Rapid-fire flow pattern
    "fan_in_fan_out",      # Aggregate then disperse
]


async def wait_for_services(client: httpx.AsyncClient, max_wait: int = 180) -> None:
    """Wait until all pipeline services are healthy before starting the cycle."""
    services = {
        "generator":       f"{GENERATOR_URL}/health",
        "graph-engine":    f"{GRAPH_URL}/health",
        "eval-harness":    f"{HARNESS_URL}/health",
        "mutator":         f"{MUTATOR_URL}/health",
        "escape-analyzer": f"{ESCAPE_ANALYZER_URL}/health",
        "topology-diversity": f"{DIVERSITY_URL}/health",
    }
    log.info("Waiting for all pipeline services to become ready...")
    deadline = time.monotonic() + max_wait

    while time.monotonic() < deadline:
        results = {}
        for name, url in services.items():
            try:
                r = await client.get(url, timeout=3.0)
                results[name] = r.status_code == 200
            except Exception:
                results[name] = False

        all_ready = all(results.values())
        not_ready = [k for k, v in results.items() if not v]

        if all_ready:
            log.info("All pipeline services ready — beginning robustness testing cycle")
            return

        log.info(f"Services not yet ready: {not_ready}. Waiting...")
        await asyncio.sleep(5)

    raise RuntimeError("Pipeline services did not become ready within timeout")


async def generate_topology(
    client: httpx.AsyncClient,
    topology_type: str,
    run_id: str,
    topology_depth: int = 6,
    mutation_generation: int = 0,
) -> List[Dict[str, Any]]:
    """Generate a synthetic laundering graph topology."""
    payload = {
        "attack_type": topology_type,
        "account_pool_size": 200,
        "attack_depth": topology_depth,
        "mutation_generation": mutation_generation,
        "simulation_id": run_id,
    }
    r = await client.post(f"{GENERATOR_URL}/generate", json=payload, timeout=15.0)
    r.raise_for_status()
    transactions = r.json()
    log.info(
        "Topology generated",
        topology_type=topology_type,
        run_id=run_id,
        nodes=len(transactions),
        mutation_gen=mutation_generation,
    )
    return transactions


async def stream_topology(
    client: httpx.AsyncClient,
    run_id: str,
    topology_type: str,
    topology_depth: int = 6,
    tps: float = 3.0,
    stream_duration: int = 8,
    mutation_generation: int = 0,
) -> str:
    """Stream a topology into the Kafka sandbox. Return run_id."""
    payload = {
        "attack_type": topology_type,
        "account_pool_size": 300,
        "attack_depth": topology_depth,
        "tps": tps,
        "mutation_rate": 0.3,
        "mutation_generation": mutation_generation,
        "simulation_id": run_id,
    }
    r = await client.post(f"{GENERATOR_URL}/simulate", json=payload, timeout=10.0)
    r.raise_for_status()
    run_id = r.json()["simulation_id"]
    log.info(
        "Topology stream started",
        run_id=run_id,
        topology_type=topology_type,
        mutation_gen=mutation_generation,
    )
    await asyncio.sleep(stream_duration)
    try:
        await client.delete(f"{GENERATOR_URL}/simulate/{run_id}", timeout=5.0)
    except Exception:
        pass
    return run_id


async def get_evasion_rate(
    client: httpx.AsyncClient,
    run_id: str,
) -> float:
    """
    Fetch evasion rate for this run from the Escape Analyzer.
    Evasion rate = % of topology events that evaded the harness.
    """
    try:
        r = await client.get(
            f"{ESCAPE_ANALYZER_URL}/metrics/{run_id}", timeout=5.0
        )
        if r.status_code == 200:
            data = r.json()
            # detection_rate = what the harness caught
            # We use this to decide if mutation is needed
            return data.get("detection_rate", 0.0)
        elif r.status_code == 404:
            return 0.0
    except Exception as e:
        log.warning(f"Could not fetch evasion analysis for {run_id}: {e}")
    return 0.0


async def apply_topology_mutation(
    client: httpx.AsyncClient,
    transactions: List[Dict[str, Any]],
    run_id: str,
    topology_type: str,
    mutation_generation: int,
    detection_rate: float,
) -> Dict[str, Any]:
    """
    Signal the Topology Mutator to generate a perturbation variation.
    Applies deterministic perturbation strategies — amount variations,
    timing shifts, intermediary node insertion, transaction splitting.
    This is NOT autonomous learning.
    """
    payload = {
        "transactions": transactions,
        "simulation_id": run_id,
        "original_pattern": topology_type,
        "mutation_generation": mutation_generation,
        "detection_rate_before": detection_rate,
    }
    r = await client.post(f"{MUTATOR_URL}/mutate", json=payload, timeout=20.0)
    r.raise_for_status()
    result = r.json()
    log.info(
        "Topology mutation applied",
        perturbation_strategies=result.get("strategies_applied"),
        original_nodes=result.get("original_count"),
        mutated_nodes=result.get("mutated_count"),
        note="Deterministic perturbation — not autonomous model improvement",
    )
    return result


async def get_graph_stats(client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        r = await client.get(f"{GRAPH_URL}/graph/stats", timeout=5.0)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


async def evaluate_topology_diversity(
    client: httpx.AsyncClient,
    transactions: List[Dict[str, Any]],
    simulation_id: str,
    parent_simulation_id: Optional[str] = None,
    mutation_sequence: List[str] = None,
) -> Dict[str, Any]:
    """Evaluate structural novelty and get semi-guided evolution feedback."""
    payload = {
        "transactions": transactions,
        "simulation_id": simulation_id,
        "parent_simulation_id": parent_simulation_id,
        "mutation_sequence": mutation_sequence or [],
    }
    try:
        r = await client.post(f"{DIVERSITY_URL}/evaluate", json=payload, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning(f"Diversity evaluation failed: {e}")
        return {}


async def register_run(
    client: httpx.AsyncClient,
    simulation_id: str,
    transactions: List[Dict[str, Any]],
    diversity_eval: Dict[str, Any],
    detection_rate: float,
) -> None:
    """Register the run in the immutable lineage registry."""
    payload = {
        "simulation_id": simulation_id,
        "payload": {
            "transactions_count": len(transactions),
            "detection_rate": detection_rate,
            "fingerprint": diversity_eval.get("fingerprint", {}),
            "novelty_score": diversity_eval.get("novelty_score", 0.0),
            "structural_divergence": diversity_eval.get("structural_divergence", 0.0),
            "topology_family": diversity_eval.get("topology_family", "unknown"),
            "branch_id": diversity_eval.get("branch_id", "unknown"),
        }
    }
    try:
        await client.post(f"{DIVERSITY_URL}/register_run", json=payload, timeout=5.0)
    except Exception as e:
        log.warning(f"Failed to register run: {e}")

    try:
        await client.post(f"{CONTROL_API_URL}/api/sandbox/metrics", json=payload["payload"], timeout=2.0)
    except Exception as e:
        log.warning(f"Failed to push metrics to control API: {e}")


async def robustness_testing_cycle(client: httpx.AsyncClient) -> None:
    """
    Core robustness testing cycle.

    Systematically generates, streams, evaluates, and mutates
    synthetic graph topologies to map the evasion boundary of
    existing detection heuristics.

    Phase 1 Prototype: Synthetic perturbations only.
    All evasion discoveries exported for human investigator review.
    Blue Team does NOT learn automatically from these results.
    """
    cycle = 0
    session_start = datetime.utcnow()

    log.info("═" * 55)
    log.info("BLING Adversarial Graph Topology Robustness Testing")
    log.info("Phase 1 — Synthetic Perturbation Evaluation")
    log.info(f"Max cycles: {MAX_CYCLES} | Cycle interval: {CYCLE_INTERVAL}s")
    log.info(f"Mutation trigger threshold: {MUTATION_TRIGGER_THRESHOLD:.0%}")
    log.info("Blue Team does NOT learn from these results automatically")
    log.info("═" * 55)

    # Track per-topology mutation state
    topology_state: Dict[str, Dict] = {}
    current_topology_type = random.choice(TOPOLOGY_TYPES)
    parent_simulation_id = None
    mutation_sequence = []

    while cycle < MAX_CYCLES:
        cycle += 1
        topology_type = current_topology_type
        run_id = f"run_{uuid4().hex[:10]}"

        if topology_type not in topology_state:
            topology_state[topology_type] = {
                "mutation_generation": 0,
                "last_detection_rate": 1.0,
                "total_cycles": 0,
            }

        state = topology_state[topology_type]
        mutation_gen = state["mutation_generation"]

        log.info("─" * 55)
        log.info(
            f"CYCLE {cycle}/{MAX_CYCLES} | Topology: {topology_type} | "
            f"Mutation Gen: {mutation_gen} | Run: {run_id}"
        )

        try:
            # ── 1. Generate graph topology ─────────────────
            transactions = await generate_topology(
                client, topology_type, run_id,
                topology_depth=6 + mutation_gen,
                mutation_generation=mutation_gen,
            )

            # ── 2. Apply perturbation if prior run was detected
            if mutation_gen > 0 and transactions:
                mutation_result = await apply_topology_mutation(
                    client,
                    transactions=transactions,
                    run_id=run_id,
                    topology_type=topology_type,
                    mutation_generation=mutation_gen,
                    detection_rate=state["last_detection_rate"],
                )
                transactions = mutation_result.get("transactions", transactions)
                strategies = mutation_result.get("strategies_applied", [])
                mutation_sequence.extend(strategies)

            # ── 2.5 Evaluate Structural Novelty ────────────
            diversity_eval = await evaluate_topology_diversity(
                client, 
                transactions, 
                run_id, 
                parent_simulation_id, 
                mutation_sequence
            )
            
            novelty_score = diversity_eval.get("novelty_score", 1.0)
            structural_divergence = diversity_eval.get("structural_divergence", 1.0)
            suggested_next_family = diversity_eval.get("suggested_next_family", topology_type)
            actual_family = diversity_eval.get("topology_family", topology_type)

            log.info(
                "Structural Morphology Evaluated",
                novelty_score=f"{novelty_score:.3f}",
                divergence=f"{structural_divergence:.3f}",
                classified_family=actual_family
            )

            # ── 3. Stream topology through sandbox ─────────
            stream_id = await stream_topology(
                client,
                run_id=run_id,
                topology_type=topology_type,
                topology_depth=6 + mutation_gen,
                tps=3.0,
                stream_duration=int(CYCLE_INTERVAL * 0.7),
                mutation_generation=mutation_gen,
            )

            # ── 4. Allow harness to process stream ─────────
            await asyncio.sleep(3.0)

            # ── 5. Measure evasion outcome ─────────────────
            detection_rate = await get_evasion_rate(client, stream_id)
            graph_stats = await get_graph_stats(client)

            state["last_detection_rate"] = detection_rate
            state["total_cycles"] += 1

            log.info(
                "Cycle evaluation",
                run_id=stream_id,
                detection_rate=f"{detection_rate:.1%}",
                evasion_rate=f"{1 - detection_rate:.1%}",
                graph_nodes=graph_stats.get("nodes", "?"),
                graph_edges=graph_stats.get("edges", "?"),
            )

            # ── 5.5 Immutable Lineage Tracking ─────────────
            await register_run(client, stream_id, transactions, diversity_eval, detection_rate)

            # ── 6. Decide whether to mutate topology ───────
            if detection_rate >= MUTATION_TRIGGER_THRESHOLD:
                if mutation_gen < MAX_MUTATION_GENERATIONS and novelty_score > 0.1:
                    state["mutation_generation"] += 1
                    parent_simulation_id = run_id # Lineage parent for next iteration
                    log.info(
                        f"⚠ Detection rate {detection_rate:.1%} ≥ threshold "
                        f"→ Topology mutation triggered (gen {state['mutation_generation']})"
                    )
                else:
                    reason = "Max generations reached" if mutation_gen >= MAX_MUTATION_GENERATIONS else "Low novelty"
                    log.info(
                        f"{reason} for {topology_type}. Transitioning to {suggested_next_family}."
                    )
                    state["mutation_generation"] = 0
                    current_topology_type = suggested_next_family
                    parent_simulation_id = None
                    mutation_sequence = []
            else:
                log.info(
                    f"✓ Topology evasion recorded. "
                    f"Detection rate {detection_rate:.1%} < threshold. "
                    f"Pattern exported to Escape Analyzer."
                )
                # Success means we explore a new branch
                current_topology_type = suggested_next_family
                parent_simulation_id = None
                mutation_sequence = []

        except Exception as e:
            log.error(f"Cycle {cycle} error: {e}", exc_info=True)

        await asyncio.sleep(CYCLE_INTERVAL)

    elapsed = (datetime.utcnow() - session_start).total_seconds()
    log.info("═" * 55)
    log.info(
        f"Robustness testing complete — {cycle} cycles in {elapsed:.1f}s. "
        f"Review /export/evasions on the Escape Analyzer for discovered topology variations."
    )
    log.info("═" * 55)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        await wait_for_services(client)
        await robustness_testing_cycle(client)


if __name__ == "__main__":
    asyncio.run(main())
