# BLING: Adversarial Sandbox Testing & Validation Framework

This document outlines the complete testing, validation, and observability framework for the **BLING Adversarial Financial Graph Topology Generation Engine**. 

> [!IMPORTANT]
> **Research-Grade Positioning**
> This validation framework proves that the system successfully generates, mutates, and evaluates synthetic adversarial graph topologies. It does NOT validate production AML fraud detection or autonomous self-learning AI. 

---

## 1. System Validation Plan

The validation suite is designed to sequentially verify the core robustness loop:

1. **Service Health (`test_01`):** Verifies all microservices respond on their `/health` endpoints.
2. **Kafka Streams (`test_02`):** Validates that `transactions.sandbox`, `graph.updates.sandbox`, `fraud.alerts.sandbox`, and `redteam.metrics` topics are available and receiving messages.
3. **Topology Generation (`test_03`):** Submits requests to the Topology Generator and verifies the structural output of generated topologies (e.g., correct number of transactions for a given depth).
4. **Mutation Application (`test_04`):** Submits a baseline topology to the Topology Mutator and asserts that structural changes (node insertion, timing jitter) occur.
5. **End-to-End Evasion Export (`test_05`):** Runs a full simulation, awaits processing by the Evaluation Harness, and queries the Escape Analyzer to assert that evasive structures are exported.
6. **Graph Topology Integrity (`test_06`):** Asserts the mathematical properties of generated graphs using NetworkX.
7. **Deterministic Replay (`test_07`):** Ensures reproducibility by asserting identical random seeds produce identical topological structures and hashes.

---

## 2. Test Data Generation

The system tests across 7 distinct topological patterns. Example expectations:

* **Layering Chains:** Linear `A → B → C → D` paths. Tested for path depth `≥ depth`.
* **Round Trips:** Cyclic flows `A → B → C → A`. Tested for cycle existence.
* **Mule Networks:** Star topologies. Tested for high out-degree central hubs.
* **Structuring:** Multiple sub-threshold transactions. Tested for amount fragmentation.
* **Dormant Activation:** Temporal gap followed by burst. Tested for timestamp distributions.
* **Velocity Attacks:** High transaction count in short window. Tested for density.
* **Fan-in / Fan-out:** `N → 1` followed by `1 → N`. Tested for concurrent high in-degree and out-degree nodes.

---

## 3. Observability & Graph Metrics

Beyond simple success rates, the framework monitors advanced graph-centric metrics:

### Standard Metrics
* **Topology Generation Count:** Volume of synthetic structures generated.
* **Evasion Rate:** Percentage of mutated topologies that successfully bypass static heuristics.
* **Mutation Diversity Index:** The variety of perturbation strategies actively applied.

### Graph Diversity Metrics
* **Topology Edit Distance:** Quantifies structural changes (nodes/edges added or removed) between mutation generations.
* **Graph Novelty Score:** Measures structural uniqueness against previously seen topologies.
* **Cycle Complexity Score:** Number of independent cycles discovered in round-trip mutations.
* **Node Centrality Shifts:** Changes in graph density around critical hub nodes.
* **Mutation Lineage Depth:** The generational depth required to achieve heuristic evasion.

---

## 4. Sandbox Test Scenarios

The `tests/test_05_e2e_evasion_export.py` script drives 10 end-to-end test scenarios:
1. **Simple Layering Chain evasion via `alter_topology` (intermediary hop insertion).**
2. **Round Trip evasion via `delay_transfers` (temporal separation).**
3. **Velocity Attack evasion via `split_transaction`.**
4. **Mule Network evasion via `add_noise_accounts`.**
5. **Structuring evasion via `randomize_timing`.**
6. **Fan-in/Fan-out evasion via `insert_low_risk_padding`.**
7. **Dormant Activation evasion via `mimic_legitimate`.**
8. **Complex Layering chain evasion via compounded `split_transaction` + `alter_topology`.**
9. **Mule Hub evasion via multi-generational `add_noise_accounts`.**
10. **Round Trip obfuscation via `insert_low_risk_padding`.**

---

## 5. Graph Output Exports

To definitively prove adversarial evolution, the validation suite extracts actual graph artifacts to the `evidence/` directory:

* **JSON Graph Export:** Structured node/edge lists for programmatic ingestion.
* **NetworkX Serialization:** Pickled or GraphML formats for Python ecosystem reuse.
* **PNG/SVG Graph Snapshots:** Rendered images of the topologies.
* **Topology Diffs:** Visual highlights showing inserted nodes (green) and mutated edges (orange).

---

## 6. Before vs After Mutation Visualization

The framework generates side-by-side visual comparisons using NetworkX and Matplotlib:
* **Original Topology:** The baseline generated graph.
* **Mutated Topology:** The graph after deterministic perturbation.
* **Highlighting:** The renderer automatically highlights structural differences, proving that the mutator is actively evolving the graph structure.

---

## 7. Evidence Capture Mode

Running the test suite automatically populates the `evidence/` directory structure:

```text
evidence/
├── graph_snapshots/      # PNGs of generated and mutated topologies
├── topology_diffs/       # Before/After comparison images
├── evasion_exports/      # JSON exports of topologies that evaded heuristics
├── kafka_logs/           # Captured stream messages
├── replay_runs/          # Hashes and metrics proving deterministic replay
└── demo_runs/            # Live capture artifacts for hackathons
```

---

## 8. Hackathon Demo Visualization Mode

For live demonstrations, the sandbox is configured for maximum observability:
1. **Live Stream:** Start a simulation on the Topology Generator.
2. **Real-time Evolution:** Watch terminal logs as the Topology Mutator applies strategies in real-time.
3. **Evasion Dashboard:** Query the Escape Analyzer's `/export/evasions` endpoint.
4. **Visual Evidence:** Open the generated PNGs in `evidence/topology_diffs/` to show judges exactly how the adversarial topology evolved to bypass the evaluation harness.

---

## 9. Success Criteria

A successful validation run is defined by:
1. **All 7 Python test scripts pass** (`EXIT 0`).
2. **Actual Graph Outputs** are written to `evidence/graph_snapshots/` and `evidence/topology_diffs/`.
3. **Evasive Topologies** are successfully verified in `evidence/evasion_exports/`.
4. **Deterministic Hashes** match across runs in the `test_07` replay logs. 

These artifacts constitute absolute proof that the research-grade adversarial sandbox is fully operational.
