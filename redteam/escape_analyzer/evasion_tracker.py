# ============================================================
# Escape Analyzer — Tracks Topology Evasion Outcomes
# ============================================================
# PURPOSE:
#   Records which synthetic graph topologies successfully evaded
#   the Topology Evaluation Harness. Stores the evasion topology
#   structure so it can be exported as "previously unseen synthetic
#   graph variations" to the Blue Team for rule development.
#
#   This is NOT an autonomous model feedback loop.
#   Human investigators validate all exported patterns before use.
# ============================================================
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


class EscapeAnalyzer:
    """
    Tracks evasion outcomes and retains the graph topology
    structures of simulations that evaded detection heuristics.

    Exported patterns are candidate inputs for Blue Team rule
    development — subject to human investigator validation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._evasion_topologies: List[Dict[str, Any]] = []  # for export
        self._global = {
            "total_topologies_evaluated": 0,
            "total_heuristic_detections": 0,
            "total_evasions": 0,
            "started_at": datetime.utcnow().isoformat() + "Z",
        }

    def record_topology_event(
        self,
        simulation_id: str,
        topology_type: str,
        mutation_generation: int,
        evaded_heuristics: bool,
        evaluation_latency_ms: float = 0.0,
        topology_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record one topology evaluation outcome.
        If the topology evaded heuristics, retain its structure for export.
        """
        with self._lock:
            self._global["total_topologies_evaluated"] += 1

            if simulation_id not in self._sessions:
                self._sessions[simulation_id] = {
                    "simulation_id": simulation_id,
                    "topology_type": topology_type,
                    "mutation_generation": mutation_generation,
                    "total_evaluated": 0,
                    "detected": 0,
                    "evaded": 0,
                    "evaluation_latencies_ms": [],
                    "started_at": datetime.utcnow().isoformat() + "Z",
                    "last_updated": None,
                }

            session = self._sessions[simulation_id]
            session["total_evaluated"] += 1
            session["mutation_generation"] = max(
                session["mutation_generation"], mutation_generation
            )

            if evaded_heuristics:
                session["evaded"] += 1
                self._global["total_evasions"] += 1

                # Retain the topology structure for export, grouping by simulation_id to reconstruct the graph
                if topology_payload:
                    existing_record = None
                    for rec in self._evasion_topologies:
                        if rec["simulation_id"] == simulation_id:
                            existing_record = rec
                            break
                    
                    if existing_record:
                        # Append the new transaction to the existing list of transactions for this topology
                        if not isinstance(existing_record["topology_payload"], list):
                            existing_record["topology_payload"] = [existing_record["topology_payload"]]
                        existing_record["topology_payload"].append(topology_payload)
                    else:
                        # Initialize a new record with a list of transactions for this topology
                        self._evasion_topologies.append({
                            "simulation_id": simulation_id,
                            "topology_type": topology_type,
                            "mutation_generation": mutation_generation,
                            "topology_payload": [topology_payload],
                            "captured_at": datetime.utcnow().isoformat() + "Z",
                            "export_status": "pending_investigator_review",
                        })
            else:
                session["detected"] += 1
                self._global["total_heuristic_detections"] += 1
                if evaluation_latency_ms > 0:
                    session["evaluation_latencies_ms"].append(evaluation_latency_ms)
            
            session["last_updated"] = datetime.utcnow().isoformat() + "Z"

    def get_session_analysis(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._sessions.get(simulation_id)
            if not session:
                return None
            return self._compute_derived(session)

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [self._compute_derived(s) for s in self._sessions.values()]

    def get_global_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._global["total_topologies_evaluated"]
            detected = self._global["total_heuristic_detections"]
            evaded = self._global["total_evasions"]
            return {
                **self._global,
                "global_detection_rate": round(detected / total, 4) if total > 0 else 0.0,
                "global_evasion_rate": round(evaded / total, 4) if total > 0 else 0.0,
                "session_count": len(self._sessions),
                "exportable_topology_variations": len(self._evasion_topologies),
                "scope": "sandbox_research_only",
            }

    def get_evasion_topology_export(
        self,
        topology_type: Optional[str] = None,
        min_mutation_gen: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Export previously unseen synthetic graph variations that evaded
        heuristic detection. These are candidate patterns for Blue Team
        rule development — requiring human investigator validation.
        """
        with self._lock:
            results = self._evasion_topologies
            if topology_type:
                results = [t for t in results if t["topology_type"] == topology_type]
            if min_mutation_gen > 0:
                results = [t for t in results if t["mutation_generation"] >= min_mutation_gen]
            return results[-limit:]

    def get_evasion_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Sessions ranked by highest evasion rate."""
        with self._lock:
            sessions = [self._compute_derived(s) for s in self._sessions.values()]
            return sorted(
                sessions, key=lambda x: x.get("evasion_rate", 0), reverse=True
            )[:top_n]

    def should_trigger_mutation(
        self,
        simulation_id: str,
        detection_rate_threshold: float = 0.5,
    ) -> bool:
        """
        Returns True if detection rate is above threshold.
        Signals the Topology Mutator to generate a new variation.
        This is NOT autonomous — the Mutator receives the signal
        and applies deterministic perturbation strategies.
        """
        session = self.get_session_analysis(simulation_id)
        if not session:
            return False
        return session.get("detection_rate", 0) >= detection_rate_threshold

    def _compute_derived(self, session: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(session)
        total = session["total_evaluated"]
        detected = session["detected"]
        evaded = session["evaded"]
        latencies = session.get("evaluation_latencies_ms", [])

        result["detection_rate"] = round(detected / total, 4) if total > 0 else 0.0
        result["evasion_rate"] = round(evaded / total, 4) if total > 0 else 0.0
        result["avg_evaluation_latency_ms"] = (
            round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        )
        result.pop("evaluation_latencies_ms", None)
        return result
