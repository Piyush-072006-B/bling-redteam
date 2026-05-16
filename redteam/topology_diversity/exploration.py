import random
from typing import Dict, Any, List

class TopologyExplorationGraph:
    """Manages the dynamic exploration of structural graph morphologies."""
    
    FAMILIES = [
        "distributed_laundering_mesh",
        "cyclic_laundering_ring",
        "hierarchical_layering_chain",
        "fragmented_swarm_topology",
        "hybrid_mesh_cycle",
        "multi_stage_funnel",
        "lattice_laundering_structure",
        "multi_hub_dispersal_network"
    ]

    def __init__(self):
        # Track how many times each family has been explored
        self.exploration_counts = {f: 0 for f in self.FAMILIES}
        
        # Track transition success (how often moving from A->B yielded high novelty)
        self.transition_weights = {
            f1: {f2: 1.0 for f2 in self.FAMILIES} for f1 in self.FAMILIES
        }

    def classify_family(self, fingerprint: Dict[str, Any]) -> str:
        """Classify a fingerprint into a semantic topology family."""
        # This is a heuristic classification based on fingerprint signatures.
        # In a full ML system, this would be a trained embedding model.
        
        triads = fingerprint.get("triad_census", {})
        cycles = fingerprint.get("cycle_signature", {}).get("total_cycles", 0)
        components = fingerprint.get("num_components", 1)
        hubs = fingerprint.get("hub_count", 0)
        density = fingerprint.get("density", 0)

        # Basic heuristic mapping
        if components > 5 and density < 0.05:
            return "fragmented_swarm_topology"
        elif hubs > 3 and density > 0.1:
            return "multi_hub_dispersal_network"
        elif cycles > 10 and density > 0.15:
            return "hybrid_mesh_cycle"
        elif cycles > 0 and hubs == 0:
            return "cyclic_laundering_ring"
        elif density > 0.2:
            return "distributed_laundering_mesh"
        elif hubs == 1 and triads.get('030T', 0) > 0: # Transitive triads imply stages
            return "multi_stage_funnel"
        elif triads.get('030C', 0) > 0: # Cyclic triads
            return "lattice_laundering_structure"
        else:
            return "hierarchical_layering_chain"

    def suggest_next_family(self, current_family: str, novelty_pressure: float) -> str:
        """
        Suggests the next topology family to explore.
        High novelty pressure means we should explore further away.
        """
        if current_family not in self.FAMILIES:
            return random.choice(self.FAMILIES)

        # Get transition weights from current family
        weights = self.transition_weights[current_family]
        
        # Adjust weights based on exploration counts to favor underexplored areas
        adjusted_weights = []
        for f in self.FAMILIES:
            w = weights[f]
            # Penalty for over-exploration
            explore_penalty = 1.0 / (1.0 + self.exploration_counts[f])
            
            # If novelty pressure is high, favor low-weight transitions (explore)
            # If low, favor high-weight transitions (exploit)
            if novelty_pressure > 0.7:
                final_w = (1.0 / max(w, 0.1)) * explore_penalty 
            else:
                final_w = w * explore_penalty
                
            adjusted_weights.append(final_w)

        # Probabilistic selection
        selected = random.choices(self.FAMILIES, weights=adjusted_weights, k=1)[0]
        return selected

    def record_transition(self, from_family: str, to_family: str, novelty_yield: float):
        """Update exploration graph with the result of a transition."""
        if from_family in self.transition_weights and to_family in self.transition_weights[from_family]:
            self.exploration_counts[to_family] += 1
            # Update weight with moving average
            current_w = self.transition_weights[from_family][to_family]
            self.transition_weights[from_family][to_family] = (current_w * 0.8) + (novelty_yield * 0.2)
