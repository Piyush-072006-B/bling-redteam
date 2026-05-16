# ============================================================
# Fraud Pattern Implementations — Generator
# ============================================================
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from account_pool import AccountPool

logger = logging.getLogger(__name__)

# Load attack profiles config
import os
_config_path = os.environ.get(
    "ATTACK_PROFILES_PATH",
    "/app/configs/attack_profiles.json"
)
# Fallback for local dev
if not os.path.exists(_config_path):
    _config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "attack_profiles.json")

with open(_config_path) as f:
    _PROFILES = json.load(f)

TRANSACTION_TYPES = _PROFILES["transaction_types"]
GEO_LOCATIONS = _PROFILES["geo_locations"]
DEVICE_PREFIXES = _PROFILES["device_prefixes"]
IP_RANGES = _PROFILES["ip_ranges"]


def _make_txn(
    sender_id: str,
    receiver_id: str,
    amount: float,
    attack_type: str,
    simulation_id: str,
    mutation_generation: int = 0,
    timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    ts = timestamp or datetime.utcnow()
    prefix = random.choice(DEVICE_PREFIXES)
    ip_base = random.choice(IP_RANGES)
    return {
        "transaction_id": f"txn_{uuid4().hex[:14]}",
        "sender_account": sender_id,
        "receiver_account": receiver_id,
        "amount": round(amount, 2),
        "timestamp": ts.isoformat() + "Z",
        "device_id": f"{prefix}_{uuid4().hex[:8]}",
        "ip_address": f"{ip_base}.{random.randint(1, 254)}.{random.randint(1, 254)}",
        "geo_location": random.choice(GEO_LOCATIONS),
        "transaction_type": random.choice(TRANSACTION_TYPES),
        "attack_type": attack_type,
        "simulation_id": simulation_id,
        "mutation_generation": mutation_generation,
        "_simulation": True,
    }


class FraudPatternGenerator:
    """
    Generates synthetic transaction sequences for all 7 fraud patterns.
    Each method returns a list of transaction dicts.
    """

    def __init__(self, account_pool: AccountPool):
        self.pool = account_pool

    def generate(
        self,
        attack_type: str,
        simulation_id: str,
        depth: int = 6,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        generators = {
            "layering_chain": self.layering_chain,
            "round_trip": self.round_trip,
            "mule_network": self.mule_network,
            "structuring": self.structuring,
            "dormant_activation": self.dormant_activation,
            "velocity_attack": self.velocity_attack,
            "fan_in_fan_out": self.fan_in_fan_out,
        }
        fn = generators.get(attack_type)
        if not fn:
            logger.warning(f"Unknown attack type {attack_type}, defaulting to layering_chain")
            fn = self.layering_chain

        txns = fn(simulation_id=simulation_id, depth=depth, mutation_generation=mutation_generation)
        logger.info(
            f"Generated {len(txns)} transactions",
            extra={
                "attack_type": attack_type,
                "simulation_id": simulation_id,
                "mutation_generation": mutation_generation,
            },
        )
        return txns

    def layering_chain(
        self,
        simulation_id: str,
        depth: int = 6,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """A → B → C → D → ... sequential layering"""
        chain_ids = self.pool.sample_ids(max(depth + 1, 3))
        profile = _PROFILES["attack_profiles"]["layering_chain"]
        txns = []
        ts = datetime.utcnow()

        for i in range(len(chain_ids) - 1):
            amount = random.uniform(*profile["amount_range"])
            amount *= (0.95 - i * 0.02)  # skimming at each hop
            gap = random.randint(60, profile["time_spread_seconds"] // depth)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(
                    chain_ids[i],
                    chain_ids[i + 1],
                    max(amount, 100),
                    "layering_chain",
                    simulation_id,
                    mutation_generation,
                    ts,
                )
            )
        return txns

    def round_trip(
        self,
        simulation_id: str,
        depth: int = 4,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """A → B → C → A cyclic flow"""
        n = max(3, min(depth, 8))
        node_ids = self.pool.sample_ids(n)
        profile = _PROFILES["attack_profiles"]["round_trip"]
        txns = []
        ts = datetime.utcnow()

        cycle = node_ids + [node_ids[0]]  # close the loop
        for i in range(len(cycle) - 1):
            amount = random.uniform(*profile["amount_range"])
            gap = random.randint(120, profile["time_spread_seconds"] // n)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(
                    cycle[i],
                    cycle[i + 1],
                    amount,
                    "round_trip",
                    simulation_id,
                    mutation_generation,
                    ts,
                )
            )
        return txns

    def mule_network(
        self,
        simulation_id: str,
        depth: int = 6,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """Hub disperses to mule accounts, mules aggregate elsewhere"""
        profile = _PROFILES["attack_profiles"]["mule_network"]
        hub = self.pool.get_random()
        mules = self.pool.get_mule_accounts(random.randint(*profile["mule_count_range"]))
        if not mules:
            mules = [self.pool.get_random() for _ in range(5)]

        sink = self.pool.get_random(exclude=[hub["account_id"]])
        txns = []
        ts = datetime.utcnow()

        for mule in mules:
            amount = random.uniform(*profile["amount_range"])
            gap = random.randint(30, 600)
            ts += timedelta(seconds=gap)
            # hub → mule
            txns.append(
                _make_txn(hub["account_id"], mule["account_id"], amount, "mule_network",
                          simulation_id, mutation_generation, ts)
            )
            # mule → sink (with delay)
            ts += timedelta(seconds=random.randint(300, 3600))
            txns.append(
                _make_txn(mule["account_id"], sink["account_id"], amount * 0.95, "mule_network",
                          simulation_id, mutation_generation, ts)
            )
        return txns

    def structuring(
        self,
        simulation_id: str,
        depth: int = 10,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """Break large amount into sub-threshold chunks (smurfing)"""
        profile = _PROFILES["attack_profiles"]["structuring"]
        threshold = profile["threshold"]
        source = self.pool.get_random()
        sinks = self.pool.sample_ids(random.randint(2, 5))
        txns = []
        ts = datetime.utcnow()
        count = random.randint(*profile["repeat_count_range"])

        for i in range(count):
            amount = random.uniform(*profile["chunk_range"])  # always below threshold
            sink_id = random.choice(sinks)
            gap = random.randint(1800, profile["time_spread_seconds"] // count)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(source["account_id"], sink_id, amount, "structuring",
                          simulation_id, mutation_generation, ts)
            )
        return txns

    def dormant_activation(
        self,
        simulation_id: str,
        depth: int = 5,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """Dormant account suddenly activates with burst of transactions"""
        profile = _PROFILES["attack_profiles"]["dormant_activation"]
        dormants = self.pool.get_dormant_accounts(1)
        if not dormants:
            dormants = [self.pool.get_random()]
        dormant = dormants[0]

        burst_count = random.randint(*profile["burst_transactions"])
        sinks = self.pool.sample_ids(burst_count)
        txns = []
        ts = datetime.utcnow()

        for sink_id in sinks[:burst_count]:
            amount = random.uniform(*profile["amount_range"])
            gap = random.randint(30, 900)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(dormant["account_id"], sink_id, amount, "dormant_activation",
                          simulation_id, mutation_generation, ts)
            )
        return txns

    def velocity_attack(
        self,
        simulation_id: str,
        depth: int = 20,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """Rapid-fire transactions in short time window"""
        profile = _PROFILES["attack_profiles"]["velocity_attack"]
        source = self.pool.get_random()
        count = random.randint(*profile["transaction_count_range"])
        window = profile["time_window_seconds"]
        txns = []
        ts = datetime.utcnow()

        for _ in range(count):
            amount = random.uniform(*profile["amount_range"])
            sink = self.pool.get_random(exclude=[source["account_id"]])
            gap = random.uniform(1, window / count)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(source["account_id"], sink["account_id"], amount, "velocity_attack",
                          simulation_id, mutation_generation, ts)
            )
        return txns

    def fan_in_fan_out(
        self,
        simulation_id: str,
        depth: int = 6,
        mutation_generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """Many sources → aggregator → many sinks"""
        profile = _PROFILES["attack_profiles"]["fan_in_fan_out"]
        src_count = random.randint(*profile["source_count_range"])
        sink_count = random.randint(*profile["sink_count_range"])
        sources = self.pool.sample_ids(src_count)
        aggregator = self.pool.get_random(exclude=sources)
        sinks = self.pool.sample_ids(sink_count)
        txns = []
        ts = datetime.utcnow()

        # Fan-in: sources → aggregator
        total = 0.0
        for src_id in sources:
            amount = random.uniform(*profile["amount_range"])
            total += amount
            gap = random.randint(60, 600)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(src_id, aggregator["account_id"], amount, "fan_in_fan_out",
                          simulation_id, mutation_generation, ts)
            )

        # Fan-out: aggregator → sinks
        ts += timedelta(seconds=random.randint(300, 3600))
        per_sink = total / len(sinks)
        for sink_id in sinks:
            amount = per_sink * random.uniform(0.8, 1.2)
            gap = random.randint(30, 300)
            ts += timedelta(seconds=gap)
            txns.append(
                _make_txn(aggregator["account_id"], sink_id, amount, "fan_in_fan_out",
                          simulation_id, mutation_generation, ts)
            )
        return txns
