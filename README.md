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
- Exports evading topology variations for human-validated review

### What the Red Team Does NOT Do
- ❌ Autonomously improve production AML models
- ❌ Trigger automatic Blue Team rule updates
- ❌ Retrain models from synthetic attack results
- ❌ Deploy any logic to production systems
- ❌ Claim continuous autonomous self-improvement

---

## Adversarial Training Approach

### Phase 1 — Prototype (Current)
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
│           ├─► Topology Diversity (Measures structural       │
│           │                       novelty & fingerprint)    │
│           │                                                 │
│           ├─► Kafka Stream (Live transaction feed)          │
│           │                                                 │
│           ├─► Graph Engine (Live NetworkX topology)         │
│           │                                                 │
│           ├─► Evaluation Harness (Detection heuristics)     │
│           │                                                 │
│           ├─► Escape Analyzer (Evasion metrics)             │
│           │                                                 │
│           ├─► Topology Mutator (Deterministic perturbations)│
│           │                                                 │
│           └─► Control API (Dashboard WebSockets & Registry) │
└─────────────────────────────────────────────────────────────┘
```

---

## The Robustness Orchestrator

The **Robustness Orchestrator** is the "brain" of the BLING framework. It automates the adversarial training loop, so researchers do not need to trigger attacks manually. 

**The Orchestrator Loop (Cycle):**
1. **Generate**: Signals the *Topology Generator* to create a synthetic fraud pattern.
2. **Evaluate Novelty**: Passes the graph to the *Topology Diversity* service to compute a structural fingerprint and novelty score.
3. **Execute**: Streams the graph's transactions through the *Kafka* sandbox.
4. **Detect**: The *Evaluation Harness* (Blue Team heuristic) attempts to detect the fraud.
5. **Analyze**: Queries the *Escape Analyzer* to calculate the evasion rate.
6. **Register Evidence**: Logs the structural fingerprint, full payload, and lineage to the immutable `evidence/runs/` registry on disk.
7. **Mutate**: 
    - If the graph was **detected** (detection rate >= 50%), it commands the *Topology Mutator* to create a more sophisticated variation and loops back to step 1.
    - If the graph **evaded** detection, it stops mutating, logs a successful evasion, and moves to the next topology family.

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

## Quick Start

### Prerequisites
- Docker Desktop running
- Ports free: `8001–8005`, `8080`, `9092`, `6379`, `5432`
- 8 GB RAM available for Docker

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
```

---

## Service Map

| Service | Port | Role |
|---|---|---|
| **Dashboard** | `:3000` | Real-time React frontend |
| **Control API** | `:8081/docs` | WebSocket hub & Sandbox controls |
| **Generator** | `:8001/docs` | Topology generation API |
| **Graph Engine** | `:8002/docs` | NetworkX graph query API |
| **Eval Harness** | `:8003/docs` | Evaluation results & evasion stats |
| **Mutator** | `:8004/docs` | Perturbation strategy API |
| **Escape Analyzer**| `:8005/docs` | Evasion analysis & pattern export |
| **Diversity** | `:8082/docs` | Structural fingerprinting & lineage |

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

### Export evasion topology variations
```bash
# Returns previously unseen synthetic graph variations — requires human review
curl "http://localhost:8005/export/evasions?topology_type=layering_chain"
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
├── configs/             Shared Kafka config, settings, topology profiles
├── streaming/           Kafka producer + consumer base classes
├── topology_generator/  7 topology pattern generators + FastAPI service
├── topology_diversity/  Structural morphology, similarity scoring, and lineage tracking
├── graph_engine/        NetworkX live graph + structural query APIs
├── evaluation_harness/  Topology Evaluation Harness (fixed benchmark)
├── topology_mutator/    7 perturbation strategies + evolution tracker
├── escape_analyzer/     Escape Analyzer + Graph Pattern Exporter
├── orchestrator/        Robustness testing cycle orchestrator
└── control_api/         WebSocket dashboard gateway & run registry
```

---

## Future Integration Points

| Integration | Location |
|---|---|
| **Neo4j** | Replace `graph_engine/graph_store.py` |
| **PyTorch Geometric GNN** | Replace `TopologyEvaluator` in `detector/ml_detector.py` |
| **Apache Flink** | Replace `streaming/consumer.py` poll loop |
| **React Dashboard** | All `/health`, `/analysis`, `/export` endpoints are CORS-open |
| **Phase 2 Training Data** | Feed confirmed fraud patterns to `generator/fraud_patterns.py` |

---

## Research Positioning

This engine is positioned as:

> *A sandboxed adversarial graph topology generation and robustness evaluation framework for financial crime detection research.*

It is **not** a production AML replacement. It is **not** a self-healing autonomous system. It is a deterministic research tool whose outputs serve as candidate inputs for human-led detection rule development.
