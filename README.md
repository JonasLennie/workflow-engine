# Manufacturing Workflow Engine

A minimal, database-driven workflow engine that analyzes manufacturing data for quality issues. Submit sensor readings and part measurements, get back a PASS/WARNING/FAIL verdict.

## What it does

A user submits manufacturing data (sensor readings, dimensional measurements) via API or web UI. The system runs a four-stage analysis pipeline:

1. **Detect Outliers** - flags values outside 2 standard deviations
2. **Analyze Trends** - computes linear slope per sensor to detect drift
3. **Synthesize** - merges outlier and trend results
4. **Verdict** - returns PASS / WARNING / FAIL based on combined findings

Tasks 1 and 2 run in parallel. Task 3 waits for both. Task 4 waits for 3.

## Architecture

Five services, all orchestrated via Docker Compose:

| Service | Role |
|---|---|
| **Postgres** | Single source of truth. Workflows and tasks live in the DB. |
| **API** (FastAPI) | `POST /workflow`, `GET /status/{id}`, `GET /results/{id}` |
| **Orchestrator** | Polls for new workflows, reads a JSON workflow spec, creates task rows |
| **Worker** | Polls for ready tasks, executes them, writes results back |
| **Frontend** (React/Vite) | Submit data, track progress, view results |

```
                         ┌─────────────┐
  User ──POST /workflow──▶    API       │
                         └──────┬──────┘
                                │ INSERT workflow
                                ▼
                         ┌─────────────┐
                         │  Postgres   │◀── single source of truth
                         └──┬──────┬───┘
                            │      │
                   reads    │      │  reads
                   workflows│      │  tasks
                            ▼      ▼
                    ┌──────────┐ ┌────────┐
                    │Orchestr. │ │ Worker │
                    └──────────┘ └────────┘
                    writes:       writes:
                    workflows     tasks only
                    + tasks
```

## Key Design Decisions

**Postgres as the queue.** No Redis, no RabbitMQ. Tasks are claimed with `SELECT ... FOR UPDATE SKIP LOCKED`, which gives us atomic acquisition without a separate broker. Good enough for this scale and removes an infrastructure dependency.

**Declarative workflow specs.** The task DAG is defined in a JSON file (`workflows/manufacturing_analysis.json`), not in code. The orchestrator reads the spec and creates task rows. Adding a new workflow type means adding a new JSON file.

**Separation of concerns.** The worker only writes to the `tasks` table. The orchestrator writes to both `workflows` and `tasks`. The API only reads (except the initial insert). This makes it straightforward to reason about who mutates what.

**Dependency resolution via `depends_on`.** Each task row stores a `depends_on TEXT[]` of task type names. The worker's acquisition query skips tasks whose dependencies aren't yet completed. No separate scheduling step needed.

**Retry with exponential backoff.** Failed tasks are retried up to `max_attempts` (default 3) with `2^attempts` second backoff, capped at 60s. Lease expiry prevents stuck tasks from blocking the pipeline.

## Running

```bash
docker compose up -d
```

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **Adminer (DB UI):** http://localhost:8080 (server: `db`, user: `postgres`, password: `postgres`, database: `workflow`)

## API

```bash
# Submit a workflow
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_readings": [{"sensor_id": "temp_1", "values": [72.1, 73.4, 71.8, 99.2]}],
    "measurements": [{"part_id": "A100", "dimension": "width", "values": [10.01, 10.02, 9.98]}]
  }'
# {"workflow_id": 1}

# Check status
curl http://localhost:8000/status/1

# Get results (once completed)
curl http://localhost:8000/results/1
```
