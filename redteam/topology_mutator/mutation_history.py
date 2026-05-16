# ============================================================
# Evolution Tracker — Mutation History
# ============================================================
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional


class EvolutionTracker:
    """
    Tracks the evolution of fraud strategies across mutation generations.
    Provides history for adversarial feedback loop analysis.
    """

    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(
        self,
        simulation_id: str,
        mutation_generation: int,
        original_pattern: str,
        mutated_pattern: str,
        mutations_applied: List[str],
        detection_rate_before: float,
        detection_rate_after: float,
        evasion_success: bool,
    ) -> None:
        entry = {
            "simulation_id": simulation_id,
            "mutation_generation": mutation_generation,
            "original_pattern": original_pattern,
            "mutated_pattern": mutated_pattern,
            "mutations_applied": mutations_applied,
            "detection_rate_before": round(detection_rate_before, 4),
            "detection_rate_after": round(detection_rate_after, 4),
            "evasion_improvement": round(detection_rate_before - detection_rate_after, 4),
            "evasion_success": evasion_success,
            "recorded_at": datetime.utcnow().isoformat() + "Z",
        }
        with self._lock:
            self._history.append(entry)

    def get_history(
        self,
        simulation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            data = self._history
            if simulation_id:
                data = [h for h in data if h["simulation_id"] == simulation_id]
            return data[-limit:]

    def get_best_evasions(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Return the mutations with the highest evasion improvement."""
        with self._lock:
            sorted_h = sorted(
                self._history,
                key=lambda x: x.get("evasion_improvement", 0),
                reverse=True,
            )
            return sorted_h[:top_n]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            if not self._history:
                return {"total_mutations": 0}
            successful = [h for h in self._history if h["evasion_success"]]
            improvements = [h["evasion_improvement"] for h in self._history]
            return {
                "total_mutations": len(self._history),
                "successful_evasions": len(successful),
                "evasion_success_rate": round(len(successful) / len(self._history), 4),
                "avg_improvement": round(sum(improvements) / len(improvements), 4),
                "max_improvement": round(max(improvements), 4),
            }
