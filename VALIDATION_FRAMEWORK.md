# BLING: Adversarial Sandbox Testing & Validation Framework

This document outlines the complete testing, validation, and observability framework for the **BLING Adversarial Financial Graph Topology Generation Engine**.

> [!IMPORTANT]
> **Research-Grade Positioning**
> This validation framework proves that the system successfully generates, mutates, and evaluates synthetic adversarial graph topologies. It does NOT validate production AML fraud detection or autonomous self-learning AI.

---

## Current Validation Status (2026-05-19)

| Test | Script | Status | Evidence Output |
|---|---|---|---|
| Service Health | `test_01_health_checks.py` | ✅ PASS | All 8 services respond on `/health` |
| Kafka Streams | `test_02_kafka_streams.py` | ✅ PASS | All 4 topics active + receiving messages |
| Topology Generation | `test_03_topology_generation.py` | ✅ PASS | All 7 topology types structurally verified |
| Mutation Validation | `test_04_mutation_validation.py` | ✅ PASS | All 7 perturbation strategies produce diffs |
| E2E Evasion Export | `test_05_e2e_evasion_export.py` | ✅ PASS | 10 evasion scenarios exported as canonical JSON |
| Graph Integrity | `test_06_graph_topology_integrity.py` | ✅ PASS | 6 PNGs in `evidence/graph_snapshots/` |
| Deterministic Replay | `test_07_deterministic_replay.py` | ✅ PASS | Matching hashes in `evidence/replay_runs/` |

**Overall: 7/7 tests passing.** All evidence artifacts committed to repository.

---

## 1. System Validation Plan

The validation suite is designed to sequentially verify the core robustness loop:

1. **Service Health (`test_01`):** Verifies all 8 microservices respond on their `/health` endpoints — Generator (`:8001`), Graph Engine (`:8002`), Eval Harness (`:8003`), Mutator (`:8004`), Escape Analyzer (`:8005`), Control API (`:8081`), Topology Diversity (`:8082`), and Kafka UI (`:8080`).

2. **Kafka Streams (`test_02`):** Validates that `transactions.sandbox`, `graph.updates.sandbox`, `fraud.alerts.sandbox`, and `redteam.metrics` topics are available and actively receiving messages. Asserts non-zero message counts.

3. **Topology Generation (`test_03`):** Submits requests to the Topology Generator for all 7 topology types and verifies the structural output — correct node count for depth, correct edge structure, correct payment rail distribution.

4. **Mutation Application (`test_04`):** Submits a baseline topology to the Topology Mutator for all 7 perturbation strategies and asserts that structural changes actually occur: node insertions for `add_noise_accounts`, timestamp shifts for `delay_transfers`, transaction splits for `split_transaction`, etc.

5. **End-to-End Evasion Export (`test_05`):** Runs 10 complete simulation scenarios, waits for Evaluation Harness processing, and queries the Escape Analyzer to assert that evasive structures are exported as canonical JSON. Validates each export against the canonical schema (field names, types, ISO timestamps, topological connectivity).

6. **Graph Topology Integrity (`test_06`):** Asserts the mathematical properties of generated graphs using NetworkX. Verifies: cycle existence in round-trip topologies, hub out-degree in mule networks, sub-threshold fragmentation in structuring, path depth ≥ requested depth in layering chains, high transaction density in velocity attacks. Saves PNG renders to `evidence/graph_snapshots/`.

7. **Deterministic Replay (`test_07`):** Ensures reproducibility by generating the same topology twice with an identical random seed and asserting that the SHA-256 hash of the serialized transaction list matches exactly. Logs hashes to `evidence/replay_runs/replay_hash.txt`.

---

## 2. Test Data Generation

The system tests across 7 distinct topological patterns. Structural expectations per topology:

| Topology | Structure | Key Assertion |
|---|---|---|
| `layering_chain` | A→B→C→D→... | Longest path ≥ `depth` parameter |
| `round_trip` | A→B→C→A | At least one cycle detected by NetworkX |
| `mule_network` | Hub→[mules]→Sink | Hub node out-degree ≥ `num_mules` |
| `structuring` | Source→N accounts | All transaction amounts < threshold; N ≥ depth |
| `dormant_activation` | Dormant→Burst | Timestamp gap between setup phase and burst phase |
| `velocity_attack` | Source→N (rapid) | Transaction count ≥ depth within short time window |
| `fan_in_fan_out` | N→Hub→M | Hub node: high in-degree AND high out-degree concurrently |

---

## 3. Observability & Graph Metrics

Beyond simple pass/fail assertions, the framework captures advanced graph-centric metrics for every Orchestrator cycle.

### Standard Metrics (per run `summary.json`)
- **`transactions_count`:** Number of transaction edges in the generated graph.
- **`detection_rate`:** Float 0.0–1.0. Percentage of heuristic rules triggered. All exported gen-0 runs achieved `0.0`.
- **`novelty_score`:** Float 0.0–1.0. Structural uniqueness vs. previously seen topologies (from Topology Diversity service).
- **`structural_divergence`:** Float. Magnitude of structural change from parent topology.
- **`topology_family`:** String identifier for the topology class.
- **`branch_id`:** Unique mutation branch identifier.

### Graph Diversity Metrics (per run `fingerprints/struct.json`)
- **`num_nodes` / `num_edges`:** Raw graph size.
- **`density`:** Edge density = edges / (nodes × (nodes-1)).
- **`in_degree_hist` / `out_degree_hist`:** Degree distribution histograms (5 bins).
- **`hub_count`:** Number of nodes with out-degree ≥ 3 (key signal for mule networks).
- **`triad_census`:** Full 16-type triad census (003, 012, 102, 021D, 021U, 021C, 111D, 111U, 030T, 030C, 201, 120D, 120U, 120C, 210, 300).
- **`cycle_signature`:** `{total_cycles, avg_length, max_length}` — key for round-trip detection.
- **`num_components` / `max_component_size`:** Connectivity analysis.
- **`spectral_variance`:** Variance of graph Laplacian eigenvalues — proxy for structural complexity.

### Lineage Tracking (per run `lineage/ancestry.json`)
- **`topology_family`:** Which of the 7 families this run belongs to.
- **`branch_id`:** Unique mutation branch identifier.
- **`parent_run_id`:** Run ID of the parent generation (null for gen-0).
- **`generation`:** Mutation depth counter (0 = original generation).

---

## 4. Sandbox Test Scenarios (test_05)

The `tests/test_05_e2e_evasion_export.py` script drives 10 end-to-end scenarios, each verifying a specific topology + perturbation combination:

1. **Simple Layering Chain evasion via `alter_topology` (intermediary hop insertion).**
2. **Round Trip evasion via `delay_transfers` (temporal separation of cyclic flow).**
3. **Velocity Attack evasion via `split_transaction` (fragment rapid-fire stream).**
4. **Mule Network evasion via `add_noise_accounts` (noise intermediary insertion).**
5. **Structuring evasion via `randomize_timing` (randomize inter-transaction timestamps).**
6. **Fan-in/Fan-out evasion via `insert_low_risk_padding` (dilute signal with benign events).**
7. **Dormant Activation evasion via `mimic_legitimate` (normalize burst amounts to benign range).**
8. **Complex Layering Chain evasion via compounded `split_transaction` + `alter_topology`.**
9. **Mule Hub evasion via multi-generational `add_noise_accounts` (gen-1 mutation chain).**
10. **Round Trip obfuscation via `insert_low_risk_padding` (dilute cyclic signal).**

Each scenario asserts:
- The Escape Analyzer confirms the topology evaded detection
- The exported file exists in `evidence/evasion_exports/`
- The file passes canonical schema validation (fields, types, ISO timestamp, connectivity rules)

---

## 5. Canonical Export Schema & Validation

All evasion exports are written by `redteam/canonical_exporter.py` and enforced at save time. The canonical format is a flat JSON array:

```json
[
  {
    "from_account": "acc_<hex>",
    "to_account": "acc_<hex>",
    "amount": 49500,
    "payment_rail": "NEFT",
    "timestamp": "2026-05-19T10:15:00"
  }
]
```

**Hard rejection rules (schema validation will raise ValueError):**

| Rule | Threshold |
|---|---|
| Minimum transaction edges | 2 |
| Minimum unique account entities | 3 |
| Intermediary hop existence | sender ∩ receiver must be non-empty |
| Timestamp format | Strict `YYYY-MM-DDTHH:MM:SS` only |
| Amount type | Non-negative integer |
| Extra / missing keys | Rejected — exactly 5 keys required |
| Nested structures in account IDs | Rejected (`{`, `}`, `[`, `]`, `:` forbidden) |

Exports are written to:
```
evidence/evasion_exports/evasion_<topology_type>_gen<N>_run_<sim_id>.json
```

**Current evasion export inventory (2026-05-19):**

| Topology Family | Export Count |
|---|---|
| `layering_chain` | 6 |
| `round_trip` | 12 |
| `mule_network` | 8 |
| `structuring` | 6 |
| `dormant_activation` | 5 |
| `velocity_attack` | 3 |
| `fan_in_fan_out` | 10 |
| **Total evasion exports** | **51** |
| Integrity check exports (`integrity_*.json`) | 6 |
| **Grand total files** | **57** |

---

## 6. Evidence Capture Mode

Running the Orchestrator loop (or the validation test suite) automatically populates the `evidence/` directory:

```text
evidence/
├── evasion_exports/      Canonical JSON exports of evading topologies
│                         57 files across all 7 topology families (2026-05-19)
├── runs/                 Immutable Orchestrator run registry
│                         65+ directories, each containing:
│                         ├── fingerprints/struct.json  (graph metrics)
│                         ├── lineage/ancestry.json     (mutation lineage)
│                         └── summary.json              (detection rate, novelty)
├── graph_snapshots/      PNG renders of generated topologies (from test_06)
│                         integrity_<topology>.png for all 7 families
├── topology_diffs/       Before/after mutation comparison images
├── replay_runs/          Hash verification logs from test_07
│                         replay_hash.txt — deterministic SHA-256 hashes
├── kafka_logs/           Captured Kafka stream message logs (from test_02)
└── demo_runs/            Live capture artifacts for hackathons/demos
```

---

## 7. Before vs After Mutation Visualization

The framework generates side-by-side visual comparisons using NetworkX and Matplotlib (from `test_06`):
- **Original Topology:** The baseline generated graph rendered as PNG.
- **Mutated Topology:** The graph after deterministic perturbation rendered as PNG.
- **Highlighting:** The renderer automatically highlights structural differences — inserted nodes shown in green, mutated edges in orange.

PNG files are saved to `evidence/graph_snapshots/` and `evidence/topology_diffs/`.

---

## 8. Structural Fingerprinting

Every run through the Orchestrator produces a structural fingerprint written to `evidence/runs/<run_id>/fingerprints/struct.json`. Example (from `run_ffcbbcf5ff`, `hierarchical_layering_chain`):

```json
{
  "num_nodes": 11,
  "num_edges": 10,
  "density": 0.0909,
  "in_degree_hist": [6, 4, 0, 1, 0],
  "out_degree_hist": [4, 6, 1, 0, 0],
  "hub_count": 1,
  "triad_census": { "003": 120, "021D": 6, "021U": 15, "021C": 24, ... },
  "cycle_signature": { "total_cycles": 0, "avg_length": 0.0, "max_length": 0 },
  "num_components": 1,
  "max_component_size": 11,
  "spectral_variance": 0.0
}
```

These fingerprints are used by the Topology Diversity service to compute novelty scores (how structurally different this run is from all prior runs in the same topology family) and to detect structural stagnation during long mutation chains.

---

## 9. Hackathon Demo Mode

For live demonstrations, configure the sandbox for maximum observability:

1. **Start backend:** `docker compose up -d`
2. **Start frontend:** `cd dashboard && npm run dev`
3. **Open dashboard:** `http://localhost:3000` — watch the 3D graph evolve in real time.
4. **Open Kafka UI:** `http://localhost:8080` — watch `transactions.sandbox` messages arriving.
5. **Watch Orchestrator:** `docker logs -f bling_robustness_orchestrator` — see each cycle logged with detection rates and novelty scores.
6. **Export evasion patterns:**
   ```bash
   .\export_blue_team.bat     # Windows
   ./export_blue_team.sh      # Mac/Linux
   ```
7. **Show evidence:** Open `evidence/evasion_exports/` and `evidence/runs/` to demonstrate the immutable audit trail of all adversarial cycles.

---

## 10. Success Criteria

A successful validation run is defined by ALL of the following:

1. **All 7 Python test scripts pass** (`EXIT 0`).
2. **Graph topology PNG outputs** exist in `evidence/graph_snapshots/` for all 7 topology families.
3. **Evasive topology exports** exist in `evidence/evasion_exports/` and each file passes canonical schema validation.
4. **Deterministic hashes match** across two runs with the same seed (logged in `evidence/replay_runs/replay_hash.txt`).
5. **Immutable run records** exist in `evidence/runs/` with `fingerprints/struct.json`, `lineage/ancestry.json`, and `summary.json` for each Orchestrator cycle.
6. **Detection rate of 0.0** on all exported gen-0 evasion patterns (as confirmed by `summary.json` in each run record).

These artifacts constitute absolute proof that the research-grade adversarial sandbox is fully operational and producing valid, structurally diverse, evasion-capable synthetic topology patterns.

---

## 11. Running the Suite

### Full suite:
```bash
cd tests
pip install -r requirements.txt
python run_all_validations.py
```

### Individual tests:
```bash
python test_01_health_checks.py
python test_02_kafka_streams.py
python test_03_topology_generation.py
python test_04_mutation_validation.py
python test_05_e2e_evasion_export.py
python test_06_graph_topology_integrity.py
python test_07_deterministic_replay.py
```

> [!IMPORTANT]
> Tests 01–05 require the Docker backend to be running (`docker compose up -d`). Tests 06 and 07 run locally using Python only (NetworkX, hashlib) and do not require Docker.
