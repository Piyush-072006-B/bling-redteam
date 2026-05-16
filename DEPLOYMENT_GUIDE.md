# BLING Adversarial Sandbox — Deployment Guide

This guide provides exact steps for setting up, running, and troubleshooting the BLING Adversarial Sandbox on both Windows and macOS/Linux.

## A. System Requirements

- **Minimum RAM:** 16 GB (Due to JVM for Kafka/Zookeeper and Python ML footprint).
- **Recommended RAM:** 32 GB (For running full 3D graph visualizations alongside heavy backend loads).
- **GPU Recommendations:** Dedicated GPU (e.g., NVIDIA RTX series) recommended for smooth 3D graph rendering in the browser. Backend runs entirely on CPU.
- **Storage:** Minimum 10 GB free space for Docker images, volumes, and evidence exports.
- **Supported OS:** Windows 10/11 (with WSL2), macOS (Intel or Apple Silicon), Linux (Ubuntu 20.04+).
- **Docker Desktop:** Version 4.20 or higher, with at least 8GB RAM allocated in Docker settings.

## B. Required Software Installation

1. **Git:** Download and install from [git-scm.com](https://git-scm.com/).
2. **Docker Desktop:** Download from [docker.com](https://www.docker.com/products/docker-desktop/) and ensure it is running. (On Windows, ensure WSL2 backend is enabled).
3. **Node.js:** Download version 18.x or 20.x (LTS) from [nodejs.org](https://nodejs.org/).
4. **Python:** (Optional, for local development) Version 3.11+.
5. **VS Code:** (Optional) Recommended IDE.

## C. Full Project Setup

### 1. Clone the Repository
**Windows (PowerShell) / Mac / Linux (Terminal):**
```bash
git clone <repository_url> bling-redteam
cd bling-redteam
```

### 2. Configure Environment
**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```
**Mac / Linux (Terminal):**
```bash
cp .env.example .env
```
*Note: The default `.env.example` settings are sufficient for local sandbox runs.*

### 3. Build & Run Backend Containers
**Windows / Mac / Linux:**
```bash
docker compose up -d --build
```
*Wait approximately 60 seconds for Kafka and all microservices to report healthy.*

### 4. Install & Run Frontend
**Windows / Mac / Linux:**
```bash
cd dashboard
npm install
npm run dev
```

### 5. Access the Sandbox
Open your browser and navigate to: `http://localhost:3000`

---

## D. Quickstart Mode (5-Minute Startup)

If your system already has Docker and Node.js installed, use the provided startup scripts from the root directory.

**Windows (PowerShell/CMD):**
```cmd
.\start_full_system.bat
```

**Mac / Linux (Terminal):**
```bash
./start_full_system.sh
```

---

## E. Backend-Only Mode (Headless Operation)

If you only want to run the simulation without the 3D visualization dashboard, or if the frontend fails to build, you can operate the sandbox purely via API calls.

1. **Start the backend:**
   ```bash
   docker compose up -d
   ```

2. **Trigger an Attack (via Control API):**
   ```bash
   curl -X POST http://localhost:8081/api/sandbox/start -H "Content-Type: application/json" -d '{"attack_type": "mule_network", "attack_depth": 5, "tps": 3.0}'
   ```

3. **Verify Kafka Stream (using Kafka UI):**
   Open `http://localhost:8080` in your browser to view the `transactions.sandbox` and `redteam.metrics` topics.

4. **Stop Sandbox:**
   ```bash
   curl -X POST http://localhost:8081/api/sandbox/stop
   ```

5. **Export Evidence Bundle:**
   ```bash
   curl -X POST http://localhost:8081/api/sandbox/bundle
   ```
   *The exported graph topologies will be saved to `./evidence`.*

---

## F. Frontend Recovery

If the dashboard displays a blank screen or fails to connect:

1. **Kill the running Vite server** (`Ctrl+C` in the terminal).
2. **Clear the Vite cache:**
   **Windows:** `Remove-Item -Recurse -Force .\node_modules\.vite`
   **Mac/Linux:** `rm -rf node_modules/.vite`
3. **Reinstall and start:**
   ```bash
   npm install
   npm run dev
   ```
4. **Hard Refresh Browser:** `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac).

---

## G. Common Failure Recovery

- **Docker Not Starting (Port Conflicts):** If port `5432` (Postgres) or `6379` (Redis) is already in use by a local installation, stop your local services or modify the exposed ports in `docker-compose.yml`.
- **Kafka Unavailable (Crash Loop):** Ensure Docker Desktop has at least 8GB of RAM allocated. Kafka requires significant memory. Run `docker compose restart kafka zookeeper`.
- **WebSocket Disconnect:** If the dashboard shows "Disconnected", check the Control API health: `curl http://localhost:8081/health`. If it is unhealthy, run `docker compose restart sandbox-control-api`.
- **Graph Rendering Crash (Browser Out of Memory):** If the 3D graph freezes due to too many nodes, click the "Reset Graph" button on the Control Panel, or run `curl -X POST http://localhost:8081/api/sandbox/clear`.
- **Corrupted Containers:** 
  ```bash
  docker compose down -v
  docker compose up -d --build
  ```

---

## H. Project Restart After PC Shutdown

When turning your PC back on, Docker containers will likely be stopped (unless configured otherwise). Follow these exact steps:

1. Start Docker Desktop and wait for the engine to initialize.
2. Open a terminal and navigate to the project directory.
3. Run `docker compose up -d`
4. Wait 30 seconds for Kafka to spin up.
5. In a second terminal, navigate to `/dashboard` and run `npm run dev`.
6. Open `http://localhost:3000`.

---

## I. Sandbox Control Commands

All interactions route through the Control API (`localhost:8081`):

- **Start Sandbox:** `POST /api/sandbox/start` (Payload: `{"attack_type": "...", "attack_depth": int, "tps": float}`)
- **Stop Sandbox:** `POST /api/sandbox/stop`
- **Clear State:** `POST /api/sandbox/clear`
- **Export Evidence:** `POST /api/sandbox/bundle`
- **View Backend Logs:** `docker compose logs -f`
- **View Specific Service Logs:** `docker compose logs -f robustness-orchestrator`
- **Rebuild System:** `docker compose up -d --build`

---

## J. Auto-Start Improvements

The `docker-compose.yml` has been configured with `restart: unless-stopped` for all stateless microservices. Data persistence is handled via Docker volumes (`postgres_data`, `redis_data`, `kafka_data`). 

*Note: The `kafka-init` container intentionally runs once and exits (`restart: "no"`) to provision topics.*
