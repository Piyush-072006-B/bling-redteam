import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

class LineageTracker:
    """Manages immutable lineage tracking and lineage-aware export filtering."""
    
    def __init__(self, registry_base_path: str = "/app/evidence/runs"):
        self.registry_base_path = registry_base_path
        self._in_memory_lineage: Dict[str, Dict[str, Any]] = {}
        self._exported_descendants: Dict[str, List[str]] = {}

    def record_lineage(
        self, 
        simulation_id: str, 
        parent_id: Optional[str],
        topology_family: str,
        mutation_sequence: List[str],
        novelty_score: float,
        fingerprint: Dict[str, Any]
    ) -> str:
        """Records immutable ancestry metadata for a topology."""
        branch_id = f"branch_{uuid4().hex[:8]}"
        
        lineage_record = {
            "simulation_id": simulation_id,
            "branch_id": branch_id,
            "parent_simulation_id": parent_id,
            "topology_family": topology_family,
            "mutation_sequence": mutation_sequence,
            "novelty_score": novelty_score,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self._in_memory_lineage[simulation_id] = lineage_record
        
        # In a real deployment, we would append this to an immutable log or DB here
        
        return branch_id

    def is_export_worthy(self, simulation_id: str, min_novelty: float = 0.5) -> bool:
        """
        Lineage-aware export filtering.
        Prevents exporting near-identical descendants.
        """
        record = self._in_memory_lineage.get(simulation_id)
        if not record:
            return True # No lineage, default to export

        # 1. Direct Novelty check
        if record["novelty_score"] < min_novelty:
            return False

        parent_id = record["parent_simulation_id"]
        if not parent_id:
            return True # Root node, export it

        # 2. Descendant pruning: Has this parent already exported a very similar branch?
        # If the parent has exported > 3 descendants, the novelty threshold for new ones increases
        exported_siblings = self._exported_descendants.get(parent_id, [])
        if len(exported_siblings) > 2 and record["novelty_score"] < (min_novelty + 0.2):
            return False

        return True

    def mark_exported(self, simulation_id: str):
        """Mark a simulation as exported for lineage tracking."""
        record = self._in_memory_lineage.get(simulation_id)
        if record and record["parent_simulation_id"]:
            parent = record["parent_simulation_id"]
            if parent not in self._exported_descendants:
                self._exported_descendants[parent] = []
            self._exported_descendants[parent].append(simulation_id)

    def write_to_registry(self, simulation_id: str, payload: Dict[str, Any]):
        """Write lineage and payload to the unified run registry."""
        run_dir = os.path.join(self.registry_base_path, f"{simulation_id}")
        
        # Create immutable directory structure
        for subdir in ["graphs", "mutations", "exports", "metrics", "replay", "lineage", "fingerprints"]:
            os.makedirs(os.path.join(run_dir, subdir), exist_ok=True)

        lineage = self._in_memory_lineage.get(simulation_id, {})
        
        # Write Lineage
        with open(os.path.join(run_dir, "lineage", "ancestry.json"), "w") as f:
            json.dump(lineage, f, indent=2)
            
        # Write Fingerprint
        if "fingerprint" in payload:
            with open(os.path.join(run_dir, "fingerprints", "struct.json"), "w") as f:
                json.dump(payload.pop("fingerprint"), f, indent=2)

        # Write Summary
        with open(os.path.join(run_dir, "summary.json"), "w") as f:
            json.dump(payload, f, indent=2)

    def get_lineage(self, simulation_id: str) -> Dict[str, Any]:
        return self._in_memory_lineage.get(simulation_id, {})
