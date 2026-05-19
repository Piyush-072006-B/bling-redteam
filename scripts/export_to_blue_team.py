import os
import sys
import json
import urllib.request
from datetime import datetime

# Resolve sys.path for redteam import
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(current_dir)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from redteam.canonical_exporter import export_pattern

# Configuration
ESCAPE_ANALYZER_URL = "http://localhost:8005"
EXPORT_DIR = os.path.join(workspace_root, "evidence", "evasion_exports")

def fetch_and_save_evasions():
    print(f"[*] Fetching latest successful evasions from Escape Analyzer API...")
    url = f"{ESCAPE_ANALYZER_URL}/export/evasions?limit=100"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"[!] Error connecting to API: {e}")
        print("    Ensure the Sandbox backend (Escape Analyzer) is running.")
        return

    variations = data.get("exported_topology_variations", [])
    if not variations:
        print("[-] No new evasive patterns found. Run the Orchestrator to generate more.")
        return

    print(f"[*] Found {len(variations)} novel evasive patterns. Saving to {EXPORT_DIR}...")
    
    saved_count = 0
    for pattern in variations:
        sim_id = pattern.get("simulation_id", "unknown")
        topo_type = pattern.get("topology_type", "unknown")
        generation = pattern.get("mutation_generation", 0)
        
        filename = f"evasion_{topo_type}_gen{generation}_{sim_id}.json"
        payload = pattern.get("topology_payload", {})
        
        try:
            export_pattern(payload, filename)
            saved_count += 1
        except Exception as e:
            print(f"[!] Schema validation failed for pattern {filename}: {e}")

    print(f"[+] Successfully saved {saved_count} evasion patterns for the Blue Team.")

if __name__ == "__main__":
    fetch_and_save_evasions()

