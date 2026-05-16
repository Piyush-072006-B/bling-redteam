# ============================================================
# Topology Evaluator — Fixed Benchmark Evaluation Model
# ============================================================
# PURPOSE:
#   Provides a STATIC baseline evaluation model for robustness
#   testing of synthetic graph topologies. This evaluator does
#   NOT retrain online, does NOT adapt continuously, and does
#   NOT claim autonomous learning.
#
#   It answers ONE question:
#   "Did this graph topology evade existing detection heuristics?"
#
# SCOPE:
#   Research/Sandbox use only. Part of the Topology Evaluation
#   Harness. This is NOT a production fraud detector.
# ============================================================
import logging
from typing import Any, Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# ─── Static Baseline Configuration ────────────────────────
# The benchmark model trains ONCE at startup on synthetic
# baseline data representing typical transaction distributions.
# It is NEVER updated after initialization.
_BASELINE_SAMPLE_COUNT = 500
_BASELINE_CONTAMINATION = 0.15  # expected anomaly ratio in baseline


class TopologyEvaluator:
    """
    Fixed benchmark evaluation model for topology robustness testing.

    Trains once at startup on a static synthetic baseline representing
    typical financial flow distributions. This fixed state provides a
    stable, reproducible benchmark so that changes in evasion rate over
    time reflect topology mutations — NOT model drift.

    This is intentionally NOT an adaptive or online-learning system.
    For research integrity, the benchmark must remain constant across
    all topology evaluation runs within a simulation session.
    """

    def __init__(self, contamination: float = _BASELINE_CONTAMINATION):
        self.contamination = contamination
        self._model: IsolationForest = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            random_state=42,   # fixed seed for reproducibility
            n_jobs=-1,
        )
        self._scaler = StandardScaler()
        self._is_initialized = False
        self._total_evaluated = 0

    def initialize(self) -> None:
        """
        Train the fixed benchmark model on a static synthetic baseline.
        Called ONCE at service startup. Never called again.
        """
        logger.info("Initializing fixed benchmark evaluation model...")
        rng = np.random.default_rng(seed=42)  # deterministic baseline

        # Generate synthetic baseline representing normal flow distributions
        # This is a stable reference point — NOT training data from live attacks.
        baseline = np.column_stack([
            rng.lognormal(mean=9.0, sigma=1.5, size=_BASELINE_SAMPLE_COUNT),  # log-amount
            rng.uniform(0, 23, size=_BASELINE_SAMPLE_COUNT),                   # hour of day
            rng.choice(range(7), size=_BASELINE_SAMPLE_COUNT).astype(float),   # topology type
            np.zeros(_BASELINE_SAMPLE_COUNT),                                   # mutation gen 0
            rng.binomial(1, 0.05, size=_BASELINE_SAMPLE_COUNT).astype(float),  # near-threshold
            rng.lognormal(mean=9.0, sigma=1.5, size=_BASELINE_SAMPLE_COUNT) / 100000.0,  # normalized
        ])

        self._scaler.fit(baseline)
        X_scaled = self._scaler.transform(baseline)
        self._model.fit(X_scaled)
        self._is_initialized = True
        logger.info(
            f"TopologyEvaluator initialized. Fixed benchmark ready. "
            f"Baseline samples: {_BASELINE_SAMPLE_COUNT}. "
            f"This model will NOT retrain."
        )

    def _extract_features(self, txn: Dict[str, Any]) -> List[float]:
        """
        Extract graph-topology-relevant features from a transaction node.
        These features reflect structural properties of the flow pattern,
        not isolated transaction attributes.
        """
        amount = float(txn.get("amount", 0))
        mutation_gen = float(txn.get("mutation_generation", 0))

        # Hour of day — temporal flow pattern
        try:
            from datetime import datetime
            ts = txn.get("timestamp", "")
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            hour = float(dt.hour)
        except Exception:
            hour = 12.0

        # Topology type encoding — represents the graph structure pattern
        topology_map = {
            "layering_chain": 0,
            "round_trip": 1,
            "mule_network": 2,
            "structuring": 3,
            "dormant_activation": 4,
            "velocity_attack": 5,
            "fan_in_fan_out": 6,
        }
        topology_enc = float(topology_map.get(txn.get("attack_type", ""), -1))

        # Amount structural indicators
        log_amount = float(np.log1p(amount))
        is_near_threshold = float(7500 <= amount <= 10000)

        return [
            log_amount,
            hour,
            topology_enc,
            mutation_gen,
            is_near_threshold,
            amount / 100000.0,
        ]

    def evaluate(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate whether a transaction's topology features evade the
        fixed benchmark heuristics.

        Returns a score indicating anomaly likelihood relative to the
        static baseline — NOT a production fraud verdict.
        """
        if not self._is_initialized:
            return {
                "transaction_id": txn.get("transaction_id"),
                "topology_risk_score": 0.0,
                "evades_baseline": False,
                "evaluator_ready": False,
                "evaluation_method": "topology_evaluator_baseline",
                "note": "Benchmark not yet initialized",
            }

        self._total_evaluated += 1

        try:
            features = self._extract_features(txn)
            X = np.array([features])
            X_scaled = self._scaler.transform(X)
            score = self._model.decision_function(X_scaled)[0]
            pred = self._model.predict(X_scaled)[0]

            # Isolation Forest: -1 = anomaly vs baseline, 1 = within baseline
            # Lower decision_function score = more anomalous vs baseline
            normalized_risk = max(0.0, min(1.0, -score + 0.5))
            evades_baseline = pred == -1

            return {
                "transaction_id": txn.get("transaction_id"),
                "topology_risk_score": round(float(normalized_risk), 4),
                "evades_baseline": evades_baseline,
                "raw_score": round(float(score), 6),
                "evaluator_ready": True,
                "evaluation_method": "topology_evaluator_baseline",
                "mutation_generation": txn.get("mutation_generation", 0),
            }
        except Exception as e:
            logger.error(f"Topology evaluation failed: {e}")
            return {
                "transaction_id": txn.get("transaction_id"),
                "topology_risk_score": 0.0,
                "evades_baseline": False,
                "evaluator_ready": False,
                "evaluation_method": "topology_evaluator_baseline",
            }

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    @property
    def total_evaluated(self) -> int:
        return self._total_evaluated
