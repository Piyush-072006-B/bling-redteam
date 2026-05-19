# ============================================================================
# canonical_exporter.py
# Red Team AML Graph Engine — Standardized Canonical Exporter
# ============================================================================

import os
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Union

# Resolve workspace root dynamically to avoid hardcoding issues across different environments/drives
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)

if os.path.exists("/app/evidence"):
    EXPORT_DIR = "/app/evidence/evasion_exports"
else:
    EXPORT_DIR = os.path.join(workspace_root, "evidence", "evasion_exports")

def normalize_graph_for_export(graph_state: Any) -> List[Dict[str, Any]]:
    """
    Dedicated normalization layer to convert any graph representation, legacy
    wrapper, or nested structure into a flat array of standardized transaction objects.
    """
    transactions = []
    
    # Helper to parse and format timestamp
    def clean_timestamp(ts: Any) -> str:
        if not ts:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%dT%H:%M:%S")
        ts_str = str(ts)
        # Handle ISO strings
        if "Z" in ts_str:
            ts_str = ts_str.replace("Z", "")
        if "+" in ts_str:
            ts_str = ts_str.split("+")[0]
        if "." in ts_str:
            ts_str = ts_str.split(".")[0]
        # Basic validation check
        try:
            datetime.fromisoformat(ts_str)
            return ts_str
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {ts}. Must be a valid ISO timestamp.")

    # Helper to parse amount
    def clean_amount(amt: Any) -> int:
        try:
            val = float(amt)
            if val < 0:
                raise ValueError("Amount cannot be negative")
            return int(val)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount value: {amt}")

    # Case 1: NetworkX DiGraph
    if "DiGraph" in str(type(graph_state)):
        try:
            import networkx as nx
            for u, v, data in graph_state.edges(data=True):
                transactions.append({
                    "from_account": str(u),
                    "to_account": str(v),
                    "amount": clean_amount(data.get("amount", data.get("weight", 100))),
                    "payment_rail": str(data.get("payment_rail", data.get("transaction_type", "NEFT"))),
                    "timestamp": clean_timestamp(data.get("timestamp"))
                })
        except ImportError:
            raise ImportError("NetworkX is required to export a DiGraph object.")
            
    # Case 2: List (Flat array of dicts or edges)
    elif isinstance(graph_state, list):
        for item in graph_state:
            if isinstance(item, dict):
                # Check for nested structures or alternate keys
                if any(k in item for k in ["from_account", "sender_account", "source", "node_from"]):
                    from_acc = item.get("from_account", item.get("sender_account", item.get("sender_id", item.get("source", item.get("node_from")))))
                    to_acc = item.get("to_account", item.get("receiver_account", item.get("receiver_id", item.get("target", item.get("node_to")))))
                    amt = item.get("amount", item.get("weight", 0))
                    rail = item.get("payment_rail", item.get("transaction_type", "NEFT"))
                    ts = item.get("timestamp", item.get("captured_at"))
                    
                    transactions.append({
                        "from_account": str(from_acc),
                        "to_account": str(to_acc),
                        "amount": clean_amount(amt),
                        "payment_rail": str(rail),
                        "timestamp": clean_timestamp(ts)
                    })
                else:
                    # Recursive check for any nested key containing transaction list
                    for k, v in item.items():
                        if isinstance(v, (list, dict)):
                            try:
                                transactions.extend(normalize_graph_for_export(v))
                            except Exception:
                                pass
            else:
                raise ValueError("List elements must be dictionaries representing transactions")
                
    # Case 3: Dictionary (Either single transaction, legacy wrapper, or containing list)
    elif isinstance(graph_state, dict):
        # Is it a single transaction?
        if any(k in graph_state for k in ["from_account", "sender_account", "sender_id", "source", "node_from"]):
            from_acc = graph_state.get("from_account", graph_state.get("sender_account", graph_state.get("sender_id", graph_state.get("source", graph_state.get("node_from")))))
            to_acc = graph_state.get("to_account", graph_state.get("receiver_account", graph_state.get("receiver_id", graph_state.get("target", graph_state.get("node_to")))))
            amt = graph_state.get("amount", graph_state.get("weight", 0))
            rail = graph_state.get("payment_rail", graph_state.get("transaction_type", "NEFT"))
            ts = graph_state.get("timestamp", graph_state.get("captured_at"))
            
            transactions.append({
                "from_account": str(from_acc),
                "to_account": str(to_acc),
                "amount": clean_amount(amt),
                "payment_rail": str(rail),
                "timestamp": clean_timestamp(ts)
            })
        else:
            # Check popular subkeys like pattern_data, topology_payload, exported_topology_variations, transactions, etc.
            subkeys = ["pattern_data", "topology_payload", "exported_topology_variations", "transactions", "payload"]
            found_subkey = False
            for sk in subkeys:
                if sk in graph_state and graph_state[sk]:
                    transactions.extend(normalize_graph_for_export(graph_state[sk]))
                    found_subkey = True
            
            # If no obvious subkey, search all dictionary values recursively
            if not found_subkey:
                for k, v in graph_state.items():
                    if isinstance(v, (list, dict)):
                        try:
                            transactions.extend(normalize_graph_for_export(v))
                        except Exception:
                            pass
                            
    else:
        raise ValueError(f"Unsupported graph state type: {type(graph_state)}")
        
    # Enforce deterministic ordering: sort by timestamp, from_account, to_account, amount
    transactions.sort(key=lambda x: (x["timestamp"], x["from_account"], x["to_account"], x["amount"]))
    
    return transactions

def validate_schema(transactions: List[Dict[str, Any]]) -> None:
    """
    Schema validation safeguard:
    - reject malformed transactions
    - reject missing keys
    - reject nested graph structures
    - reject non-ISO timestamps (must strictly match YYYY-MM-DDTHH:MM:SS)
    - strict Topological Density Controls and Structural Connectivity Safeguards:
        - NEVER emit or save a pattern that contains fewer than 2 interconnected transaction edges.
        - Every exported pattern MUST contain a meaningful money-laundering topology involving at least 3 unique account entities.
        - The transaction array MUST be topologically linked (at least one intermediary hop).
        - Refuse to save/export if the intersection of all senders and all receivers is empty.
    """
    if not isinstance(transactions, list):
        raise ValueError("Transactions must be a list")
        
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
    
    # ─── Strict Topological Density and Structural Connectivity Safeguards ───
    # Rule 1: Minimum 2 transaction edges
    if len(transactions) < 2:
        raise ValueError(
            f"Topological Density Control: Transaction array has {len(transactions)} edge(s). "
            f"NEVER emit or save a pattern that contains fewer than 2 interconnected transaction edges."
        )

    # Validate individual transactions and gather accounts
    senders = set()
    receivers = set()
    
    for idx, txn in enumerate(transactions):
        if not isinstance(txn, dict):
            raise ValueError(f"Transaction at index {idx} is not a dictionary")
            
        # Reject extra keys or missing keys
        expected_keys = {"from_account", "to_account", "amount", "payment_rail", "timestamp"}
        actual_keys = set(txn.keys())
        if actual_keys != expected_keys:
            raise ValueError(f"Transaction at index {idx} keys {actual_keys} do not match expected {expected_keys}")
            
        # Validate values
        if not isinstance(txn["from_account"], str) or not txn["from_account"]:
            raise ValueError(f"Transaction at index {idx} has invalid 'from_account': must be non-empty string")
        if not isinstance(txn["to_account"], str) or not txn["to_account"]:
            raise ValueError(f"Transaction at index {idx} has invalid 'to_account': must be non-empty string")
            
        # Avoid nested structures in accounts
        if any(char in txn["from_account"] for char in ["{", "}", "[", "]", ":"]):
            raise ValueError(f"Transaction at index {idx} has nested or invalid structure in 'from_account'")
        if any(char in txn["to_account"] for char in ["{", "}", "[", "]", ":"]):
            raise ValueError(f"Transaction at index {idx} has nested or invalid structure in 'to_account'")
            
        if not isinstance(txn["amount"], int) or txn["amount"] < 0:
            raise ValueError(f"Transaction at index {idx} has invalid 'amount': must be non-negative integer")
        if not isinstance(txn["payment_rail"], str) or not txn["payment_rail"]:
            raise ValueError(f"Transaction at index {idx} has invalid 'payment_rail': must be non-empty string")
            
        # Check ISO timestamp format: YYYY-MM-DDTHH:MM:SS
        if not isinstance(txn["timestamp"], str) or not iso_pattern.match(txn["timestamp"]):
            raise ValueError(f"Transaction at index {idx} has invalid 'timestamp': {txn['timestamp']}. Must strictly match ISO format YYYY-MM-DDTHH:MM:SS")
            
        senders.add(txn["from_account"])
        receivers.add(txn["to_account"])

    # Rule 2: Minimum 3 unique account entities
    unique_accounts = senders.union(receivers)
    if len(unique_accounts) < 3:
        raise ValueError(
            f"Topological Density Control: Graph contains {len(unique_accounts)} unique account entity/entities. "
            f"Every exported pattern MUST contain a meaningful money-laundering topology involving at least 3 unique account entities."
        )

    # Rule 3 & 4: Topologically linked / Non-empty intersection of senders and receivers (Intermediary hops)
    intersection = senders.intersection(receivers)
    if not intersection:
        raise ValueError(
            "Structural Connectivity Safeguard: The intersection of all sender accounts and all receiver accounts is empty. "
            "The generated transaction array must be topologically linked (at least one intermediary hop ACC_A -> ACC_B -> ACC_C)."
        )

def export_pattern(transactions: Any, filename: str) -> str:
    """
    Single export manager:
    - normalize input if needed
    - validate schema before writing (rejects malformed/nested data)
    - auto-create export directory if missing
    - overwrite invalid legacy formats
    - save only clean canonical JSON (pretty-printed with indent=2)
    """
    normalized = normalize_graph_for_export(transactions)
    validate_schema(normalized)
    
    # Determine full filepath
    os.makedirs(EXPORT_DIR, exist_ok=True)
    if not os.path.isabs(filename):
        filename = os.path.basename(filename)
        filepath = os.path.join(EXPORT_DIR, filename)
    else:
        filepath = filename
        # Ensure it is in the target directory
        if not filepath.startswith(EXPORT_DIR):
            filename = os.path.basename(filepath)
            filepath = os.path.join(EXPORT_DIR, filename)
            
    with open(filepath, "w") as f:
        json.dump(normalized, f, indent=2)
        
    return filepath
