# BLING Adversarial Sandbox — Deployment Guide

This guide provides exact steps for setting up, running, and troubleshooting the BLING Adversarial Sandbox on both Windows and macOS/Linux.

> **Current Status:** Phase 1 fully operational as of 2026-05-19. All 7 microservices containerised, Orchestrator loop validated, 65+ evidence run records committed.

---

## A. System Requirements

- **Minimum RAM:** 16 GB (JVM for Kafka/Zookeeper + Python microservice footprint).
- **Recommended RAM:** 32 GB (for running full 3D graph visualizations alongside backend load).
- **GPU:** Dedicated GPU (e.g., NVIDIA RTX series) recommended for smooth 3D graph rendering in the browser. Backend runs entirely on CPU.
- **Storage:** Minimum 10 GB free space for Docker images, volumes, and evidence exports. The `evidence/runs/` registry grows continuously at ~3 KB per cycle.
- **Supported OS:** Windows 10/11 (with WSL2 backend), macOS (Intel or Apple Silicon), Linux (Ubuntu 20.04+).
- **Docker Desktop:** Version 4.20 or higher. On Windows, WSL2 backend must be enabled in Docker Desktop settings.

---

## B. Required Software

| Tool | Version | Notes |
|---|---|---|
| **Git** | Any | [git-scm.com](https://git-scm.com/) |
| **Docker Desktop** | 4.20+ | WSL2 backend required on Windows |
| **Node.js** | 18.x or 20.x (LTS) | For the React dashboard |
| **Python** | 3.11+ | Optional — for local script execution only |
| **VS Code** | Any | Optional — recommended IDE |

---

## C. Full Project Setup

### 1. Clone the Repository

**Windows (PowerShell) / Mac / Linux (Terminal):**
```bash
git clone <repository_url> bling-redteam
cd bling-redteam
```

### 2. Configure Environment

The project ships with a pre-populated `.env` file for sandbox use. If it is missing, copy from the example:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```
**Mac / Linux (Terminal):**
```bash
cp .env.example .env
```

*Note: The default `.env` settings are sufficient for all local sandbox runs. No external credentials required.*

### 3. Build & Run Backend Containers

**Windows / Mac / Linux:**
```bash
docker compose up -d --build
```

*Wait approximately 60–90 seconds for Kafka and all microservices to report healthy.*

To verify all services are up:
```bash
docker compose ps
```

Expected healthy services:
- `bling_zookeeper`
- `bling_kafka`
- `bling_kafka_init` (exits after topic provisioning — this is expected)
- `bling_kafka_ui` (`:8080`)
- `bling_postgres`
- `bling_redis`
- `bling_topology_generator` (`:8001`)
- `bling_graph_engine` (`:8002`)
- `bling_evaluation_harness` (`:8003`)
- `bling_topology_mutator` (`:8004`)
- `bling_escape_analyzer` (`:8005`)
- `bling_robustness_orchestrator`
- `bling_topology_diversity` (`:8082`)
- `bling_sandbox_control_api` (`:8081`)

### 4. Install & Run Frontend

**Windows / Mac / Linux:**
```bash
cd dashboard
npm install
npm run dev
```

### 5. Access the Sandbox

Open your browser and navigate to: `http://localhost:3000`

The dashboard will auto-connect to the Control API WebSocket on `:8081`.

---

## D. Quickstart Mode (One-Command Startup)

If Docker and Node.js are already installed, use the provided startup scripts from the root directory.

**Windows (PowerShell/CMD):**
```cmd
.\start_full_system.bat
```

**Mac / Linux (Terminal):**
```bash
./start_full_system.sh
```

These scripts spin up the Docker backend (`docker compose up -d`) and then launch the Vite dev server (`cd dashboard && npm run dev`) sequentially, with a 60-second wait between them for Kafka to initialize.

---

## E. Backend-Only / Headless Mode

If you only want to run the simulation without the 3D visualization dashboard:

### 1. Start the backend:
```bash
docker compose up -d
```

### 2. Trigger an Attack (via Control API):
```bash
curl -X POST http://localhost:8081/api/sandbox/start \
  -H "Content-Type: application/json" \
  -d '{"attack_type": "mule_network", "attack_depth": 5, "tps": 3.0}'
```

### 3. Watch Orchestrator logs:
```bash
docker logs -f bling_robustness_orchestrator
```

### 4. Verify Kafka Stream (Kafka UI):
Open `http://localhost:8080` to inspect the `transactions.sandbox`, `graph.updates.sandbox`, `fraud.alerts.sandbox`, and `redteam.metrics` topics live.

### 5. Query Evasion Stats:
```bash
curl "http://localhost:8003/evaluations?evaded_only=true"
curl http://localhost:8003/stats
curl "http://localhost:8005/export/evasions?limit=20"
```

### 6. Export Blue Team Patterns:
```bash
# Windows
.\export_blue_team.bat

# Mac/Linux
./export_blue_team.sh
```

Exports all currently evading patterns as validated canonical JSON to `evidence/evasion_exports/`.

### 7. Stop Sandbox:
```bash
curl -X POST http://localhost:8081/api/sandbox/stop
```

---

## F. Blue Team Export Workflow

The `scripts/export_to_blue_team.py` script fetches evasion patterns from the live Escape Analyzer API and validates them through the Canonical Exporter before saving.

```bash
# Run directly (requires backend running):
python scripts/export_to_blue_team.py
```

Exported files are written to:
```
evidence/evasion_exports/evasion_<topology_type>_gen<generation>_run_<sim_id>.json
```

Each file is a flat JSON array of canonical transactions with these exact fields:
- `from_account` (string)
- `to_account` (string)
- `amount` (non-negative integer)
- `payment_rail` (string)
- `timestamp` (ISO format: `YYYY-MM-DDTHH:MM:SS`)

**Schema rejection rules** (hard-enforced at export time):
- Fewer than 2 transaction edges → rejected
- Fewer than 3 unique account entities → rejected
- No intermediary hop (empty sender ∩ receiver) → rejected
- Invalid ISO timestamp → rejected
- Negative amounts or nested structures → rejected

---

## G. Frontend Recovery

If the dashboard displays a blank screen, shows "WebSocket Disconnected", or fails to load:

1. **Kill the running Vite server** (`Ctrl+C` in the terminal).
2. **Clear the Vite cache:**
   - **Windows:** `Remove-Item -Recurse -Force .\node_modules\.vite`
   - **Mac/Linux:** `rm -rf node_modules/.vite`
3. **Reinstall and start:**
   ```bash
   npm install
   npm run dev
   ```
4. **Hard Refresh Browser:** `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac).
5. **Verify Control API is healthy:**
   ```bash
   curl http://localhost:8081/health
   ```
   If unhealthy: `docker compose restart sandbox-control-api`

---

## H. Common Failure Recovery

| Symptom | Cause | Fix |
|---|---|---|
| **Port already in use** | Local Postgres (5432) or Redis (6379) running | Stop local service or change port in `docker-compose.yml` |
| **Kafka crash loop** | Insufficient Docker memory | Set Docker RAM to ≥ 8 GB; run `docker compose restart kafka zookeeper` |
| **WebSocket disconnect** | Control API unhealthy | `docker compose restart sandbox-control-api` |
| **3D graph freezes** | Too many nodes in browser | Click "Reset Graph" on Control Panel, or `curl -X POST http://localhost:8081/api/sandbox/clear` |
| **Orchestrator exits immediately** | Topology Diversity service unreachable | `docker compose restart topology-diversity robustness-orchestrator` |
| **Export script: connection refused** | Backend not running | `docker compose up -d` and wait 60 sec |
| **Corrupted containers / blank state** | Volume corruption | `docker compose down -v && docker compose up -d --build` |

---

## I. Project Restart After PC Shutdown

Docker containers stop when the PC is powered off. Follow these exact steps to resume:

1. Start **Docker Desktop** and wait for the engine to initialize (Docker whale icon in taskbar stops animating).
2. Open a terminal and navigate to the project directory:
   ```bash
   cd D:\bling-redteam      # Windows
   cd ~/bling-redteam        # Mac/Linux
   ```
3. Start the backend:
   ```bash
   docker compose up -d
   ```
4. Wait **60 seconds** for Kafka to spin up (check with `docker compose ps` until all services show `Up`).
5. In a second terminal, start the frontend:
   ```bash
   cd dashboard
   npm run dev
   ```
6. Open `http://localhost:3000`.

---

## J. Sandbox Control Commands

All interactions route through the Control API (`localhost:8081`):

| Operation | Command |
|---|---|
| **Start Sandbox** | `POST /api/sandbox/start` — `{"attack_type": "...", "attack_depth": int, "tps": float}` |
| **Stop Sandbox** | `POST /api/sandbox/stop` |
| **Clear State** | `POST /api/sandbox/clear` |
| **Export Evidence Bundle** | `POST /api/sandbox/bundle` |
| **View All Backend Logs** | `docker compose logs -f` |
| **View Orchestrator Logs** | `docker compose logs -f robustness-orchestrator` |
| **View Diversity Logs** | `docker compose logs -f topology-diversity` |
| **Rebuild System** | `docker compose up -d --build` |
| **Full Teardown** | `docker compose down -v` |

---

## K. Running the Validation Suite

The 7-script test suite verifies the entire system from service health through to deterministic replay. Requires backend running.

```bash
cd tests
pip install -r requirements.txt
python run_all_validations.py
```

Or run individual tests:
```bash
python test_01_health_checks.py
python test_06_graph_topology_integrity.py
python test_07_deterministic_replay.py
```

Expected outcome: all 7 scripts exit with code `0`. Evidence artifacts are written to `evidence/` subdirectories during the run.

---

## L. Auto-Start Configuration

The `docker-compose.yml` is configured with `restart: unless-stopped` for all stateless microservices, so they auto-resume after Docker Desktop restarts.

Data persistence is handled via Docker named volumes:
- `postgres_data` — Postgres relational state
- `redis_data` — Redis cache state
- `kafka_data` — Kafka topic log persistence

> **Note:** The `kafka-init` container intentionally runs once and exits (`restart: "no"`) to provision topics. This is expected behavior and not an error.

---

## M. Evidence Directory Reference

```
evidence/
├── evasion_exports/   57 canonical JSON exports (all 7 topology families, as of 2026-05-19)
│                      Naming: evasion_<topology>_gen<N>_run_<sim_id>.json
│                      Also: integrity_<topology>.json (from test_06 integrity checks)
├── runs/              65+ immutable Orchestrator run records
│                      Each: fingerprints/struct.json + lineage/ancestry.json + summary.json
├── graph_snapshots/   PNG renders from test_06_graph_topology_integrity.py
├── topology_diffs/    Before/after mutation comparison images
├── replay_runs/       Deterministic replay hash logs from test_07
├── kafka_logs/        Captured Kafka stream messages from test_02
└── demo_runs/         Live capture artifacts for hackathon/demo use
```
