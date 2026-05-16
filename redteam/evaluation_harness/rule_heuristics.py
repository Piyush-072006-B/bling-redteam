# ============================================================
# Rule-Based Detection Engine
# ============================================================
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Rule-based fraud detection.
    Each rule returns a risk contribution [0.0, 1.0] and a flag.
    """

    def __init__(
        self,
        structuring_threshold: float = 10000.0,
        velocity_window: int = 300,
        max_velocity_count: int = 10,
    ):
        self.structuring_threshold = structuring_threshold
        self.velocity_window = velocity_window
        self.max_velocity_count = max_velocity_count

        # In-memory velocity tracker: {account_id: [timestamps]}
        self._velocity: Dict[str, List[datetime]] = {}

    def evaluate(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all rules against a transaction.
        Returns list of triggered rules and composite risk score.
        """
        triggered = []
        risk_score = 0.0

        # Rule 1: Structuring / below-threshold amounts
        structuring_risk = self._rule_structuring(txn)
        if structuring_risk > 0:
            triggered.append({"rule": "structuring", "risk": structuring_risk})
            risk_score += structuring_risk * 0.3

        # Rule 2: Velocity attack
        velocity_risk, velocity_count = self._rule_velocity(txn)
        if velocity_risk > 0:
            triggered.append({
                "rule": "velocity_burst",
                "risk": velocity_risk,
                "count_in_window": velocity_count,
            })
            risk_score += velocity_risk * 0.4

        # Rule 3: Known attack type passthrough
        attack_risk = self._rule_attack_type(txn)
        if attack_risk > 0:
            triggered.append({"rule": "known_attack_pattern", "risk": attack_risk})
            risk_score += attack_risk * 0.3

        # Rule 4: Unusually large amount
        amount_risk = self._rule_large_amount(txn)
        if amount_risk > 0:
            triggered.append({"rule": "large_amount", "risk": amount_risk})
            risk_score += amount_risk * 0.2

        return {
            "transaction_id": txn.get("transaction_id"),
            "triggered_rules": triggered,
            "rule_risk_score": min(round(risk_score, 4), 1.0),
            "detection_method": "rule_based",
        }

    def _rule_structuring(self, txn: Dict[str, Any]) -> float:
        amount = float(txn.get("amount", 0))
        if 0 < amount < self.structuring_threshold:
            # Near threshold (90–99% of threshold) is highly suspicious
            ratio = amount / self.structuring_threshold
            if ratio >= 0.90:
                return 0.85
            elif ratio >= 0.75:
                return 0.5
        return 0.0

    def _rule_velocity(self, txn: Dict[str, Any]) -> tuple[float, int]:
        sender = txn.get("sender_account", "")
        try:
            ts = datetime.fromisoformat(txn.get("timestamp", "").replace("Z", "+00:00"))
            ts = ts.replace(tzinfo=None)
        except Exception:
            ts = datetime.utcnow()

        # Prune old entries
        cutoff = ts - timedelta(seconds=self.velocity_window)
        history = self._velocity.get(sender, [])
        history = [t for t in history if t >= cutoff]
        history.append(ts)
        self._velocity[sender] = history

        count = len(history)
        if count >= self.max_velocity_count:
            # Exponential risk as count grows
            excess = count - self.max_velocity_count
            return min(0.5 + excess * 0.05, 1.0), count
        return 0.0, count

    def _rule_attack_type(self, txn: Dict[str, Any]) -> float:
        attack = txn.get("attack_type", "")
        risk_map = {
            "velocity_attack": 0.9,
            "structuring": 0.7,
            "round_trip": 0.95,
            "mule_network": 0.85,
            "dormant_activation": 0.75,
            "layering_chain": 0.6,
            "fan_in_fan_out": 0.8,
        }
        return risk_map.get(attack, 0.0)

    def _rule_large_amount(self, txn: Dict[str, Any]) -> float:
        amount = float(txn.get("amount", 0))
        if amount >= 1_000_000:
            return 0.9
        elif amount >= 500_000:
            return 0.7
        elif amount >= 100_000:
            return 0.5
        elif amount >= 50_000:
            return 0.3
        return 0.0
