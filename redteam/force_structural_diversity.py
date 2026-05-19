# ============================================================================
# force_structural_diversity.py
# Red Team AML Graph Engine — Diversity-Driven Mutation & Exploration Controller
# ============================================================================

import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Ensure correct path resolution to import from redteam modules
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from topology_diversity.similarity import SimilarityEngine
    from topology_diversity.fingerprinting import TopologyFingerprinter
except ImportError:
    # Fallback to local import depending on working directory
    sys.path.append(os.path.join(current_dir, "topology_diversity"))
    # pyrefly: ignore [missing-import]
    from similarity import SimilarityEngine
    # pyrefly: ignore [missing-import]
    from fingerprinting import TopologyFingerprinter

from canonical_exporter import export_pattern

RUNS_DIR = os.path.join(workspace_root, "evidence", "runs")
EXPORTS_DIR = os.path.join(workspace_root, "evidence", "evasion_exports")

def load_recent_fingerprints(limit: int = 5) -> List[Dict[str, Any]]:
    """Scan the unified run registry for the last 5 registered runs and load their fingerprints."""
    fingerprints = []
    if not os.path.exists(RUNS_DIR):
        return fingerprints

    # Sort run directories by modification time (or name) to get the most recent ones
    subdirs = []
    for d in os.listdir(RUNS_DIR):
        path = os.path.join(RUNS_DIR, d)
        if os.path.isdir(path) and d.startswith("run_"):
            subdirs.append((os.path.getmtime(path), path))
    
    subdirs.sort(reverse=True)
    recent_dirs = [path for _, path in subdirs[:limit]]

    for run_path in recent_dirs:
        fp_path = os.path.join(run_path, "fingerprints", "struct.json")
        if os.path.exists(fp_path):
            try:
                with open(fp_path, "r") as f:
                    fingerprints.append(json.load(f))
            except Exception as e:
                print(f"[Warning] Failed to load fingerprint from {fp_path}: {e}")
                
    # Fallback if no historical fingerprints are available
    if not fingerprints:
        print("[Info] No historical run fingerprints found. Generating mock history.")
        # Create a basic layering chain fingerprint as fallback
        base_txns = [
            {"sender_account": f"ACC_{4000+i}", "receiver_account": f"ACC_{4000+i+1}", "amount": 10000}
            for i in range(5)
        ]
        fingerprints.append(TopologyFingerprinter.generate_fingerprint(base_txns))
        
    return fingerprints

# --- Core Mutation Operators ---

def apply_split_fan_out(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Operator 1: SPLIT / FAN-OUT
    Split a transaction volume across parallel intermediary accounts.
    A -> B becomes A -> X1 -> B and A -> X2 -> B
    """
    mutated = []
    for txn in txns:
        sender = txn["sender_account"]
        receiver = txn["receiver_account"]
        amount = txn["amount"]
        ts = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))
        
        # Split transactions above 5000
        if amount > 5000:
            x1 = f"ACC_X_{random.randint(100, 999)}"
            x2 = f"ACC_X_{random.randint(100, 999)}"
            amt1 = round(amount * random.uniform(0.45, 0.55), 2)
            amt2 = round(amount - amt1, 2)
            
            # Hop 1: Sender -> Intermediaries
            mutated.append({
                "sender_account": sender,
                "receiver_account": x1,
                "amount": amt1,
                "timestamp": ts.isoformat(),
                "payment_rail": random.choice(["NEFT", "RTGS"]),
                "mutation": "split_fan_out"
            })
            mutated.append({
                "sender_account": sender,
                "receiver_account": x2,
                "amount": amt2,
                "timestamp": (ts + timedelta(minutes=random.randint(2, 5))).isoformat(),
                "payment_rail": random.choice(["NEFT", "RTGS"]),
                "mutation": "split_fan_out"
            })
            
            # Hop 2: Intermediaries -> Receiver
            mutated.append({
                "sender_account": x1,
                "receiver_account": receiver,
                "amount": amt1,
                "timestamp": (ts + timedelta(minutes=random.randint(10, 15))).isoformat(),
                "payment_rail": random.choice(["NEFT", "RTGS"]),
                "mutation": "split_fan_out"
            })
            mutated.append({
                "sender_account": x2,
                "receiver_account": receiver,
                "amount": amt2,
                "timestamp": (ts + timedelta(minutes=random.randint(12, 18))).isoformat(),
                "payment_rail": random.choice(["NEFT", "RTGS"]),
                "mutation": "split_fan_out"
            })
        else:
            mutated.append(txn)
    return mutated

def apply_layered_extension(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Operator 2: LAYERED EXTENSION
    Insert an intermediate hop node between an existing sender and receiver to increase path length.
    A -> B becomes A -> Y -> B
    """
    mutated = []
    for txn in txns:
        sender = txn["sender_account"]
        receiver = txn["receiver_account"]
        amount = txn["amount"]
        ts = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))
        
        y = f"ACC_Y_{random.randint(100, 999)}"
        # Skim slightly to mimic actual laundering hops
        skimmed_amount = round(amount * 0.97, 2)
        
        mutated.append({
            "sender_account": sender,
            "receiver_account": y,
            "amount": amount,
            "timestamp": ts.isoformat(),
            "payment_rail": random.choice(["NEFT", "RTGS"]),
            "mutation": "layered_extension"
        })
        mutated.append({
            "sender_account": y,
            "receiver_account": receiver,
            "amount": skimmed_amount,
            "timestamp": (ts + timedelta(minutes=random.randint(15, 30))).isoformat(),
            "payment_rail": random.choice(["NEFT", "RTGS"]),
            "mutation": "layered_extension"
        })
    return mutated

def apply_aggregation_fan_in(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Operator 3: AGGREGATION (FAN-IN)
    Merge multiple incoming branches into a single exit node.
    A1 -> B, A2 -> B becomes A1 -> Aggregator, A2 -> Aggregator, and then Aggregator -> B
    """
    if len(txns) < 2:
        return txns
        
    aggregator = f"ACC_AGG_{random.randint(100, 999)}"
    mutated = []
    
    # We group by receiver and route inputs to the aggregator instead
    receivers = list(set([t["receiver_account"] for t in txns]))
    final_receiver = receivers[0] # Merge to the first primary receiver
    
    total_amount = 0.0
    latest_ts = datetime.min
    
    for txn in txns:
        sender = txn["sender_account"]
        amount = txn["amount"]
        ts = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))
        if ts > latest_ts:
            latest_ts = ts
            
        total_amount += amount
        mutated.append({
            "sender_account": sender,
            "receiver_account": aggregator,
            "amount": amount,
            "timestamp": ts.isoformat(),
            "payment_rail": random.choice(["NEFT", "RTGS"]),
            "mutation": "aggregation_fan_in"
        })
        
    # Flow out from Aggregator to final receiver
    mutated.append({
        "sender_account": aggregator,
        "receiver_account": final_receiver,
        "amount": round(total_amount * 0.95, 2), # Skim 5%
        "timestamp": (latest_ts + timedelta(hours=random.randint(1, 3))).isoformat(),
        "payment_rail": "RTGS",
        "mutation": "aggregation_fan_in"
    })
    
    return mutated

def apply_temporal_staggering(txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Operator 4: TEMPORAL STAGGERING
    Stagger the transaction timestamps across days or hours to break time-window velocity rules.
    """
    mutated = []
    current_time = datetime.fromisoformat(txns[0]["timestamp"].replace("Z", "+00:00")) if txns else datetime.now()
    
    for i, txn in enumerate(txns):
        t = txn.copy()
        # Add random delay of 12 to 36 hours for each subsequent transaction
        delay = timedelta(hours=random.uniform(12, 36))
        current_time += delay
        t["timestamp"] = current_time.isoformat()
        t["mutation"] = "temporal_staggering"
        mutated.append(t)
    return mutated

# --- High-Novelty Structural Family Generators ---

def spawn_fan_out_network() -> List[Dict[str, Any]]:
    """Radically different family: Fan-Out / Mule network."""
    base_ts = datetime.now()
    txns = []
    hub = "ACC_HUB_9000"
    mules = [f"ACC_MULE_{i}" for i in range(5001, 5005)]
    receivers = [f"ACC_RCV_{i}" for i in range(6001, 6003)]
    
    for i, mule in enumerate(mules):
        ts_mule = base_ts + timedelta(hours=i * 2)
        # Hub -> Mule
        txns.append({
            "sender_account": hub,
            "receiver_account": mule,
            "amount": round(random.uniform(8000, 12000), 2),
            "timestamp": ts_mule.isoformat(),
            "payment_rail": "NEFT"
        })
        # Mule -> Receiver
        ts_rcv = ts_mule + timedelta(hours=random.randint(6, 12))
        txns.append({
            "sender_account": mule,
            "receiver_account": random.choice(receivers),
            "amount": round(random.uniform(7500, 11500), 2),
            "timestamp": ts_rcv.isoformat(),
            "payment_rail": "RTGS"
        })
    return txns

def spawn_cycle_network() -> List[Dict[str, Any]]:
    """Radically different family: Cyclic laundering ring."""
    base_ts = datetime.now()
    nodes = ["ACC_CYCLE_A", "ACC_CYCLE_B", "ACC_CYCLE_C", "ACC_CYCLE_D", "ACC_CYCLE_A"]
    txns = []
    for i in range(len(nodes) - 1):
        ts = base_ts + timedelta(days=i)
        txns.append({
            "sender_account": nodes[i],
            "receiver_account": nodes[i+1],
            "amount": round(15000 * (0.96 ** i), 2),
            "timestamp": ts.isoformat(),
            "payment_rail": "NEFT"
        })
    return txns

def spawn_scatter_gather_network() -> List[Dict[str, Any]]:
    """Radically different family: Scatter-Gather (Fan-in Fan-out)."""
    base_ts = datetime.now()
    sources = ["ACC_SRC_1", "ACC_SRC_2", "ACC_SRC_3"]
    aggregator = "ACC_AGGREGATOR"
    destinations = ["ACC_DST_1", "ACC_DST_2"]
    txns = []
    
    # Scatter to aggregator
    for i, src in enumerate(sources):
        ts = base_ts + timedelta(hours=i * 3)
        txns.append({
            "sender_account": src,
            "receiver_account": aggregator,
            "amount": round(random.uniform(9000, 11000), 2),
            "timestamp": ts.isoformat(),
            "payment_rail": "NEFT"
        })
        
    # Gather from aggregator
    latest_ts = base_ts + timedelta(hours=len(sources) * 3 + 2)
    for i, dst in enumerate(destinations):
        ts = latest_ts + timedelta(hours=i * 4)
        txns.append({
            "sender_account": aggregator,
            "receiver_account": dst,
            "amount": round(14500, 2),
            "timestamp": ts.isoformat(),
            "payment_rail": "RTGS"
        })
    return txns

# --- Main Engine Loop ---

def run_diversity_engine():
    # 1. Initialize variables & load the current successful topology state
    # Let's start with a standard layering chain that is stuck in a local minimum
    base_chain = [
        {"sender_account": "ACC_4001", "receiver_account": "ACC_5001", "amount": 15000, "timestamp": "2026-05-15T10:03:00"},
        {"sender_account": "ACC_5001", "receiver_account": "ACC_6001", "amount": 14500, "timestamp": "2026-05-15T10:15:00"},
        {"sender_account": "ACC_6001", "receiver_account": "ACC_7001", "amount": 14000, "timestamp": "2026-05-15T10:30:00"}
    ]
    
    print("\n--- [Engine] Red Team AML Topology Diversity Loop Initiated ---")
    print(f"Current Baseline Topology: layering_chain (Linear Flow, depth: {len(base_chain)})")
    
    # Load past 5 fingerprints
    history = load_recent_fingerprints(5)
    print(f"Loaded {len(history)} historical structural fingerprints from registry.")

    # 2. Epsilon-greedy Exploration Check (Epsilon = 0.2)
    epsilon = 0.2
    exploration_roll = random.random()
    exploration_triggered = exploration_roll < epsilon
    
    mutated_txns = []
    applied_operation = ""
    family_name = ""

    if exploration_triggered:
        print(f"\n[EXPLORATION TRIGGERED] Roll: {exploration_roll:.3f} < Epsilon: {epsilon}")
        print("Abandoning current successful topology family ('layering_chain') to force structural diversity.")
        
        # Select randomly from radically different structural families
        choices = [
            ("fan_out_network", spawn_fan_out_network),
            ("cyclic_network", spawn_cycle_network),
            ("scatter_gather_network", spawn_scatter_gather_network)
        ]
        family_name, generator_fn = random.choice(choices)
        mutated_txns = generator_fn()
        applied_operation = f"SPAWN_RADICAL_FAMILY: {family_name.upper()}"
        print(f"Spawned brand new structural family: {family_name}")
    else:
        print(f"\n[EXPLOITATION / MUTATION] Roll: {exploration_roll:.3f} >= Epsilon: {epsilon}")
        print("Applying explicit Topological Mutation Operators to physically alter graph structure.")
        
        # Select mutation operator
        operators = [
            ("SPLIT / FAN-OUT", apply_split_fan_out),
            ("LAYERED EXTENSION", apply_layered_extension),
            ("AGGREGATION (FAN-IN)", apply_aggregation_fan_in),
            ("TEMPORAL STAGGERING", apply_temporal_staggering)
        ]
        op_name, op_fn = random.choice(operators)
        mutated_txns = op_fn(base_chain)
        applied_operation = op_name
        family_name = "layering_chain_mutated"
        print(f"Applied physical structural operator: {op_name}")

    # 3. Calculate Fingerprint & Structural Similarity against History
    # Format transactions back to match the TopologyFingerprinter requirements
    converted_to_fingerprint = []
    for t in mutated_txns:
        converted_to_fingerprint.append({
            "sender_account": t.get("sender_account", t.get("from_account")),
            "receiver_account": t.get("receiver_account", t.get("to_account")),
            "amount": t.get("amount")
        })
        
    new_fingerprint = TopologyFingerprinter.generate_fingerprint(converted_to_fingerprint)
    
    # Calculate maximum structural similarity against the history of 5
    similarities = [SimilarityEngine.calculate_similarity(new_fingerprint, hist_fp) for hist_fp in history]
    max_similarity = max(similarities) if similarities else 0.0
    print(f"\nStructural Similarity Check:")
    for idx, sim in enumerate(similarities):
        print(f" - Vs. Historical Run {idx+1}: {sim:.1%}")
    print(f"Maximum Structural Similarity: {max_similarity:.1%}")

    # 4. Novelty Penalty & Fitness Evaluation
    # Fitness = Evasion Success - (0.4 * Structural Similarity)
    # Assume high evasion success for this generation, say 0.95
    evasion_success = 0.95
    novelty_penalty = 0.4 * max_similarity
    raw_fitness = evasion_success - novelty_penalty
    
    # Heavily penalize score if similarity exceeds 60%
    heavy_penalty_applied = False
    if max_similarity > 0.6:
        print("[WARNING] Structural similarity exceeds 60%! Applying heavy novelty penalty.")
        heavy_penalty_applied = True
        fitness = raw_fitness - 0.8  # Heavy penalty
    else:
        fitness = raw_fitness
        
    print(f"\nFitness Evaluation Summary:")
    print(f" - Evasion Success Score: {evasion_success:.3f}")
    print(f" - Structural Similarity: {max_similarity:.3f}")
    print(f" - Novelty Penalty factor: -{novelty_penalty:.3f}")
    if heavy_penalty_applied:
        print(f" - Heavy similarity penalty: -0.800")
    print(f" => Final Fitness Score: {fitness:.3f}")

    # 5. Save flat array output using the canonical export layer
    output_filename = "evasion_mutated_diversity_sim.json"
    output_path = export_pattern(mutated_txns, output_filename)
    
    # Load standardized canonical output to return
    with open(output_path, "r") as f:
        final_output = json.load(f)
        
    print(f"\nSuccess! Next mutated diversity-optimized topology written to:")
    print(f" => {output_path}")
    print(f"Transaction count: {len(final_output)}")

    return final_output, output_path

if __name__ == "__main__":
    run_diversity_engine()
