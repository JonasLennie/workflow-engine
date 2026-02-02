# Workflow Engine - Implementation Plan

## Status: COMPLETE

## Architecture Overview

A minimal workflow engine for manufacturing data analysis with 5 services:
- **Postgres** - persistence
- **API** (FastAPI) - accepts workflow requests, serves status/results
- **Orchestrator** - polls for pending workflows, creates tasks from JSON spec
- **Worker** - polls for ready tasks, executes them, writes results
- **Frontend** (React/Vite) - submit data, track progress, view results

## 1. Database Schema

Tables: `workflows`, `tasks`, `task_logs`, `task_history`

Key columns added to skeleton:
- `workflows.input_data JSONB` - raw manufacturing data
- `workflows.result JSONB` - final verdict output
- `tasks.depends_on TEXT[]` - task_type names this task depends on
- `tasks.input_data JSONB` - input for this task
- `tasks.output_data JSONB` - result of this task
- `tasks.error TEXT` - error message on failure

Status values:
- Workflows: pending -> running -> completed | failed
- Tasks: pending -> running -> completed | failed

## 2. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/workflow` | POST | Accept manufacturing JSON, create workflow, return `{workflow_id}` |
| `/status/{id}` | GET | Return workflow status + task statuses |
| `/results/{id}` | GET | Return final result (404 if not done) |

## 3. Workflow JSON Spec

File: `workflows/manufacturing_analysis.json`

Defines a DAG of tasks:
- `detect_outliers` (no deps) - flag values outside 2 std devs
- `analyze_trends` (no deps) - linear slope for each sensor
- `synthesize` (depends on outliers + trends) - merge results
- `verdict` (depends on synthesize) - PASS/WARNING/FAIL

## 4. Orchestrator Design

Single loop polling every 2s:
1. Find `pending` workflows (FOR UPDATE SKIP LOCKED)
2. Create all task rows from workflow spec
3. Mark workflow as `running`
4. Check `running` workflows: all tasks done -> `completed`, any failed -> `failed`

Writes to: workflows table, tasks table

## 5. Worker Design

Single loop polling every 1s:
1. Find `pending` tasks where all `depends_on` tasks are `completed` (FOR UPDATE SKIP LOCKED)
2. Set lease, increment attempts, mark `running`
3. Gather upstream outputs for dependent tasks
4. Execute handler function
5. Write `output_data` on success, handle retry/failure

Writes to: tasks table ONLY

Retry: exponential backoff (2^attempts seconds, max 60s). Failed after max_attempts.

## 6. Frontend

React + Vite. Three panels:
- Submit form (JSON textarea -> POST /workflow)
- Status tracker (poll /status/{id}, show task pipeline)
- Results viewer (show verdict badge + details)

## 7. File Structure

```
api.py, orchestrator.py, worker.py, task_handlers.py, db.py
Dockerfile, requirements.txt, init.sql
workflows/manufacturing_analysis.json
frontend/ (Vite React app)
docker-compose.yaml
```

## 8. Implementation Checklist

- [x] Plan
- [x] Database schema (init.sql)
- [x] Shared db module (db.py)
- [x] Workflow spec (workflows/manufacturing_analysis.json)
- [x] Task handlers (task_handlers.py)
- [x] API service (api.py)
- [x] Orchestrator (orchestrator.py)
- [x] Worker (worker.py)
- [x] Frontend
- [x] Docker Compose + Dockerfiles
- [ ] End-to-end test
