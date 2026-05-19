# BLING — Adversarial Financial Graph Topology Generation Engine

> **Sandboxed Research Infrastructure** · **Not a Production System** · All events carry `_simulation: true`

---

## What Is This?

BLING is a **research-grade, sandboxed adversarial graph topology generation engine** designed to stress-test existing AML detection heuristics by systematically generating, mutating, and evaluating synthetic money laundering graph structures.

Its purpose is to discover **previously unseen synthetic graph variations** that evade existing detection logic — producing candidate patterns for Blue Team rule development under human investigator review.

### What the Red Team Does
- Generates synthetic laundering graph topologies (7 structural patterns)
- Applies deterministic perturbation strategies to mutate graph structures
- Streams topology events through a Kafka sandbox
- Evaluates evasion against a fixed benchmark harness
- Computes structural fingerprints, novelty scores, and mutation lineage for every run
- Exports evading topology variations via canonical schema for human-validated review

### What the Red Team Does NOT Do
- ❌ Autonomously improve production AML models
- ❌ Trigger automatic Blue Team rule updates
- ❌ Retrain models from synthetic attack results
- ❌ Deploy any logic to production systems
- ❌ Claim continuous autonomous self-improvement

---

## Current Project Status — Phase 1 Complete (May 19 2026)

The Phase 1 adversarial sandbox is **fully operational**. All core components have been implemented, validated, and the evidence registry has been populated.

### Completed Milestones
- ✅ All 7 topology pattern generators implemented and tested
- ✅ All 7 perturbation strategies implemented and verified
- ✅ Robustness Orchestrator loop running end-to-end (generate → fingerprint → stream → evaluate → mutate → export)
- ✅ Topology Diversity service computing structural fingerprints, novelty scores, and lineage ancestry for every run
- ✅ 7-script validation suite passing (tests 01–07)
- ✅ **65+ immutable run records** written to `evidence/runs/` (fingerprints, lineage, summary per run)
- ✅ **57 evasion exports** written to `evidence/evasion_exports/` across all 7 topology families
- ✅ Canonical Exporter (`redteam/canonical_exporter.py`) enforcing strict schema, topological density controls, and structural connectivity safeguards
- ✅ Blue Team export pipeline (`scripts/export_to_blue_team.py`) wired to Escape Analyzer API
- ✅ Dashboard (React + Vite) wired to Control API via WebSocket
- ✅ Evasion detection rate on gen-0 topologies: **0.0%** (all exported runs evaded static harness)

---

## Adversarial Training Approach

### Phase 1 — Prototype (Complete)
Synthetic perturbation testing against static baseline heuristics:

| Perturbation Type | Description |
|---|---|
| Amount variations | Scale amounts to probe threshold boundaries |
| Timing shifts | Temporal jitter to evade velocity rules |
| Intermediary node insertion | Add hops to obscure flow topology |
| Transaction splitting | Fragment large flows into sub-threshold chunks |
| Topology mutation | Alter graph structure (fan-in/out, cycles, chains) |

### Phase 2 — Production Research Direction *(Future)*
- Trained on confirmed historical fraud patterns
- Generates realistic evasion simulations
- Human investigators validate all discovered patterns before operational usage

### Safeguards
- 🔒 Blue Team **never** learns automatically from synthetic attack results
- 🔒 No automatic rule updates triggered from Red Team outputs
- 🔒 Exported patterns require **human investigator validation**
- 🔒 Canonical Exporter enforces: minimum 2 transaction edges, minimum 3 unique account entities, mandatory intermediary hop (non-empty sender ∩ receiver intersection)
- 🔒 Prevents feedback poisoning from unrealistic synthetic structures

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│             BLING Adversarial Sandbox Pipeline              │
│                                                             │
│  [Robustness Orchestrator] ← (Automates the entire cycle)   │
│           │                                                 │
│           ├─► Topology Generator (7 fraud patterns)         │
│           │                                                 │
│           ├─► Topology Diversity (Structural fingerprint,   │
│           │                       novelty score & lineage)  │
│           │                                                 │
│           ├─► Kafka Stream (Live transaction feed)          │
│           │                                                 │
│           ├─► Graph Engine (Live NetworkX topology)         │
│           │                                                 │
│           ├─► Evaluation Harness (Detection heuristics)     │
│           │                                                 │
│           ├─► Escape Analyzer (Evasion metrics + export)    │
│           │                                                 │
│           ├─► Topology Mutator (Deterministic perturbations)│
│           │                                                 │
│           ├─► Canonical Exporter (Schema validation)        │
│           │                                                 │
│           └─► Control API (Dashboard WebSockets & Registry) │
└─────────────────────────────────────────────────────────────┘
```

---

## The Robustness Orchestrator

The **Robustness Orchestrator** (`redteam/orchestrator/orchestrator.py`) is the "brain" of the BLING framework. It automates the adversarial training loop, so researchers do not need to trigger attacks manually.

**The Orchestrator Loop (Cycle):**
1. **Generate**: Signals the *Topology Generator* to create a synthetic fraud pattern.
2. **Evaluate Novelty**: Passes the graph to the *Topology Diversity* service to compute a structural fingerprint (node/edge count, density, triad census, spectral variance, cycle signature, hub count) and novelty score against previously seen topologies.
3. **Execute**: Streams the graph's transactions through the *Kafka* sandbox.
4. **Detect**: The *Evaluation Harness* (Blue Team heuristic) attempts to detect the fraud.
5. **Analyze**: Queries the *Escape Analyzer* to calculate the evasion rate.
6. **Register Evidence**: Writes structural fingerprint (`fingerprints/struct.json`), ancestry lineage (`lineage/ancestry.json`), and run summary (`summary.json`) to the immutable `evidence/runs/<run_id>/` registry on disk.
7. **Mutate**:
    - If the graph was **detected** (detection rate >= 50%), it commands the *Topology Mutator* to create a more sophisticated variation and loops back to step 1.
    - If the graph **evaded** detection, it stops mutating, logs a successful evasion, exports the canonical pattern via the *Canonical Exporter*, and moves to the next topology family.

---

## Topology Types

| Pattern | Graph Structure | Description |
|---|---|---|
| `layering_chain` | A→B→C→D→... | Sequential fund hops with skimming |
| `round_trip` | A→B→C→A | Cyclic flow — closes back to origin |
| `mule_network` | Hub→[mules]→Sink | Hub disperses to mule accounts |
| `structuring` | 1→N (sub-threshold) | Smurfing — sub-threshold fragmentation |
| `dormant_activation` | Dormant→Burst | Inactive account sudden burst |
| `velocity_attack` | 1→N (rapid) | High-frequency rapid-fire flow |
| `fan_in_fan_out` | N→Hub→M | Aggregate then disperse |

---

## Topology Mutation Strategies (Phase 1)

| Strategy | Perturbation Type |
|---|---|
| `split_transaction` | Transaction splitting — fragment large into small |
| `delay_transfers` | Timing shifts — temporal jitter |
| `add_noise_accounts` | Intermediary node insertion |
| `mimic_legitimate` | Amount/pattern normalization |
| `randomize_timing` | Inter-transaction timing disruption |
| `alter_topology` | Graph structure alteration — extra hops |
| `insert_low_risk_padding` | Signal dilution with benign events |

---

## Canonical Export Schema

All evasion exports are written by `redteam/canonical_exporter.py` as a flat JSON array. Each transaction strictly conforms to:

```json
{
  "from_account": "acc_<hex>",
  "to_account": "acc_<hex>",
  "amount": 12345,
  "payment_rail": "NEFT|RTGS|ach_transfer|wire_transfer|...",
  "timestamp": "YYYY-MM-DDTHH:MM:SS"
}
```

**Schema enforcement rules (hard-rejected at export time):**
- Minimum 2 transaction edges per pattern
- Minimum 3 unique account entities
- Transaction array must be topologically linked (non-empty sender ∩ receiver — i.e., at least one account acts as both sender and receiver, proving an intermediary hop exists)
- Strict ISO timestamp format `YYYY-MM-DDTHH:MM:SS` (no timezone, no fractional seconds)
- Non-negative integer amounts
- No nested structures or extra keys

---

## Blue Team Export Pipeline

Use the following to export all current evasion patterns for Blue Team review:

**Windows:**
```cmd
.\export_blue_team.bat
```

**Mac / Linux:**
```bash
./export_blue_team.sh
```

This invokes `scripts/export_to_blue_team.py`, which:
1. Calls `GET http://localhost:8005/export/evasions?limit=100` on the Escape Analyzer
2. Normalizes and validates each pattern through `canonical_exporter.export_pattern()`
3. Saves each validated pattern to `evidence/evasion_exports/evasion_<topology>_gen<N>_<run_id>.json`

> ⚠️ Requires the backend (`docker compose up -d`) to be running.

---

## Evidence Registry

The Orchestrator writes an immutable record to `evidence/runs/<run_id>/` for every cycle:

```
evidence/runs/<run_id>/
├── fingerprints/
│   └── struct.json      # num_nodes, num_edges, density, degree histograms,
│                        # hub_count, triad_census, cycle_signature,
│                        # num_components, spectral_variance
├── lineage/
│   └── ancestry.json    # topology_family, branch_id, parent_run_id, generation
└── summary.json         # transactions_count, detection_rate, novelty_score,
                         # structural_divergence, topology_family, branch_id
```

**Current registry stats (as of 2026-05-19):**
- Total run records: **65+**
- Detection rate on all exported gen-0 runs: **0.0** (100% evasion)
- Topology families covered: all 7

---

## Quick Start

### Prerequisites
- Docker Desktop running (WSL2 backend on Windows)
- Ports free: `8001–8005`, `8080`, `8081`, `8082`, `9092`, `6379`, `5432`
- 8 GB RAM allocated to Docker (16 GB recommended)

### Launch
```powershell
cd D:\bling-redteam
docker compose up --build
```

> First build: ~5–10 min (downloads base images + installs Python deps)
> Subsequent starts: `docker compose up`

### Watch the Cycle
```bash
# Robustness testing orchestrator
docker logs -f bling_robustness_orchestrator

# Topology generation
docker logs -f bling_topology_generator

# Evaluation harness (evasion/detection outcomes)
docker logs -f bling_evaluation_harness

# Topology diversity (novelty & fingerprinting)
docker logs -f bling_topology_diversity
```

---

## Service Map

| Service | Port | Role |
|---|---|---|
| **Dashboard** | `:3000` | Real-time React + Vite frontend |
| **Control API** | `:8081/docs` | WebSocket hub & Sandbox controls |
| **Generator** | `:8001/docs` | Topology generation API |
| **Graph Engine** | `:8002/docs` | NetworkX graph query API |
| **Eval Harness** | `:8003/docs` | Evaluation results & evasion stats |
| **Mutator** | `:8004/docs` | Perturbation strategy API |
| **Escape Analyzer**| `:8005/docs` | Evasion analysis & pattern export |
| **Diversity** | `:8082/docs` | Structural fingerprinting & lineage |
| **Kafka UI** | `:8080` | Live topic browser |

---

## Kafka Topics

| Topic | Purpose |
|---|---|
| `transactions.sandbox` | Synthetic topology event stream |
| `graph.updates.sandbox` | Graph structure delta events |
| `fraud.alerts.sandbox` | Evasion events (topologies that evaded harness) |
| `redteam.metrics` | Mutation trigger signals |

---

## Key API Calls

### Generate a topology
```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"attack_type": "round_trip", "attack_depth": 5}'
```

### Start streaming a topology
```bash
curl -X POST http://localhost:8001/simulate \
  -H "Content-Type: application/json" \
  -d '{"attack_type": "layering_chain", "tps": 3.0}'
```

### Query graph topology stats
```bash
curl http://localhost:8002/graph/stats
curl http://localhost:8002/graph/cycles
```

### View evaluation results
```bash
curl "http://localhost:8003/evaluations?evaded_only=true"
curl http://localhost:8003/stats
```

### Export evasion topology variations (requires human review)
```bash
curl "http://localhost:8005/export/evasions?topology_type=layering_chain"
curl "http://localhost:8005/export/evasions?limit=100"
```

### Query structural diversity / novelty
```bash
curl http://localhost:8082/diversity/novelty
curl http://localhost:8082/diversity/lineage
```

---

## Stop
```bash
docker compose down -v
```

---

## Module Map

```
redteam/
├── configs/              Shared Kafka config, settings, topology profiles
├── streaming/            Kafka producer + consumer base classes
├── topology_generator/   7 topology pattern generators + FastAPI service
├── topology_diversity/   Structural morphology, similarity scoring, lineage tracking
│                         (fingerprinting.py, similarity.py, lineage.py, exploration.py)
├── graph_engine/         NetworkX live graph + structural query APIs
├── evaluation_harness/   Topology Evaluation Harness (fixed benchmark)
│                         (graph_heuristics.py, rule_heuristics.py, topology_evaluator.py)
├── topology_mutator/     7 perturbation strategies + evolution tracker
├── escape_analyzer/      Escape Analyzer + evasion_tracker.py + Graph Pattern Exporter
├── orchestrator/         Robustness testing cycle orchestrator (orchestrator.py)
├── control_api/          WebSocket dashboard gateway & run registry
│                         (main.py, sandbox_state.py, state_cache.py, evidence_bundle.py)
└── canonical_exporter.py Standardized canonical schema exporter with strict validation

scripts/
└── export_to_blue_team.py  Fetches evasions from API and saves validated canonical JSON

evidence/
├── evasion_exports/      57 canonical JSON exports (all 7 topology families)
├── runs/                 65+ immutable run records (fingerprints + lineage + summary)
├── graph_snapshots/      PNG renders of generated topologies (test_06 integrity checks)
├── topology_diffs/       Before/after mutation comparison images
├── replay_runs/          Deterministic replay hash logs (test_07)
├── kafka_logs/           Captured stream message logs
└── demo_runs/            Hackathon/demo capture artifacts

tests/
├── run_all_validations.py         Runner for all 7 test scripts
├── test_01_health_checks.py       All microservice /health endpoints
├── test_02_kafka_streams.py       All 4 Kafka topics active
├── test_03_topology_generation.py All 7 topology types, structural assertion
├── test_04_mutation_validation.py All 7 mutation strategies, diff assertion
├── test_05_e2e_evasion_export.py  10 end-to-end evasion scenarios
├── test_06_graph_topology_integrity.py  NetworkX graph mathematical property assertions
└── test_07_deterministic_replay.py     Seed-reproducibility hash verification
```

---

## Future Integration Points

| Integration | Location |
|---|---|
| **Neo4j** | Replace `graph_engine/graph_store.py` |
| **PyTorch Geometric GNN** | Replace `TopologyEvaluator` in `evaluation_harness/topology_evaluator.py` |
| **Apache Flink** | Replace `streaming/consumer.py` poll loop |
| **React Dashboard** | All `/health`, `/analysis`, `/export` endpoints are CORS-open |
| **Phase 2 Training Data** | Feed confirmed fraud patterns to `topology_generator/topology_patterns.py` |

---

## Git History

| Commit | Date | Description |
|---|---|---|
| `9ca1995` | 2026-05-19 19:53 KST | Track evidence runs — 65+ run records, 57 evasion exports |
| `03c2011` | 2026-05-19 19:50 KST | Complete validation suite, structural diversity, orchestration fixes, canonical exporter |
| `3f91275` | 2026-05-17 00:31 KST | docs: Add Orchestrator section and update module names in README |
| `25cb1db` | 2026-05-16 23:27 KST | Initial commit: BLING Adversarial Sandbox |

---

## Research Positioning

This engine is positioned as:

> *A sandboxed adversarial graph topology generation and robustness evaluation framework for financial crime detection research.*

It is **not** a production AML replacement. It is **not** a self-healing autonomous system. It is a deterministic research tool whose outputs serve as candidate inputs for human-led detection rule development.
