import os
import json
import urllib.request
from datetime import datetime

# Configuration
ESCAPE_ANALYZER_URL = "http://localhost:8005"
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence", "evasion_exports")

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
    
    # Ensure export directory exists
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    saved_count = 0
    for pattern in variations:
        sim_id = pattern.get("simulation_id", "unknown")
        topo_type = pattern.get("topology_type", "unknown")
        generation = pattern.get("mutation_generation", 0)
        
        filename = f"evasion_{topo_type}_gen{generation}_{sim_id}.json"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # Add metadata for the Blue Team
        export_payload = {
            "meta": {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "source": "BLING_Adversarial_Sandbox",
                "status": "REQUIRES_HUMAN_VALIDATION",
                "topology_type": topo_type,
                "mutation_generation": generation,
                "simulation_id": sim_id
            },
            "pattern_data": pattern.get("topology_payload", {})
        }
        
        with open(filepath, "w") as f:
            json.dump(export_payload, f, indent=2)
        saved_count += 1

    print(f"[+] Successfully saved {saved_count} evasion patterns for the Blue Team.")

if __name__ == "__main__":
    fetch_and_save_evasions()
