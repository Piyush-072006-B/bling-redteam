# ============================================================
# Mutation Strategies — Red Team Fraud Mutator
# ============================================================
import logging
import random
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

DEVICE_PREFIXES = ["mob", "web", "atm", "pos", "api"]
GEO_LOCATIONS = [
    "37.5665,126.9780", "40.7128,-74.0060", "51.5074,-0.1278",
    "48.8566,2.3522", "35.6762,139.6503", "1.3521,103.8198",
]


class MutationStrategies:
    """
    Implements 7 mutation strategies to evolve fraud patterns.
    Each strategy modifies a transaction list to evade detection.
    """

    @staticmethod
    def split_transaction(
        txns: List[Dict[str, Any]],
        split_count: int = 3,
        account_pool_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Split large transactions into multiple smaller ones.
        Evades large-amount rules and velocity detection.
        """
        mutated = []
        for txn in txns:
            amount = txn.get("amount", 0)
            if amount > 5000 and random.random() < 0.7:
                n = random.randint(2, split_count)
                fractions = [random.random() for _ in range(n)]
                total = sum(fractions)
                ts = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))

                for i, frac in enumerate(fractions):
                    t = deepcopy(txn)
                    t["transaction_id"] = f"txn_{uuid4().hex[:14]}"
                    t["amount"] = round(amount * frac / total, 2)
                    t["timestamp"] = (ts + timedelta(seconds=i * random.randint(30, 600))).isoformat() + "Z"
                    t["mutation_applied"] = "split_transaction"
                    mutated.append(t)
            else:
                mutated.append(txn)
        logger.debug(f"split_transaction: {len(txns)} → {len(mutated)} txns")
        return mutated

    @staticmethod
    def delay_transfers(
        txns: List[Dict[str, Any]],
        max_delay_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Add temporal jitter to transactions.
        Evades velocity window detection.
        """
        mutated = []
        for txn in txns:
            t = deepcopy(txn)
            try:
                ts = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))
                delay = timedelta(hours=random.uniform(1, max_delay_hours))
                t["timestamp"] = (ts + delay).isoformat() + "Z"
            except Exception:
                pass
            t["mutation_applied"] = "delay_transfers"
            mutated.append(t)
        return mutated

    @staticmethod
    def add_noise_accounts(
        txns: List[Dict[str, Any]],
        noise_ratio: float = 0.3,
        account_pool_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Insert decoy transactions to noise accounts.
        Evades graph topology detection.
        """
        if not account_pool_ids:
            account_pool_ids = [f"acc_{uuid4().hex[:10]}" for _ in range(20)]

        mutated = list(deepcopy(txns))
        noise_count = max(1, int(len(txns) * noise_ratio))

        for _ in range(noise_count):
            base = random.choice(txns)
            ts = datetime.fromisoformat(base["timestamp"].replace("Z", "+00:00"))
            noise_txn = deepcopy(base)
            noise_txn["transaction_id"] = f"txn_{uuid4().hex[:14]}"
            noise_txn["sender_account"] = random.choice(account_pool_ids)
            noise_txn["receiver_account"] = random.choice(account_pool_ids)
            noise_txn["amount"] = round(random.uniform(50, 500), 2)
            noise_txn["timestamp"] = (ts + timedelta(seconds=random.randint(10, 3600))).isoformat() + "Z"
            noise_txn["attack_type"] = "noise"
            noise_txn["mutation_applied"] = "add_noise_accounts"
            mutated.append(noise_txn)

        return mutated

    @staticmethod
    def mimic_legitimate(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make transactions look like normal behavior.
        - Lower amounts to normal ranges
        - Change transaction types to mundane ones
        - Use regular-looking timing
        """
        legitimate_types = ["debit_purchase", "bill_payment", "pos_transaction"]
        mutated = []
        for txn in txns:
            t = deepcopy(txn)
            # Reduce amount to look normal
            if t.get("amount", 0) > 2000:
                t["amount"] = round(random.uniform(50, 800), 2)
            t["transaction_type"] = random.choice(legitimate_types)
            # Normal business hours
            try:
                ts = datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00"))
                normal_hour = random.randint(9, 17)
                ts = ts.replace(hour=normal_hour, minute=random.randint(0, 59))
                t["timestamp"] = ts.isoformat() + "Z"
            except Exception:
                pass
            t["mutation_applied"] = "mimic_legitimate"
            mutated.append(t)
        return mutated

    @staticmethod
    def randomize_timing(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Randomize inter-transaction timing.
        Evades velocity pattern detection.
        """
        mutated = []
        base_ts = datetime.utcnow()
        for i, txn in enumerate(txns):
            t = deepcopy(txn)
            jitter = random.uniform(-3600, 3600)
            new_ts = base_ts + timedelta(seconds=i * random.randint(60, 7200) + jitter)
            t["timestamp"] = new_ts.isoformat() + "Z"
            t["mutation_applied"] = "randomize_timing"
            mutated.append(t)
        return mutated

    @staticmethod
    def alter_topology(
        txns: List[Dict[str, Any]],
        account_pool_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Insert intermediary accounts to alter graph structure.
        A→B becomes A→X→Y→B.
        Evades direct path detection and cycle detection.
        """
        if not account_pool_ids:
            account_pool_ids = [f"acc_{uuid4().hex[:10]}" for _ in range(30)]

        mutated = []
        for txn in txns:
            if random.random() < 0.5:
                # Insert 1–2 intermediary hops
                hops = random.randint(1, 2)
                intermediaries = [random.choice(account_pool_ids) for _ in range(hops)]
                chain = [txn["sender_account"]] + intermediaries + [txn["receiver_account"]]
                amount = txn.get("amount", 100)
                ts = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))

                for j in range(len(chain) - 1):
                    t = deepcopy(txn)
                    t["transaction_id"] = f"txn_{uuid4().hex[:14]}"
                    t["sender_account"] = chain[j]
                    t["receiver_account"] = chain[j + 1]
                    t["amount"] = round(amount * (0.98 ** j), 2)  # skim
                    t["timestamp"] = (ts + timedelta(seconds=j * random.randint(60, 1800))).isoformat() + "Z"
                    t["mutation_applied"] = "alter_topology"
                    mutated.append(t)
            else:
                mutated.append(txn)

        return mutated

    @staticmethod
    def insert_low_risk_padding(
        txns: List[Dict[str, Any]],
        padding_ratio: float = 0.4,
        account_pool_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pad with benign-looking low-risk transactions.
        Dilutes suspicious signals in detection windows.
        """
        if not account_pool_ids:
            account_pool_ids = [f"acc_{uuid4().hex[:10]}" for _ in range(20)]

        mutated = list(deepcopy(txns))
        pad_count = max(1, int(len(txns) * padding_ratio))

        for _ in range(pad_count):
            base = random.choice(txns)
            ts = datetime.fromisoformat(base["timestamp"].replace("Z", "+00:00"))
            pad = {
                "transaction_id": f"txn_{uuid4().hex[:14]}",
                "sender_account": random.choice(account_pool_ids),
                "receiver_account": random.choice(account_pool_ids),
                "amount": round(random.uniform(10, 200), 2),
                "timestamp": (ts + timedelta(seconds=random.randint(-1800, 1800))).isoformat() + "Z",
                "device_id": f"mob_{uuid4().hex[:8]}",
                "ip_address": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
                "geo_location": random.choice(GEO_LOCATIONS),
                "transaction_type": "debit_purchase",
                "attack_type": "padding",
                "simulation_id": base.get("simulation_id", ""),
                "mutation_generation": base.get("mutation_generation", 0),
                "mutation_applied": "insert_low_risk_padding",
                "_simulation": True,
            }
            mutated.append(pad)

        return mutated
