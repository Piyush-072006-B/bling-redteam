# BLING Red Team Engine — Launch Guide

## ✅ Status: BUILD-COMPLETE & VERIFIED

All 19 Python files passed AST syntax validation.
Docker Compose YAML validated — 12 services defined.

---

## Project Location
```
D:\bling-redteam\
```

---

## Launch Instructions

### Step 1 — Open a terminal in the project folder

```powershell
cd D:\bling-redteam
```

### Step 2 — Build and start all services

```bash
docker compose up --build
```

> First build takes ~5–10 minutes (downloads base images + installs Python deps).
> Subsequent starts are fast: `docker compose up`

### Step 3 — Watch the adversarial loop run

```bash
# Adversarial feedback loop logs
docker logs -f bling_simulation_runner

# Generator logs (fraud being produced)
docker logs -f bling_generator

# Detector alerts (fraud being caught)
docker logs -f bling_detector
```

---

## Service URLs (after startup)

| Service | URL |
|---|---|
| **Kafka UI** (monitor topics) | http://localhost:8080 |
| **Generator API docs** | http://localhost:8001/docs |
| **Graph Engine API docs** | http://localhost:8002/docs |
| **Detector API docs** | http://localhost:8003/docs |
| **Mutator API docs** | http://localhost:8004/docs |
| **Metrics API docs** | http://localhost:8005/docs |

---

## Quick API Test (after services are healthy)

```bash
# Trigger one attack manually
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"attack_type": "layering_chain", "attack_depth": 5}'

# Check graph stats
curl http://localhost:8002/graph/stats

# View fraud alerts
curl http://localhost:8003/alerts

# Check evasion leaderboard
curl http://localhost:8005/metrics/leaderboard/evasions
```

---

## Stop Everything

```bash
docker compose down -v
```

---

## Fixes Applied in this Session
- Added `streaming/__init__.py` (Python package marker)
- Fixed `mutator/main.py`: replaced fragile `__code__.co_varnames` with `inspect.signature`
- Fixed `metrics/main.py`: added Pydantic model for POST body; reordered routes to prevent path shadowing
- Updated `.dockerignore` to exclude pycache from build context

---

## What Was Built

```
D:\bling-redteam\
├── docker-compose.yml        # 12-service orchestration
├── .env                      # All config variables
├── scripts/init_db.sql       # PostgreSQL schema (7 tables)
├── redteam/
│   ├── configs/              # Shared: Kafka, settings, attack_profiles.json
│   ├── streaming/            # Kafka producer + consumer base classes
│   ├── generator/            # 7 fraud patterns, FastAPI, account pool
│   ├── graph_engine/         # NetworkX graph, cycle detection, centrality
│   ├── detector/             # Rules + Graph Heuristics + Isolation Forest
│   ├── mutator/              # 7 mutation strategies, evolution tracker
│   ├── metrics/              # Detection rate tracking, mutation triggers
│   └── simulation_runner/    # Adversarial feedback loop orchestrator
```
