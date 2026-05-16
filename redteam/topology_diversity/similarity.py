import math
from typing import Dict, Any

class SimilarityEngine:
    """Calculates structural similarity and behavioral divergence between topologies."""

    @staticmethod
    def calculate_similarity(fp1: Dict[str, Any], fp2: Dict[str, Any]) -> float:
        """
        Compute motif-based similarity between two topology fingerprints.
        Returns a score between 0.0 (completely different) and 1.0 (identical).
        """
        if not fp1 or not fp2:
            return 0.0

        # 1. Triad Census Similarity (Motif Overlap)
        triad_sim = SimilarityEngine._dict_cosine_similarity(
            fp1.get("triad_census", {}), fp2.get("triad_census", {})
        )

        # 2. Cycle Signature Similarity
        c1 = fp1.get("cycle_signature", {})
        c2 = fp2.get("cycle_signature", {})
        cycle_sim = SimilarityEngine._scalar_similarity(c1.get("total_cycles", 0), c2.get("total_cycles", 0)) * 0.5 + \
                    SimilarityEngine._scalar_similarity(c1.get("avg_length", 0), c2.get("avg_length", 0)) * 0.5

        # 3. Degree Histogram Divergence (Hub profiles)
        in_hist_sim = SimilarityEngine._vector_similarity(fp1.get("in_degree_hist", []), fp2.get("in_degree_hist", []))
        out_hist_sim = SimilarityEngine._vector_similarity(fp1.get("out_degree_hist", []), fp2.get("out_degree_hist", []))
        hist_sim = (in_hist_sim + out_hist_sim) / 2.0

        # 4. Global Structural Similarity (Density, Hubs, Components, Spectra)
        global_sim = (
            SimilarityEngine._scalar_similarity(fp1.get("density", 0), fp2.get("density", 0)) * 0.3 +
            SimilarityEngine._scalar_similarity(fp1.get("hub_count", 0), fp2.get("hub_count", 0)) * 0.3 +
            SimilarityEngine._scalar_similarity(fp1.get("num_components", 0), fp2.get("num_components", 0)) * 0.2 +
            SimilarityEngine._scalar_similarity(fp1.get("spectral_variance", 0), fp2.get("spectral_variance", 0)) * 0.2
        )

        # Weighted combination emphasizing structural motifs over global scalars
        final_score = (triad_sim * 0.4) + (cycle_sim * 0.3) + (hist_sim * 0.2) + (global_sim * 0.1)
        
        # Ensure bounds
        return max(0.0, min(1.0, final_score))

    @staticmethod
    def _scalar_similarity(val1: float, val2: float) -> float:
        """Calculate similarity between two scalars, handling zeros."""
        if val1 == val2:
            return 1.0
        max_val = max(abs(val1), abs(val2))
        if max_val == 0:
            return 1.0
        return 1.0 - (abs(val1 - val2) / max_val)

    @staticmethod
    def _vector_similarity(v1: list, v2: list) -> float:
        """Cosine similarity between two lists."""
        if not v1 and not v2: return 1.0
        if not v1 or not v2: return 0.0
        
        # Pad to same length if needed
        max_len = max(len(v1), len(v2))
        v1_pad = v1 + [0] * (max_len - len(v1))
        v2_pad = v2 + [0] * (max_len - len(v2))

        dot_product = sum(a * b for a, b in zip(v1_pad, v2_pad))
        norm1 = math.sqrt(sum(a * a for a in v1_pad))
        norm2 = math.sqrt(sum(b * b for b in v2_pad))

        if norm1 == 0 or norm2 == 0:
            return 0.0 if norm1 != norm2 else 1.0
            
        return dot_product / (norm1 * norm2)

    @staticmethod
    def _dict_cosine_similarity(d1: dict, d2: dict) -> float:
        """Cosine similarity for dictionaries (like triad census)."""
        keys = set(d1.keys()).union(set(d2.keys()))
        if not keys: return 1.0
        
        dot_product = sum(d1.get(k, 0) * d2.get(k, 0) for k in keys)
        norm1 = math.sqrt(sum(v * v for v in d1.values()))
        norm2 = math.sqrt(sum(v * v for v in d2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0 if norm1 != norm2 else 1.0
            
        return dot_product / (norm1 * norm2)
